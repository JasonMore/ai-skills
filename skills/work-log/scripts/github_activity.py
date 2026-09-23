#!/usr/bin/env python3
"""Collect read-only GitHub activity candidates with the GitHub CLI.

The collector uses the authenticated user's event feed for timestamped events
and GraphQL search for authored discussions. It writes one JSON document to
stdout. Per-source failures are included in that document and do not hide
partial successful collection.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlsplit, urlunsplit

DEFAULT_OWNER = "github"
DEFAULT_MAX_PAGES = 10
DEFAULT_PER_PAGE = 100
SUBSTANTIVE_COMMENT_MINIMUM = 40
JsonObject = Dict[str, Any]
RunCommand = Callable[[Sequence[str]], Tuple[int, str, str]]


def parse_range_boundary(value: str, is_end: bool = False) -> dt.datetime:
    """Parse a date or ISO timestamp as an aware UTC boundary."""
    if len(value) == 10:
        parsed_date = dt.date.fromisoformat(value)
        boundary = dt.datetime.combine(parsed_date, dt.time.min, tzinfo=dt.timezone.utc)
        return boundary + dt.timedelta(days=1) if is_end else boundary
    normalized = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def parse_github_timestamp(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            dt.timezone.utc
        )
    except ValueError:
        return None


def timestamp_in_range(
    timestamp: Optional[str], start: dt.datetime, end: dt.datetime
) -> bool:
    parsed = parse_github_timestamp(timestamp)
    return parsed is not None and start <= parsed < end


def canonical_url(value: Optional[str]) -> Optional[str]:
    """Remove fragments, query strings, and a non-root trailing slash."""
    if not value:
        return None
    parts = urlsplit(value)
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def nested(value: JsonObject, *keys: str) -> Optional[Any]:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def actor_is_user(event: JsonObject, user: str) -> bool:
    return str(nested(event, "actor", "login") or "").lower() == user.lower()


def text_is_substantive(value: object) -> bool:
    text = " ".join(str(value or "").split())
    return len(text) >= SUBSTANTIVE_COMMENT_MINIMUM and len(text.split()) >= 3


def event_candidate(
    *,
    event: JsonObject,
    source_type: str,
    timestamp: str,
    title: str,
    url: Optional[str],
    roles: Iterable[str],
    facts: Iterable[str],
    event_id_suffix: Optional[str] = None,
) -> JsonObject:
    """Build the stable JSON shape shared by all normalized candidates."""
    native_event_id = str(event.get("id", ""))
    if event_id_suffix:
        native_event_id = f"{native_event_id}:{event_id_suffix}"
    stable_id = f"github-event:{native_event_id}"
    clean_url = canonical_url(url)
    return {
        "id": stable_id,
        "source_native_event_id": native_event_id,
        "source_type": source_type,
        "event_timestamp": timestamp,
        "title": title,
        "url": clean_url,
        "roles": sorted(set(roles)),
        "evidence_facts": list(facts),
        "source": {
            "type": "github-event",
            "id": str(event.get("id", "")),
            "url": clean_url,
        },
    }


def normalize_event(event: JsonObject, user: str, owner: str) -> List[JsonObject]:
    """Convert one GitHub user-event payload into zero or more candidates."""
    timestamp = event.get("created_at")
    if not isinstance(timestamp, str) or not actor_is_user(event, user):
        return []
    event_type = event.get("type")
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return []

    if event_type == "PullRequestEvent":
        pull_request = payload.get("pull_request") or {}
        if str(nested(pull_request, "user", "login") or "").lower() != user.lower():
            return []
        action = str(payload.get("action", ""))
        if action not in {"opened", "reopened", "closed", "synchronize"}:
            return []
        merged = bool(pull_request.get("merged")) and action == "closed"
        label = "Merged" if merged else action.capitalize()
        title = str(pull_request.get("title") or "Pull request")
        number = pull_request.get("number") or nested(event, "repo", "name")
        facts = [
            f"PR {label.lower()} by {user}.",
            f"Repository: {event.get('repo', {}).get('name', owner)}.",
        ]
        return [
            event_candidate(
                event=event,
                source_type="github-pr",
                timestamp=timestamp,
                title=f"{label} PR: {title}",
                url=pull_request.get("html_url"),
                roles=["author"],
                facts=facts,
            )
        ]

    if event_type == "PullRequestReviewEvent":
        review = payload.get("review") or {}
        pull_request = payload.get("pull_request") or {}
        state = str(review.get("state", "")).lower()
        if (
            str(payload.get("action", "")).lower() != "submitted"
            or state != "submitted"
            or str(nested(review, "user", "login") or "").lower() != user.lower()
        ):
            return []
        title = str(pull_request.get("title") or "Pull request")
        return [
            event_candidate(
                event=event,
                source_type="github-review",
                timestamp=timestamp,
                title=f"Submitted review: {title}",
                url=review.get("html_url") or pull_request.get("html_url"),
                roles=["reviewer"],
                facts=[
                    "Review state: submitted.",
                    f"Repository: {event.get('repo', {}).get('name', owner)}.",
                ],
            )
        ]

    if event_type == "IssuesEvent":
        issue = payload.get("issue") or {}
        action = str(payload.get("action", "")).lower()
        issue_author = str(nested(issue, "user", "login") or "").lower()
        assignees = {
            str(item.get("login", "")).lower()
            for item in issue.get("assignees", [])
            if isinstance(item, dict)
        }
        if action == "opened" and issue_author == user.lower():
            role, label = "author", "Opened"
        elif action == "assigned" and user.lower() in assignees:
            role, label = "assignee", "Assigned"
        elif action == "closed" and issue_author == user.lower():
            role, label = "author", "Closed"
        else:
            return []
        return [
            event_candidate(
                event=event,
                source_type="github-issue",
                timestamp=timestamp,
                title=f"{label} issue: {issue.get('title') or 'Issue'}",
                url=issue.get("html_url"),
                roles=[role],
                facts=[
                    f"Issue action: {action}.",
                    f"Repository: {event.get('repo', {}).get('name', owner)}.",
                ],
            )
        ]

    if event_type == "IssueCommentEvent":
        comment = payload.get("comment") or {}
        issue = payload.get("issue") or {}
        if (
            str(nested(comment, "user", "login") or "").lower() != user.lower()
            or not text_is_substantive(comment.get("body"))
        ):
            return []
        return [
            event_candidate(
                event=event,
                source_type="github-issue-comment",
                timestamp=timestamp,
                title=f"Commented on issue: {issue.get('title') or 'Issue'}",
                url=comment.get("html_url") or issue.get("html_url"),
                roles=["commenter"],
                facts=[
                    f"Comment length: {len(' '.join(str(comment.get('body', '')).split()))} characters.",
                    f"Repository: {event.get('repo', {}).get('name', owner)}.",
                ],
            )
        ]

    if event_type == "PushEvent":
        candidates: List[JsonObject] = []
        for commit in payload.get("commits", []):
            if not isinstance(commit, dict) or not commit.get("sha"):
                continue
            commit_author = nested(commit, "author", "username")
            if commit_author and str(commit_author).lower() != user.lower():
                continue
            repository = str(nested(event, "repo", "name") or owner)
            sha = str(commit["sha"])
            candidates.append(
                event_candidate(
                    event=event,
                    source_type="github-commit",
                    timestamp=timestamp,
                    title=f"Committed: {str(commit.get('message') or sha).splitlines()[0]}",
                    url=f"https://github.com/{repository}/commit/{sha}",
                    roles=["author"],
                    facts=[
                        f"Commit SHA: {sha}.",
                        f"Repository: {repository}.",
                        f"Push reference: {payload.get('ref', '')}.",
                    ],
                    event_id_suffix=sha,
                )
            )
        return candidates

    if event_type == "DiscussionCommentEvent":
        comment = payload.get("comment") or {}
        discussion = payload.get("discussion") or {}
        if (
            str(nested(comment, "user", "login") or "").lower() != user.lower()
            or not text_is_substantive(comment.get("body"))
        ):
            return []
        return [
            event_candidate(
                event=event,
                source_type="github-discussion-reply",
                timestamp=timestamp,
                title=f"Replied to discussion: {discussion.get('title') or 'Discussion'}",
                url=comment.get("html_url") or discussion.get("html_url"),
                roles=["author", "replier"],
                facts=["Discussion reply from authenticated user."],
            )
        ]
    return []


def normalize_discussion(node: JsonObject, user: str) -> Optional[JsonObject]:
    """Normalize an authored GraphQL discussion search result."""
    author = nested(node, "author", "login")
    timestamp = node.get("createdAt")
    if str(author or "").lower() != user.lower() or not isinstance(timestamp, str):
        return None
    node_id = str(node.get("id", ""))
    if not node_id:
        return None
    url = canonical_url(node.get("url"))
    return {
        "id": f"github-discussion:{node_id}",
        "source_native_event_id": node_id,
        "source_type": "github-discussion",
        "event_timestamp": timestamp,
        "title": f"Started discussion: {node.get('title') or 'Discussion'}",
        "url": url,
        "roles": ["author"],
        "evidence_facts": [
            "Discussion author matches authenticated user.",
            f"Repository: {nested(node, 'repository', 'nameWithOwner') or 'unknown'}.",
        ],
        "source": {"type": "github-discussion", "id": node_id, "url": url},
    }


def default_run_command(command: Sequence[str]) -> Tuple[int, str, str]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return completed.returncode, completed.stdout, completed.stderr


def gh_json(
    arguments: Sequence[str], run_command: RunCommand = default_run_command
) -> Any:
    command = ["gh", "api", *arguments]
    code, stdout, stderr = run_command(command)
    if code != 0:
        raise RuntimeError(stderr.strip() or f"{' '.join(command)} exited with {code}")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"gh returned invalid JSON: {error}") from error


def collect_user_events(
    user: str,
    start: dt.datetime,
    end: dt.datetime,
    owner: str,
    max_pages: int,
    per_page: int,
    run_command: RunCommand,
) -> Tuple[List[JsonObject], JsonObject]:
    """Fetch date-bounded user events with an explicit page cap."""
    candidates: List[JsonObject] = []
    scanned = 0
    for page in range(1, max_pages + 1):
        payload = gh_json(
            [f"/user/events?per_page={per_page}&page={page}"], run_command
        )
        if not isinstance(payload, list):
            raise RuntimeError("GitHub user events response was not a JSON array")
        if not payload:
            break
        scanned += len(payload)
        timestamps = []
        for event in payload:
            if isinstance(event, dict):
                timestamps.append(parse_github_timestamp(event.get("created_at")))
                if timestamp_in_range(event.get("created_at"), start, end):
                    candidates.extend(normalize_event(event, user, owner))
        oldest = min((value for value in timestamps if value is not None), default=None)
        if oldest is not None and oldest < start:
            break
    return candidates, {
        "ok": True,
        "pages_scanned": page,
        "events_scanned": scanned,
        "result_limit": max_pages * per_page,
    }


DISCUSSION_QUERY = """
query($search_query: String!, $after: String) {
  search(query: $search_query, type: DISCUSSION, first: 100, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Discussion {
        id
        title
        url
        createdAt
        author { login }
        repository { nameWithOwner }
      }
    }
  }
}
"""


def collect_discussions(
    user: str,
    start: dt.datetime,
    end: dt.datetime,
    owner: str,
    max_pages: int,
    run_command: RunCommand,
) -> Tuple[List[JsonObject], JsonObject]:
    """Find authored discussions through the GraphQL search API."""
    query = (
        f"owner:{owner} author:{user} type:discussion "
        f"created:{start.date().isoformat()}..{(end - dt.timedelta(microseconds=1)).date().isoformat()}"
    )
    candidates: List[JsonObject] = []
    cursor: Optional[str] = None
    pages_scanned = 0
    for _ in range(max_pages):
        arguments = [
            "graphql",
            "-f",
            f"query={DISCUSSION_QUERY}",
            "-f",
            f"search_query={query}",
        ]
        if cursor:
            arguments.extend(["-f", f"after={cursor}"])
        payload = gh_json(arguments, run_command)
        search = nested(payload, "data", "search")
        if not isinstance(search, dict):
            raise RuntimeError("GitHub discussion search response had no data.search")
        pages_scanned += 1
        for node in search.get("nodes", []):
            if isinstance(node, dict) and timestamp_in_range(node.get("createdAt"), start, end):
                candidate = normalize_discussion(node, user)
                if candidate:
                    candidates.append(candidate)
        page_info = search.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            raise RuntimeError("GitHub discussion search returned an empty next cursor")
    return candidates, {
        "ok": True,
        "pages_scanned": pages_scanned,
        "result_limit": max_pages * 100,
        "note": "Discussion replies are collected from user events when GitHub exposes them.",
    }


def collect(
    start: dt.datetime,
    end: dt.datetime,
    owner: str,
    max_pages: int = DEFAULT_MAX_PAGES,
    per_page: int = DEFAULT_PER_PAGE,
    run_command: RunCommand = default_run_command,
) -> JsonObject:
    """Collect all supported sources and return a serializable result."""
    statuses: JsonObject = {}
    errors: List[JsonObject] = []
    candidates: List[JsonObject] = []
    try:
        viewer = gh_json(["/user"], run_command)
        user = str(viewer.get("login", ""))
        if not user:
            raise RuntimeError("GitHub /user response did not include login")
        statuses["authenticated_user"] = {"ok": True, "login": user}
    except RuntimeError as error:
        statuses["authenticated_user"] = {"ok": False, "error": str(error)}
        errors.append({"source": "authenticated_user", "error": str(error)})
        user = ""

    if user:
        for source, function in (
            (
                "user_events",
                lambda: collect_user_events(
                    user, start, end, owner, max_pages, per_page, run_command
                ),
            ),
            (
                "discussions",
                lambda: collect_discussions(user, start, end, owner, max_pages, run_command),
            ),
        ):
            try:
                source_candidates, status = function()
                statuses[source] = status
                candidates.extend(source_candidates)
            except RuntimeError as error:
                statuses[source] = {"ok": False, "error": str(error)}
                errors.append({"source": source, "error": str(error)})

    deduplicated = {candidate["id"]: candidate for candidate in candidates}
    ordered = sorted(
        deduplicated.values(), key=lambda candidate: (candidate["event_timestamp"], candidate["id"])
    )
    return {
        "range": {"start": start.isoformat().replace("+00:00", "Z"), "end": end.isoformat().replace("+00:00", "Z")},
        "authenticated_user": user or None,
        "owner": owner,
        "candidates": ordered,
        "collector_status": {"ok": not errors, "sources": statuses},
        "errors": errors,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect read-only GitHub activity candidates as JSON."
    )
    parser.add_argument("--start", required=True, help="Inclusive ISO date or timestamp.")
    parser.add_argument("--end", required=True, help="Exclusive ISO timestamp or inclusive ISO date.")
    parser.add_argument("--owner", default=DEFAULT_OWNER, help="GitHub owner for discussion search.")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--per-page", type=int, default=DEFAULT_PER_PAGE)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        start = parse_range_boundary(args.start)
        end = parse_range_boundary(args.end, is_end=True)
        if start >= end:
            raise ValueError("--start must be before --end")
        if args.max_pages < 1 or args.per_page < 1 or args.per_page > 100:
            raise ValueError("--max-pages must be positive and --per-page must be 1 through 100")
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            collect(start, end, args.owner, args.max_pages, args.per_page),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
