"""Unit tests for the read-only GitHub activity collector."""

from __future__ import annotations

import datetime as dt
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
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


def assert_candidate_schema(test: unittest.TestCase, value: dict) -> None:
    test.assertEqual(
        set(value),
        {
            "event_id",
            "event_at",
            "event_type",
            "title",
            "summary_facts",
            "focus_hints",
            "source",
            "context_sources",
            "role",
            "confidence",
        },
    )
    test.assertTrue(value["event_id"])
    test.assertTrue(value["event_at"])
    test.assertTrue(value["summary_facts"])
    test.assertEqual(value["confidence"], "high")
    test.assertTrue(value["source"]["type"])
    test.assertTrue(value["source"]["id"])


class PureNormalizationTests(unittest.TestCase):
    def test_canonical_url_keeps_only_event_fragments_when_requested(self) -> None:
        source = "https://github.com/github/example/pull/1/?a=b#pullrequestreview-3"
        self.assertEqual(
            github_activity.canonical_url(source),
            "https://github.com/github/example/pull/1",
        )
        self.assertEqual(
            github_activity.canonical_url(source, preserve_fragment=True),
            "https://github.com/github/example/pull/1#pullrequestreview-3",
        )

    def test_reviews_accept_actionable_submitted_states_and_use_review_identity(self) -> None:
        pr = {
            "number": 2,
            "title": "Improve collector",
            "html_url": "https://github.com/github/example/pull/2/",
        }
        approved = github_activity.normalize_event(
            event(
                "PullRequestReviewEvent",
                {
                    "action": "submitted",
                    "pull_request": pr,
                    "review": {
                        "node_id": "PRR_approved",
                        "state": "approved",
                        "user": {"login": "octocat"},
                        "html_url": "https://github.com/github/example/pull/2#pullrequestreview-3",
                    },
                },
                "10",
            ),
            "octocat",
            "github",
        )[0]
        commented = github_activity.normalize_event(
            event(
                "PullRequestReviewEvent",
                {
                    "action": "submitted",
                    "pull_request": pr,
                    "review": {
                        "id": 4,
                        "state": "commented",
                        "user": {"login": "octocat"},
                        "body": "This change can race with a retry and should retain the original cache key.",
                    },
                },
                "11",
            ),
            "octocat",
            "github",
        )[0]
        assert_candidate_schema(self, approved)
        self.assertEqual(approved["event_id"], "github-review:PRR_approved")
        self.assertEqual(approved["source"]["id"], "PRR_approved")
        self.assertEqual(approved["source"]["url"].split("#")[1], "pullrequestreview-3")
        self.assertIn("Review state: approved.", approved["summary_facts"])
        self.assertEqual(commented["source"]["id"], "4")
        self.assertIn("Review state: commented.", commented["summary_facts"])

    def test_reviews_exclude_pending_dismissed_and_low_signal_comments(self) -> None:
        for state, body in (
            ("pending", "This is a substantive review comment with enough implementation details."),
            ("dismissed", "This is a substantive review comment with enough implementation details."),
            ("commented", "looks good"),
        ):
            candidates = github_activity.normalize_event(
                event(
                    "PullRequestReviewEvent",
                    {
                        "action": "submitted",
                        "review": {
                            "id": 1,
                            "state": state,
                            "user": {"login": "octocat"},
                            "body": body,
                        },
                    },
                ),
                "octocat",
                "github",
            )
            self.assertEqual(candidates, [])

    def test_issue_assignment_is_excluded_and_actor_can_close_another_authors_issue(self) -> None:
        issue = {
            "number": 4,
            "title": "Fix event handling",
            "html_url": "https://github.com/github/example/issues/4",
            "user": {"login": "someone-else"},
            "assignees": [{"login": "octocat"}],
        }
        assignment = github_activity.normalize_event(
            event("IssuesEvent", {"action": "assigned", "issue": issue}, "12"),
            "octocat",
            "github",
        )
        closed = github_activity.normalize_event(
            event("IssuesEvent", {"action": "closed", "issue": issue}, "13"),
            "octocat",
            "github",
        )[0]
        self.assertEqual(assignment, [])
        assert_candidate_schema(self, closed)
        self.assertEqual(closed["role"], "closer")
        self.assertEqual(closed["source"], {
            "type": "github-event",
            "id": "13",
            "url": "https://github.com/github/example/issues/4",
        })

    def test_comment_and_commit_keep_native_source_identity(self) -> None:
        comment = github_activity.normalize_event(
            event(
                "IssueCommentEvent",
                {
                    "issue": {
                        "number": 4,
                        "title": "Issue",
                        "html_url": "https://github.com/github/example/issues/4#ordinary",
                    },
                    "comment": {
                        "node_id": "IC_123",
                        "user": {"login": "octocat"},
                        "html_url": "https://github.com/github/example/issues/4#issuecomment-1",
                        "body": "This is a substantive comment with enough detail to show the technical reasoning.",
                    },
                },
                "14",
            ),
            "octocat",
            "github",
        )[0]
        commit = github_activity.normalize_event(
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
        )[0]
        assert_candidate_schema(self, comment)
        assert_candidate_schema(self, commit)
        self.assertEqual(comment["source"]["id"], "IC_123")
        self.assertTrue(comment["source"]["url"].endswith("#issuecomment-1"))
        self.assertEqual(commit["event_id"], "github-commit:github/example@abc123")
        self.assertEqual(commit["source"]["id"], "abc123")

    def test_authored_discussion_matches_schema(self) -> None:
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
        assert_candidate_schema(self, candidate)
        self.assertEqual(candidate["event_id"], "github-discussion:D_kwDO123")


class CollectionTests(unittest.TestCase):
    def test_collect_reports_partial_status_and_documented_result_shape(self) -> None:
        user_events = [
            event(
                "PullRequestEvent",
                {
                    "action": "opened",
                    "pull_request": {
                        "number": 1,
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
        self.assertEqual(result["collector"], "github")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(
            result["coverage"],
            ["pull-requests", "reviews", "issues", "commits", "discussions"],
        )
        self.assertEqual(result["errors"], [{"source": "discussions", "error": "GraphQL unavailable"}])
        assert_candidate_schema(self, result["candidates"][0])

    def test_output_write_is_atomic_for_normal_use(self) -> None:
        payload = {"collector": "github", "status": "ok"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activity.json"
            github_activity.write_json_output(path, payload)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), payload)
            self.assertEqual(list(Path(directory).glob(".activity.json.*")), [])

    def test_output_error_is_reported_in_json(self) -> None:
        result = {
            "collector": "github",
            "status": "ok",
            "candidate_count": 0,
            "candidates": [],
            "errors": [],
            "coverage": [],
        }
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch.object(github_activity, "collect", return_value=result),
            patch.object(
                github_activity,
                "write_json_output",
                side_effect=PermissionError("permission denied"),
            ),
            patch.object(sys, "stdout", stdout),
            patch.object(sys, "stderr", stderr),
        ):
            exit_code = github_activity.main(
                ["--start", "2026-09-22", "--end", "2026-09-22", "--output", "out.json"]
            )
        self.assertEqual(exit_code, 1)
        self.assertEqual(json.loads(stdout.getvalue())["errors"][0]["source"], "output")
        self.assertIn("could not write out.json", stderr.getvalue())

    def test_gh_json_uses_subprocess_only_through_default_runner(self) -> None:
        completed = subprocess.CompletedProcess(["gh"], 0, '{"login":"octocat"}', "")
        with patch.object(github_activity.subprocess, "run", return_value=completed) as mocked:
            self.assertEqual(github_activity.gh_json(["/user"]), {"login": "octocat"})
        mocked.assert_called_once_with(
            ["gh", "api", "/user"], capture_output=True, text=True, check=False
        )

    def test_date_only_boundaries_use_supplied_local_timezone(self) -> None:
        utc_minus_five = dt.timezone(dt.timedelta(hours=-5))
        self.assertEqual(
            github_activity.parse_range_boundary("2026-09-23", timezone=utc_minus_five),
            dt.datetime(2026, 9, 23, 5, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(
            github_activity.parse_range_boundary(
                "2026-09-23", is_end=True, timezone=utc_minus_five
            ),
            dt.datetime(2026, 9, 24, 5, tzinfo=dt.timezone.utc),
        )


if __name__ == "__main__":
    unittest.main()
