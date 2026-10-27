#!/usr/bin/env python3
"""Collect visit-only work evidence from selected Dia history profiles."""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_USER_DATA_DIR = Path.home() / "Library/Application Support/Dia/User Data"
EPOCH = dt.datetime(1601, 1, 1, tzinfo=dt.timezone.utc)
SNAPSHOT_ATTEMPTS = 3
SENSITIVE = {
    "auth", "authentication", "authorize", "authorization", "oauth", "oauth2",
    "login", "logout", "signin", "signup", "password", "passwords", "token",
    "tokens", "callback", "settings", "credentials", "secret", "secrets",
    "sso", "session", "sessions", "account", "accounts", "security", "reset",
}
RESOURCE_ROUTES = {
    "pull", "pulls", "issues", "wiki", "blob", "tree", "commit", "commits",
    "actions", "discussions", "projects", "releases", "tags", "branches",
    "compare", "milestones", "labels", "docs",
}
LIMITS = [
    "History proves recorded visits only, not active time, completed reviews, or outcomes.",
    "Profile history does not prove human attention or identify who used the profile.",
    "No duration is inferred from visits, visit durations, or gaps.",
    "Private browsing, deleted history, and history outside browser retention are unavailable.",
    "Only selected Dia profiles and date-bounded stored visits are read.",
    "One candidate per canonical page per local day across selected profiles.",
    "Snapshots retry at most three times; a changing or unreadable history is unavailable.",
]


def resolve_timezone(name: str | None) -> dt.tzinfo:
    if name:
        return ZoneInfo(name)
    local_name = os.environ.get("TZ", "").removeprefix(":")
    if local_name:
        try:
            return ZoneInfo(local_name)
        except (ValueError, ZoneInfoNotFoundError):
            pass
    local_path = str(Path("/etc/localtime").resolve())
    if "/zoneinfo/" in local_path:
        try:
            return ZoneInfo(local_path.split("/zoneinfo/", 1)[1])
        except ZoneInfoNotFoundError:
            pass
    return dt.datetime.now().astimezone().tzinfo or dt.timezone.utc


def parse_range_boundary(
    value: str, is_end: bool = False, timezone: dt.tzinfo | None = None
) -> dt.datetime:
    if len(value) == 10:
        day = dt.date.fromisoformat(value)
        if is_end:
            day += dt.timedelta(days=1)
        parsed = dt.datetime.combine(day, dt.time.min, timezone or resolve_timezone(None))
    else:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def chromium_time(value: dt.datetime) -> int:
    delta = value.astimezone(dt.timezone.utc) - EPOCH
    return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds


def canonical_page(
    value: str, owner: str, allow_hosts: set[str]
) -> tuple[str | None, str]:
    """Return a safe page URL or a fixed, non-sensitive skip reason."""
    try:
        if any(ord(char) < 32 or ord(char) == 127 for char in value) or "\\" in value:
            return None, "invalid_url"
        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            return None, "unsupported_scheme"
        if parts.username is not None or parts.password is not None:
            return None, "credentials"
        host = parts.hostname.lower()
        if parts.port not in {None, 443 if parts.scheme == "https" else 80}:
            return None, "unapproved_host"
        if host != "github.com" and host not in allow_hosts:
            return None, "unapproved_host"
        path = parts.path
        for _ in range(3):
            decoded = unquote(path)
            if decoded == path:
                break
            path = decoded
        if (
            "%" in path or "\\" in path or "//" in path
            or any(ord(char) < 32 or ord(char) == 127 for char in path)
        ):
            return None, "invalid_path"
        segments = [part for part in path.split("/") if part]
        if any(part in {".", ".."} for part in segments):
            return None, "invalid_path"
        words = set(re.split(r"[^a-z0-9]+", path.lower()))
        if words & SENSITIVE:
            return None, "sensitive_route"
        if host == "github.com":
            if not segments or segments[0].lower() != owner.lower():
                return None, "outside_owner"
            if len(segments) > 1 and not re.fullmatch(r"[A-Za-z0-9_.-]+", segments[1]):
                return None, "invalid_path"
            if len(segments) > 2 and segments[2].lower() not in RESOURCE_ROUTES:
                return None, "unsupported_github_route"
            segments[0] = owner.lower()
            if len(segments) >= 4 and segments[2].lower() == "pull" and segments[3].isdigit():
                segments = segments[:4]
                segments[1] = segments[1].lower()
                segments[2] = "pull"
                segments[3] = str(int(segments[3]))
            scheme = "https"
        else:
            scheme = parts.scheme
        safe_path = "/" + "/".join(quote(part, safe="-._~:@") for part in segments)
        return urlunsplit((scheme, host, safe_path, "", "")), ""
    except (ValueError, TypeError, UnicodeError):
        return None, "invalid_url"


def select_profiles(root: Path, profiles: list[str] | None) -> list[str]:
    if profiles is None:
        try:
            state = json.loads((root / "Local State").read_text(encoding="utf-8"))
            profiles = [state["profile"]["last_used"]]
        except (OSError, ValueError, KeyError, TypeError):
            raise ValueError("Local State last_used is missing or invalid") from None
    if not profiles or any(
        not isinstance(profile, str) or not profile or profile in {".", ".."}
        or "/" in profile or "\\" in profile
        or any(ord(char) < 32 for char in profile)
        for profile in profiles
    ):
        raise ValueError("selected profile names are invalid")
    return list(dict.fromkeys(profiles))


def file_states(history: Path) -> dict[str, tuple[int, int, int, int]]:
    states = {}
    for suffix in ("", "-wal", "-journal"):
        path = Path(str(history) + suffix)
        try:
            stat = path.stat()
        except FileNotFoundError:
            if not suffix:
                raise
            continue
        states[suffix] = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
    return states


def read_visits(history: Path, start: int, end: int) -> list[tuple[int, int, str]]:
    """Read only a stable private copy. Never open the live database with SQLite."""
    for attempt in range(SNAPSHOT_ATTEMPTS):
        try:
            before = file_states(history)
            with tempfile.TemporaryDirectory(prefix="work-log-browser-history-") as directory:
                copied = Path(directory) / "History"
                for suffix in before:
                    shutil.copyfile(Path(str(history) + suffix), Path(str(copied) + suffix))
                if before != file_states(history):
                    continue
                with closing(sqlite3.connect(copied.resolve().as_uri() + "?mode=ro", uri=True, timeout=0)) as db:
                    if db.execute("PRAGMA quick_check").fetchone() != ("ok",):
                        raise sqlite3.DatabaseError("snapshot integrity check failed")
                    return db.execute(
                        "SELECT visits.id, visits.visit_time, urls.url "
                        "FROM visits JOIN urls ON urls.id = visits.url "
                        "WHERE visits.visit_time >= ? AND visits.visit_time < ? "
                        "ORDER BY visits.visit_time, visits.id",
                        (start, end),
                    ).fetchall()
        except FileNotFoundError:
            if attempt == SNAPSHOT_ATTEMPTS - 1:
                raise RuntimeError("History or a required snapshot file is missing") from None
        except PermissionError:
            raise RuntimeError("History snapshot permission denied") from None
        except (sqlite3.Error, OSError):
            if attempt == SNAPSHOT_ATTEMPTS - 1:
                raise RuntimeError("History snapshot is locked, unreadable, or malformed") from None
    raise RuntimeError("History changed during all snapshot attempts")


def source_id(root: Path, profile: str, visit_id: int, visit_time: int) -> str:
    namespace = hashlib.sha256(os.fsencode(str(root.resolve()))).hexdigest()
    return f"dia:{namespace}:{quote(profile, safe='')}:{visit_id}:{visit_time}"


def collect(
    start: dt.datetime,
    end: dt.datetime,
    owner: str = "github",
    *,
    timezone: dt.tzinfo | None = None,
    user_data_dir: Path = DEFAULT_USER_DATA_DIR,
    profiles: list[str] | None = None,
    allow_hosts: set[str] | None = None,
) -> dict:
    timezone = timezone or resolve_timezone(None)
    root = Path(user_data_dir).expanduser().resolve()
    groups: dict[tuple[str, str], list[tuple[dt.datetime, dict]]] = {}
    errors, statuses = [], {}
    skipped: Counter = Counter()
    try:
        selected = select_profiles(root, profiles)
    except ValueError as error:
        selected = []
        errors.append({"source": "profile_selection", "error": str(error)})
    for profile in selected:
        history = root / profile / "History"
        try:
            if not history.resolve().is_relative_to(root / profile) or not (root / profile).resolve().is_relative_to(root):
                raise RuntimeError("Selected profile history resolves outside its profile")
            rows = read_visits(history, chromium_time(start), chromium_time(end))
            statuses[profile] = {"ok": True, "visit_rows_in_range": len(rows)}
            for visit_id, visit_time, url in rows:
                if not isinstance(visit_id, int) or not isinstance(visit_time, int) or not isinstance(url, str):
                    skipped["invalid_visit"] += 1
                    continue
                page, reason = canonical_page(url, owner, allow_hosts or set())
                if page is None:
                    skipped[reason] += 1
                    continue
                try:
                    at = EPOCH + dt.timedelta(microseconds=visit_time)
                    day = at.astimezone(timezone).date().isoformat()
                except (OverflowError, ValueError):
                    skipped["invalid_visit"] += 1
                    continue
                source = {
                    "type": "browser-visit", "id": source_id(root, profile, visit_id, visit_time),
                    "url": page, "event_at": at.isoformat(),
                }
                groups.setdefault((day, page), []).append((at, source))
        except RuntimeError as error:
            statuses[profile] = {"ok": False, "error": str(error)}
            errors.append({"source": profile, "error": str(error)})

    candidates = []
    for (day, page), visits in sorted(groups.items()):
        unique = {source["id"]: (at, source) for at, source in visits}
        ordered = sorted(unique.values(), key=lambda row: (row[0], row[1]["id"]))
        first, source = ordered[0]
        last = ordered[-1][0]
        first_at, last_at = first.isoformat(), last.isoformat()
        parts = urlsplit(page)
        path = parts.path.strip("/").split("/")
        is_pr = parts.hostname == "github.com" and len(path) == 4 and path[2] == "pull" and path[3].isdigit()
        label = f"{path[0]}/{path[1]}#{path[3]}" if is_pr else page
        candidates.append({
            "event_id": source["id"], "event_at": first_at, "event_type": "browser-visit",
            "title": f"Visited {label}",
            "summary_facts": [
                f"Recorded {len(ordered)} visit(s) on local date {day}.",
                f"First recorded visit: {first_at}. Last recorded visit: {last_at}.",
                "Visit evidence only. No active time, completed review, or meaningful outcome is established.",
            ],
            "focus_hints": [], "source": source,
            "event_sources": [item[1] for item in ordered[1:]],
            "context_sources": [{"type": "github-pr", "id": label, "url": page}] if is_pr else [],
            "role": "visitor", "confidence": "high", "local_date": day,
            "first_visit_at": first_at, "last_visit_at": last_at, "visit_count": len(ordered),
        })
    successes = sum(status["ok"] for status in statuses.values())
    status = "partial" if successes and errors else "ok" if successes else "unavailable"
    return {
        "collector": "browser", "status": status, "candidate_count": len(candidates),
        "candidates": candidates, "errors": errors, "coverage": ["browser-visits"],
        "source_status": statuses, "skipped": dict(sorted(skipped.items())),
        "limits": LIMITS,
        "profile_coverage": {"selected": selected, "successful": successes},
        "timezone": str(timezone),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="Inclusive ISO date or aware timestamp.")
    parser.add_argument("--end", required=True, help="Inclusive ISO date or exclusive aware timestamp.")
    parser.add_argument("--timezone", help="IANA timezone; default: host local timezone.")
    parser.add_argument("--user-data-dir", type=Path, default=DEFAULT_USER_DATA_DIR)
    parser.add_argument("--profile", action="append", help="Selected profile directory. Repeatable.")
    parser.add_argument("--owner", default="github")
    parser.add_argument("--allow-host", action="append", default=[], help="Additional exact work hostname.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        timezone = resolve_timezone(args.timezone)
        start = parse_range_boundary(args.start, timezone=timezone)
        end = parse_range_boundary(args.end, is_end=True, timezone=timezone)
        if start >= end:
            raise ValueError("--start must be before --end")
        if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?", args.owner):
            raise ValueError("--owner must be a GitHub owner name")
        hosts = {host.lower() for host in args.allow_host}
        if any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host) for host in hosts):
            raise ValueError("--allow-host requires exact hostnames without ports or paths")
    except (ValueError, ZoneInfoNotFoundError):
        print("error: invalid range, timezone, owner, or allowed hostname", file=sys.stderr)
        return 2
    result = collect(start, end, args.owner, timezone=timezone, user_data_dir=args.user_data_dir,
                     profiles=args.profile, allow_hosts=hosts)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
