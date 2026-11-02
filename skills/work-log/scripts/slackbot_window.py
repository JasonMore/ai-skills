#!/usr/bin/env python3
"""Resolve the Slackbot request window from the last answered work-log check."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TEAM = "github"
DEFAULT_CHANNEL = "D09C62HD62J"
PROMPT_MARKER = "Work log check:"
DEFAULT_OVERLAP_MINUTES = 15
HISTORY_PAGE_SIZE = 200
MAX_HISTORY_PAGES = 5
MAX_PROMPT_CHECKS = 10
COMMAND_TIMEOUT_SECONDS = 60
UTC = dt.timezone.utc
JsonObject = Dict[str, Any]
RunCommand = Callable[[Sequence[str]], Tuple[int, str, str]]


def default_run_command(command: Sequence[str]) -> Tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return 1, "", str(error)
    return completed.returncode, completed.stdout, completed.stderr


def current_time() -> dt.datetime:
    return dt.datetime.now(UTC)


def local_timezone() -> dt.tzinfo:
    """Return the host's current local timezone."""
    return dt.datetime.now().astimezone().tzinfo or UTC


def slack_get(
    method: str, fields: Dict[str, str], team: str, run_command: RunCommand
) -> JsonObject:
    """Call one read-only Slack Web API method through `gh slack`."""
    command = ["gh", "slack", "api", "get", method, "--team", team]
    for name, value in fields.items():
        command += ["-f", f"{name}={value}"]
    code, stdout, stderr = run_command(command)
    if code != 0:
        detail = " ".join(stderr.split())[:200] or f"exit code {code}"
        raise RuntimeError(f"{method} failed: {detail}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{method} returned invalid JSON") from error
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        reason = payload.get("error") if isinstance(payload, dict) else None
        raise RuntimeError(f"{method} was not ok: {reason or 'unknown error'}")
    return payload


def parse_slack_ts(value: object) -> Optional[dt.datetime]:
    try:
        return dt.datetime.fromtimestamp(float(str(value)), tz=UTC)
    except (ValueError, OverflowError, OSError):
        return None


def floor_minute(value: dt.datetime) -> dt.datetime:
    return value.replace(second=0, microsecond=0)


def is_check_prompt(message: JsonObject, user_id: str, marker: str) -> bool:
    """Match a thread root that the user sent with the work-log marker."""
    ts = message.get("ts")
    return (
        message.get("user") == user_id
        and message.get("thread_ts", ts) == ts
        and str(message.get("text") or "").lstrip().startswith(marker)
    )


def has_completed_reply(root_ts: str, replies: Sequence[Any]) -> bool:
    """Require a completed AI reply that Slack matched to this exact prompt."""
    for reply in replies:
        context = reply.get("ai_context") if isinstance(reply, dict) else None
        if (
            isinstance(context, dict)
            and reply.get("ts") != root_ts
            and context.get("parent_message_ts") == root_ts
            and context.get("result_status") == "complete"
        ):
            return True
    return False


def find_last_check(
    team: str, channel: str, user_id: str, marker: str, run_command: RunCommand
) -> Tuple[Optional[str], JsonObject]:
    """Return the send timestamp of the newest answered check prompt."""
    stats: JsonObject = {
        "pages_read": 0,
        "prompts_found": 0,
        "skipped": {"no-reply": 0, "no-completed-ai-reply": 0},
        "limit_reached": False,
    }
    cursor = None
    for _ in range(MAX_HISTORY_PAGES):
        fields = {"channel": channel, "limit": str(HISTORY_PAGE_SIZE)}
        if cursor:
            fields["cursor"] = cursor
        page = slack_get("conversations.history", fields, team, run_command)
        stats["pages_read"] += 1
        for message in page.get("messages") or []:
            if not (isinstance(message, dict) and is_check_prompt(message, user_id, marker)):
                continue
            root_ts = str(message["ts"])
            if parse_slack_ts(root_ts) is None:
                continue
            if stats["prompts_found"] >= MAX_PROMPT_CHECKS:
                stats["limit_reached"] = True
                return None, stats
            stats["prompts_found"] += 1
            if not message.get("reply_count"):
                stats["skipped"]["no-reply"] += 1
                continue
            thread = slack_get(
                "conversations.replies",
                {"channel": channel, "ts": root_ts, "limit": "100"},
                team,
                run_command,
            )
            if has_completed_reply(root_ts, thread.get("messages") or []):
                return root_ts, stats
            stats["skipped"]["no-completed-ai-reply"] += 1
        cursor = (page.get("response_metadata") or {}).get("next_cursor")
        if not (page.get("has_more") and cursor):
            return None, stats
    stats["limit_reached"] = True
    return None, stats


def authenticated_user_id(team: str, run_command: RunCommand) -> str:
    user_id = slack_get("auth.test", {}, team, run_command).get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise RuntimeError("auth.test returned no user_id")
    return user_id


def parse_start(value: str, timezone: dt.tzinfo) -> dt.datetime:
    """Parse a local date or an aware timestamp as a UTC instant."""
    if len(value) == 10:
        day = dt.date.fromisoformat(value)
        return dt.datetime.combine(day, dt.time.min, tzinfo=timezone).astimezone(UTC)
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(UTC)


def collect(
    now: dt.datetime,
    timezone: dt.tzinfo,
    *,
    team: str = DEFAULT_TEAM,
    channel: str = DEFAULT_CHANNEL,
    marker: str = PROMPT_MARKER,
    overlap_minutes: int = DEFAULT_OVERLAP_MINUTES,
    fallback_start: Optional[dt.datetime] = None,
    run_command: RunCommand = default_run_command,
) -> JsonObject:
    """Build the window. All arithmetic uses UTC so daylight-saving changes stay correct."""
    overlap = dt.timedelta(minutes=overlap_minutes)
    end = floor_minute(now.astimezone(UTC))
    if fallback_start is None:
        today = end.astimezone(timezone).date()
        fallback_start = dt.datetime.combine(today, dt.time.min, tzinfo=timezone).astimezone(UTC)

    errors: List[JsonObject] = []
    history: Optional[JsonObject] = None
    last_ts: Optional[str] = None
    try:
        user_id = authenticated_user_id(team, run_command)
        last_ts, history = find_last_check(team, channel, user_id, marker, run_command)
    except RuntimeError as error:
        errors.append({"source": "slack", "error": str(error)})

    checked = parse_slack_ts(last_ts) if last_ts else None
    if checked is not None:
        start_source, anchor, fallback_reason = "last-check", floor_minute(checked - overlap), None
    else:
        start_source, anchor = "requested-range", fallback_start
        if errors:
            fallback_reason = "history-unavailable"
        elif history and history["limit_reached"]:
            fallback_reason = "scan-limit-reached"
        else:
            fallback_reason = "no-prior-check"
    # A skewed clock or a very recent check must not give an empty or inverted window.
    start = min(anchor, end - overlap)

    def text(value: dt.datetime) -> str:
        return value.astimezone(timezone).strftime("%A %Y-%m-%d %H:%M %Z")

    def iso(value: dt.datetime) -> str:
        return value.astimezone(timezone).isoformat(timespec="seconds")

    return {
        "collector": "slackbot-window",
        "status": "unavailable" if errors else "ok",
        "start_source": start_source,
        "fallback_reason": fallback_reason,
        "start": iso(start),
        "end": iso(end),
        "start_text": text(start),
        "end_text": text(end),
        "timezone": str(timezone),
        "overlap_minutes": overlap_minutes,
        "last_check": {"ts": last_ts, "at": iso(checked)} if checked is not None else None,
        "prompt_marker": marker,
        "history": history,
        "errors": errors,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timezone", help="IANA timezone. Default: host local timezone.")
    parser.add_argument(
        "--fallback-start",
        help="Start when no answered check exists: ISO date or aware timestamp. "
        "Default: start of today.",
    )
    parser.add_argument("--overlap-minutes", type=int, default=DEFAULT_OVERLAP_MINUTES)
    parser.add_argument("--team", default=DEFAULT_TEAM)
    parser.add_argument("--channel", default=DEFAULT_CHANNEL, help="Slackbot DM channel ID.")
    parser.add_argument("--marker", default=PROMPT_MARKER, help="Text that starts each check prompt.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        timezone = ZoneInfo(args.timezone) if args.timezone else local_timezone()
        if not 1 <= args.overlap_minutes <= 1440:
            raise ValueError("--overlap-minutes must be 1 through 1440")
        if not args.marker.strip():
            raise ValueError("--marker must not be empty")
        fallback_start = parse_start(args.fallback_start, timezone) if args.fallback_start else None
    except (ValueError, ZoneInfoNotFoundError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    result = collect(
        current_time(),
        timezone,
        team=args.team,
        channel=args.channel,
        marker=args.marker,
        overlap_minutes=args.overlap_minutes,
        fallback_start=fallback_start,
        run_command=default_run_command,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
