#!/usr/bin/env python3
"""Collect read-only GitHub activity candidates with the GitHub CLI."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote, urlsplit, urlunsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_OWNER = "github"
DEFAULT_MAX_PAGES = 10
DEFAULT_PER_PAGE = 100
SUBSTANTIVE_COMMENT_MINIMUM = 40
JsonObject = Dict[str, Any]
RunCommand = Callable[[Sequence[str]], Tuple[int, str, str]]


def local_timezone() -> dt.tzinfo:
    """Return the host's current local timezone."""
    return dt.datetime.now().astimezone().tzinfo or dt.timezone.utc


def resolve_timezone(name: Optional[str]) -> dt.tzinfo:
    """Resolve an IANA timezone, or use the host local timezone by default."""
    return ZoneInfo(name) if name else local_timezone()


def parse_range_boundary(
    value: str, is_end: bool = False, timezone: Optional[dt.tzinfo] = None
) -> dt.datetime:
    """Parse local dates and aware timestamps as UTC range boundaries."""
    if len(value) == 10:
        parsed_date = dt.date.fromisoformat(value)
        boundary = dt.datetime.combine(
            parsed_date, dt.time.min, tzinfo=timezone or local_timezone()
        )
        if is_end:
            boundary += dt.timedelta(days=1)
        return boundary.astimezone(dt.timezone.utc)
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
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


def timestamp_in_range(timestamp: Optional[str], start: dt.datetime, end: dt.datetime) -> bool:
    parsed = parse_github_timestamp(timestamp)
    return parsed is not None and start <= parsed < end


def canonical_url(value: Optional[str], preserve_fragment: bool = False) -> Optional[str]:
    """Strip queries and parent-item fragments while keeping event fragments."""
    if not value:
        return None
    parts = urlsplit(value)
    path = parts.path.rstrip("/") or "/"
    fragment = parts.fragment if preserve_fragment else ""
    return urlunsplit((parts.scheme, parts.netloc, path, "", fragment))


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


def repository_name(event: JsonObject, fallback: str) -> str:
    return str(nested(event, "repo", "name") or fallback)


def item_context(source_type: str, source_id: str, url: Optional[str]) -> JsonObject:
    return {"type": source_type, "id": source_id, "url": canonical_url(url)}


def candidate(
    *,
    event_id: str,
    event_at: str,
    event_type: str,
    title: str,
    summary_facts: List[str],
    source_type: str,
    source_id: str,
    source_url: Optional[str],
    role: str,
    context_sources: Optional[List[JsonObject]] = None,
) -> JsonObject:
    """Build a candidate that conforms to references/schema.md."""
    return {
        "event_id": event_id,
        "event_at": event_at,
        "event_type": event_type,
        "title": title,
        "summary_facts": summary_facts,
        "focus_hints": [],
        "source": {"type": source_type, "id": source_id, "url": source_url},
        "context_sources": context_sources or [],
        "role": role,
        "confidence": "high",
    }


def normalize_event(event: JsonObject, user: str, owner: str) -> List[JsonObject]:
    """Convert one GitHub user-event payload into schema candidates."""
    event_at = event.get("created_at")
    event_id = str(event.get("id") or "")
    if not event_id or not isinstance(event_at, str) or not actor_is_user(event, user):
        return []
    event_type = event.get("type")
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return []
    repository = repository_name(event, owner)

    if event_type == "PullRequestEvent":
        pull_request = payload.get("pull_request") or {}
        action = str(payload.get("action", "")).lower()
        if (
            str(nested(pull_request, "user", "login") or "").lower() != user.lower()
            or action not in {"opened", "reopened", "closed", "synchronize"}
        ):
            return []
        merged = action == "closed" and bool(pull_request.get("merged"))
        label = "Merged" if merged else action.capitalize()
        number = str(pull_request.get("number") or "")
        pr_id = f"{repository}#{number}" if number else repository
        pr_url = canonical_url(pull_request.get("html_url"))
        return [
            candidate(
                event_id=f"github-event:{event_id}",
                event_at=event_at,
                event_type="pull-request",
                title=f"{label} PR: {pull_request.get('title') or 'Pull request'}",
                summary_facts=[
                    f"PR action: {label.lower()}.",
                    f"Repository: {repository}.",
                ],
                source_type="github-event",
                source_id=event_id,
                source_url=pr_url,
                role="author",
                context_sources=[item_context("github-pr", pr_id, pr_url)],
            )
        ]

    if event_type == "PullRequestReviewEvent":
        review = payload.get("review") or {}
        pull_request = payload.get("pull_request") or {}
        action = str(payload.get("action", "")).lower()
        state = str(review.get("state", "")).lower()
        review_id = str(review.get("node_id") or review.get("id") or "")
        review_body = review.get("body")
        actionable_comment = state == "commented" and text_is_substantive(review_body)
        if (
            action != "submitted"
            or str(nested(review, "user", "login") or "").lower() != user.lower()
            or not review_id
            or (state not in {"approved", "changes_requested"} and not actionable_comment)
        ):
            return []
        number = str(pull_request.get("number") or "")
        pr_id = f"{repository}#{number}" if number else repository
        pr_url = canonical_url(pull_request.get("html_url"))
        review_url = canonical_url(
            review.get("html_url") or pull_request.get("html_url"), preserve_fragment=True
        )
        return [
            candidate(
                event_id=f"github-review:{review_id}",
                event_at=event_at,
                event_type="review",
                title=f"Submitted review: {pull_request.get('title') or 'Pull request'}",
                summary_facts=[
                    f"Review state: {state}.",
                    f"Repository: {repository}.",
                ],
                source_type="github-review",
                source_id=review_id,
                source_url=review_url,
                role="reviewer",
                context_sources=[item_context("github-pr", pr_id, pr_url)],
            )
        ]

    if event_type == "IssuesEvent":
        issue = payload.get("issue") or {}
        action = str(payload.get("action", "")).lower()
        author = str(nested(issue, "user", "login") or "").lower()
        if action == "opened" and author == user.lower():
            role, label = "author", "Opened"
        elif action == "closed":
            role, label = ("author", "Closed") if author == user.lower() else ("closer", "Closed")
        else:
            return []
        number = str(issue.get("number") or "")
        issue_id = f"{repository}#{number}" if number else repository
        issue_url = canonical_url(issue.get("html_url"))
        return [
            candidate(
                event_id=f"github-event:{event_id}",
                event_at=event_at,
                event_type="issue",
                title=f"{label} issue: {issue.get('title') or 'Issue'}",
                summary_facts=[f"Issue action: {action}.", f"Repository: {repository}."],
                source_type="github-event",
                source_id=event_id,
                source_url=issue_url,
                role=role,
                context_sources=[item_context("github-issue", issue_id, issue_url)],
            )
        ]

    if event_type == "IssueCommentEvent":
        comment = payload.get("comment") or {}
        issue = payload.get("issue") or {}
        comment_id = str(comment.get("node_id") or comment.get("id") or "")
        if (
            str(nested(comment, "user", "login") or "").lower() != user.lower()
            or not text_is_substantive(comment.get("body"))
            or not comment_id
        ):
            return []
        number = str(issue.get("number") or "")
        issue_id = f"{repository}#{number}" if number else repository
        issue_url = canonical_url(issue.get("html_url"))
        comment_url = canonical_url(
            comment.get("html_url") or issue.get("html_url"), preserve_fragment=True
        )
        return [
            candidate(
                event_id=f"github-issue-comment:{comment_id}",
                event_at=event_at,
                event_type="comment",
                title=f"Commented on issue: {issue.get('title') or 'Issue'}",
                summary_facts=[
                    f"Comment length: {len(' '.join(str(comment.get('body', '')).split()))} characters.",
                    f"Repository: {repository}.",
                ],
                source_type="github-issue-comment",
                source_id=comment_id,
                source_url=comment_url,
                role="commenter",
                context_sources=[item_context("github-issue", issue_id, issue_url)],
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
            sha = str(commit["sha"])
            candidates.append(
                candidate(
                    event_id=f"github-commit:{repository}@{sha}",
                    event_at=event_at,
                    event_type="commit",
                    title=f"Committed: {str(commit.get('message') or sha).splitlines()[0]}",
                    summary_facts=[
                        f"Commit SHA: {sha}.",
                        f"Repository: {repository}.",
                        f"Push reference: {payload.get('ref', '')}.",
                    ],
                    source_type="github-commit",
                    source_id=sha,
                    source_url=canonical_url(f"https://github.com/{repository}/commit/{sha}"),
                    role="author",
                )
            )
        return candidates

    if event_type == "DiscussionCommentEvent":
        comment = payload.get("comment") or {}
        discussion = payload.get("discussion") or {}
        comment_id = str(comment.get("node_id") or comment.get("id") or "")
        if (
            str(nested(comment, "user", "login") or "").lower() != user.lower()
            or not text_is_substantive(comment.get("body"))
            or not comment_id
        ):
            return []
        discussion_id = str(discussion.get("node_id") or discussion.get("id") or "")
        discussion_url = canonical_url(discussion.get("html_url"))
        comment_url = canonical_url(
            comment.get("html_url") or discussion.get("html_url"), preserve_fragment=True
        )
        context = (
            [item_context("github-discussion", discussion_id, discussion_url)]
            if discussion_id
            else []
        )
        return [
            candidate(
                event_id=f"github-discussion-comment:{comment_id}",
                event_at=event_at,
                event_type="discussion-reply",
                title=f"Replied to discussion: {discussion.get('title') or 'Discussion'}",
                summary_facts=["Discussion reply from authenticated user."],
                source_type="github-discussion-comment",
                source_id=comment_id,
                source_url=comment_url,
                role="replier",
                context_sources=context,
            )
        ]
    return []


def normalize_discussion(node: JsonObject, user: str) -> Optional[JsonObject]:
    """Normalize an authored GraphQL discussion search result."""
    author = nested(node, "author", "login")
    event_at = node.get("createdAt")
    node_id = str(node.get("id") or "")
    if str(author or "").lower() != user.lower() or not isinstance(event_at, str) or not node_id:
        return None
    url = canonical_url(node.get("url"))
    repository = str(nested(node, "repository", "nameWithOwner") or "unknown")
    return candidate(
        event_id=f"github-discussion:{node_id}",
        event_at=event_at,
        event_type="discussion",
        title=f"Started discussion: {node.get('title') or 'Discussion'}",
        summary_facts=[
            "Discussion author matches authenticated user.",
            f"Repository: {repository}.",
        ],
        source_type="github-discussion",
        source_id=node_id,
        source_url=url,
        role="author",
    )


def default_run_command(command: Sequence[str]) -> Tuple[int, str, str]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return completed.returncode, completed.stdout, completed.stderr


def gh_json(arguments: Sequence[str], run_command: RunCommand = default_run_command) -> Any:
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
    pages_scanned = 0
    complete = False
    encoded_user = quote(user, safe="")
    encoded_owner = quote(owner, safe="")
    for page in range(1, max_pages + 1):
        payload = gh_json(
            [
                f"/users/{encoded_user}/events/orgs/{encoded_owner}"
                f"?per_page={per_page}&page={page}"
            ],
            run_command,
        )
        pages_scanned = page
        if not isinstance(payload, list):
            raise RuntimeError("GitHub user events response was not a JSON array")
        if not payload:
            complete = True
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
            complete = True
            break
        if len(payload) < per_page:
            complete = True
            break
    status = {
        "ok": True,
        "complete": complete,
        "pages_scanned": pages_scanned,
        "events_scanned": scanned,
        "result_limit": max_pages * per_page,
    }
    if not complete:
        status["warning"] = (
            "Result limit reached before the event feed crossed the requested start time."
        )
    return candidates, status


DISCUSSION_QUERY = """
query($search_query: String!, $after: String) {
  search(query: $search_query, type: DISCUSSION, first: 100, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Discussion {
        id title url createdAt author { login } repository { nameWithOwner }
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
    search_query = (
        f"owner:{owner} author:{user} type:discussion "
        f"created:{start.date().isoformat()}..{(end - dt.timedelta(microseconds=1)).date().isoformat()}"
    )
    candidates: List[JsonObject] = []
    cursor: Optional[str] = None
    pages_scanned = 0
    complete = False
    for _ in range(max_pages):
        arguments = [
            "graphql",
            "-f",
            f"query={DISCUSSION_QUERY}",
            "-f",
            f"search_query={search_query}",
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
                normalized = normalize_discussion(node, user)
                if normalized:
                    candidates.append(normalized)
        page_info = search.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            complete = True
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            raise RuntimeError("GitHub discussion search returned an empty next cursor")
    status = {
        "ok": True,
        "complete": complete,
        "pages_scanned": pages_scanned,
        "result_limit": max_pages * 100,
        "note": "Discussion replies are collected from user events when GitHub exposes them.",
    }
    if not complete:
        status["warning"] = "Result limit reached while more discussion search pages remained."
    return candidates, status


def status_for(statuses: JsonObject, authenticated: bool) -> str:
    if not authenticated:
        return "unavailable"
    successful_sources = [
        status for name, status in statuses.items() if name != "authenticated_user" and status["ok"]
    ]
    failed_sources = [
        status for name, status in statuses.items() if name != "authenticated_user" and not status["ok"]
    ]
    incomplete_sources = [
        status for status in successful_sources if status.get("complete") is False
    ]
    if (failed_sources and successful_sources) or incomplete_sources:
        return "partial"
    if failed_sources:
        return "failed"
    return "ok"


def collect(
    start: dt.datetime,
    end: dt.datetime,
    owner: str,
    max_pages: int = DEFAULT_MAX_PAGES,
    per_page: int = DEFAULT_PER_PAGE,
    run_command: RunCommand = default_run_command,
) -> JsonObject:
    """Collect supported sources and return the documented result shape."""
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
        sources = (
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
        )
        for source, function in sources:
            try:
                source_candidates, source_status = function()
                statuses[source] = source_status
                candidates.extend(source_candidates)
            except RuntimeError as error:
                statuses[source] = {"ok": False, "error": str(error)}
                errors.append({"source": source, "error": str(error)})

    deduplicated = {item["event_id"]: item for item in candidates}
    ordered = sorted(
        deduplicated.values(), key=lambda item: (item["event_at"], item["event_id"])
    )
    return {
        "collector": "github",
        "status": status_for(statuses, bool(user)),
        "candidate_count": len(ordered),
        "candidates": ordered,
        "errors": errors,
        "coverage": ["pull-requests", "reviews", "issues", "commits", "discussions"],
        "source_status": statuses,
    }


def write_json_output(path: Path, payload: JsonObject) -> None:
    """Write JSON through a same-directory temporary file and atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except OSError:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect read-only GitHub activity candidates as JSON."
    )
    parser.add_argument("--start", required=True, help="Inclusive ISO date or timestamp.")
    parser.add_argument("--end", required=True, help="Exclusive ISO timestamp or inclusive ISO date.")
    parser.add_argument("--owner", default=DEFAULT_OWNER, help="GitHub owner for discussion search.")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--per-page", type=int, default=DEFAULT_PER_PAGE)
    parser.add_argument("--output", type=Path, help="Write JSON atomically to this path.")
    parser.add_argument(
        "--timezone",
        help="IANA timezone for date-only boundaries. Defaults to the host local timezone.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        timezone = resolve_timezone(args.timezone)
        start = parse_range_boundary(args.start, timezone=timezone)
        end = parse_range_boundary(args.end, is_end=True, timezone=timezone)
        if start >= end:
            raise ValueError("--start must be before --end")
        if args.max_pages < 1 or args.per_page < 1 or args.per_page > 100:
            raise ValueError("--max-pages must be positive and --per-page must be 1 through 100")
    except (ValueError, ZoneInfoNotFoundError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    result = collect(start, end, args.owner, args.max_pages, args.per_page)
    if args.output:
        try:
            write_json_output(args.output, result)
        except OSError as error:
            result["errors"].append({"source": "output", "error": str(error)})
            result["status"] = "failed" if result["status"] == "unavailable" else "partial"
            print(json.dumps(result, indent=2, sort_keys=True))
            print(f"error: could not write {args.output}: {error}", file=sys.stderr)
            return 1
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
