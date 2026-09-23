"""Unit tests for the read-only GitHub activity collector."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "github_activity.py"
SPEC = importlib.util.spec_from_file_location("github_activity", MODULE_PATH)
assert SPEC and SPEC.loader
github_activity = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = github_activity
SPEC.loader.exec_module(github_activity)


def event(event_type: str, payload: dict, event_id: str = "1") -> dict:
    return {
        "id": event_id,
        "type": event_type,
        "created_at": "2026-09-22T15:00:00Z",
        "actor": {"login": "octocat"},
        "repo": {"name": "github/example"},
        "payload": payload,
    }


class PureNormalizationTests(unittest.TestCase):
    def test_canonical_url_removes_query_fragment_and_trailing_slash(self) -> None:
        self.assertEqual(
            github_activity.canonical_url("https://github.com/github/example/pull/1/?a=b#review"),
            "https://github.com/github/example/pull/1",
        )

    def test_pr_and_submitted_review_are_normalized(self) -> None:
        pr = {
            "number": 2,
            "title": "Improve collector",
            "html_url": "https://github.com/github/example/pull/2/",
            "user": {"login": "octocat"},
            "merged": False,
        }
        pr_candidates = github_activity.normalize_event(
            event("PullRequestEvent", {"action": "opened", "pull_request": pr}, "10"),
            "octocat",
            "github",
        )
        review_candidates = github_activity.normalize_event(
            event(
                "PullRequestReviewEvent",
                {
                    "action": "submitted",
                    "pull_request": pr,
                    "review": {
                        "state": "submitted",
                        "user": {"login": "octocat"},
                        "html_url": "https://github.com/github/example/pull/2#review",
                    },
                },
                "11",
            ),
            "octocat",
            "github",
        )
        self.assertEqual(pr_candidates[0]["roles"], ["author"])
        self.assertEqual(pr_candidates[0]["url"], "https://github.com/github/example/pull/2")
        self.assertEqual(review_candidates[0]["source_type"], "github-review")
        self.assertEqual(review_candidates[0]["roles"], ["reviewer"])

    def test_dismissed_or_draft_review_is_excluded(self) -> None:
        candidates = github_activity.normalize_event(
            event(
                "PullRequestReviewEvent",
                {
                    "action": "edited",
                    "review": {"state": "approved", "user": {"login": "octocat"}},
                },
            ),
            "octocat",
            "github",
        )
        self.assertEqual(candidates, [])

    def test_issue_assignment_and_substantive_comment_are_normalized(self) -> None:
        issue = {
            "title": "Fix event handling",
            "html_url": "https://github.com/github/example/issues/4",
            "user": {"login": "someone-else"},
            "assignees": [{"login": "octocat"}],
        }
        assigned = github_activity.normalize_event(
            event("IssuesEvent", {"action": "assigned", "issue": issue}, "12"),
            "octocat",
            "github",
        )
        commented = github_activity.normalize_event(
            event(
                "IssueCommentEvent",
                {
                    "issue": issue,
                    "comment": {
                        "user": {"login": "octocat"},
                        "html_url": "https://github.com/github/example/issues/4#issuecomment-1",
                        "body": "This is a substantive comment with enough detail to show the technical reasoning.",
                    },
                },
                "13",
            ),
            "octocat",
            "github",
        )
        self.assertEqual(assigned[0]["roles"], ["assignee"])
        self.assertEqual(commented[0]["source_type"], "github-issue-comment")

    def test_short_comment_is_excluded_and_push_commit_id_is_stable(self) -> None:
        short_comment = github_activity.normalize_event(
            event(
                "IssueCommentEvent",
                {"comment": {"user": {"login": "octocat"}, "body": "looks good"}},
                "14",
            ),
            "octocat",
            "github",
        )
        commits = github_activity.normalize_event(
            event(
                "PushEvent",
                {
                    "ref": "refs/heads/main",
                    "commits": [{"sha": "abc123", "message": "Record activity"}],
                },
                "15",
            ),
            "octocat",
            "github",
        )
        self.assertEqual(short_comment, [])
        self.assertEqual(commits[0]["id"], "github-event:15:abc123")
        self.assertEqual(commits[0]["url"], "https://github.com/github/example/commit/abc123")

    def test_authored_discussion_is_normalized(self) -> None:
        candidate = github_activity.normalize_discussion(
            {
                "id": "D_kwDO123",
                "title": "Collector design",
                "url": "https://github.com/org/repo/discussions/1/",
                "createdAt": "2026-09-22T15:00:00Z",
                "author": {"login": "octocat"},
                "repository": {"nameWithOwner": "org/repo"},
            },
            "octocat",
        )
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["id"], "github-discussion:D_kwDO123")
        self.assertEqual(candidate["url"], "https://github.com/org/repo/discussions/1")


class CollectionTests(unittest.TestCase):
    def test_collect_reports_a_source_failure_without_losing_other_candidates(self) -> None:
        user_events = [
            event(
                "PullRequestEvent",
                {
                    "action": "opened",
                    "pull_request": {
                        "title": "Useful PR",
                        "html_url": "https://github.com/github/example/pull/1",
                        "user": {"login": "octocat"},
                    },
                },
                "20",
            )
        ]

        def fake_run(command: list[str]) -> tuple[int, str, str]:
            joined = " ".join(command)
            if command[-1] == "/user":
                return 0, json.dumps({"login": "octocat"}), ""
            if "/user/events?" in joined:
                return 0, json.dumps(user_events if "page=1" in joined else []), ""
            if "graphql" in command:
                return 1, "", "GraphQL unavailable"
            self.fail(f"Unexpected command: {command}")

        result = github_activity.collect(
            dt.datetime(2026, 9, 22, tzinfo=dt.timezone.utc),
            dt.datetime(2026, 9, 23, tzinfo=dt.timezone.utc),
            "github",
            max_pages=2,
            run_command=fake_run,
        )
        self.assertEqual(len(result["candidates"]), 1)
        self.assertFalse(result["collector_status"]["ok"])
        self.assertEqual(result["errors"], [{"source": "discussions", "error": "GraphQL unavailable"}])

    def test_gh_json_uses_subprocess_only_through_default_runner(self) -> None:
        completed = subprocess.CompletedProcess(["gh"], 0, '{"login":"octocat"}', "")
        with patch.object(github_activity.subprocess, "run", return_value=completed) as mocked:
            self.assertEqual(github_activity.gh_json(["/user"]), {"login": "octocat"})
        mocked.assert_called_once_with(
            ["gh", "api", "/user"], capture_output=True, text=True, check=False
        )

    def test_date_end_is_inclusive_for_a_date_argument(self) -> None:
        self.assertEqual(
            github_activity.parse_range_boundary("2026-09-22", is_end=True),
            dt.datetime(2026, 9, 23, tzinfo=dt.timezone.utc),
        )


if __name__ == "__main__":
    unittest.main()
