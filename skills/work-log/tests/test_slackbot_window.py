"""Synthetic-only tests for the Slackbot window. Never call Slack."""

from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "slackbot_window.py"
SPEC = importlib.util.spec_from_file_location("slackbot_window", MODULE_PATH)
assert SPEC and SPEC.loader
window = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = window
SPEC.loader.exec_module(window)

UTC = dt.timezone.utc
ZONE = ZoneInfo("America/Chicago")
USER = "U_ME"
MARKER = window.PROMPT_MARKER
NOW = dt.datetime(2026, 11, 2, 14, 0, 56, tzinfo=UTC)  # 2026-11-02 08:00:56 CST


def ts(iso: str) -> str:
    return f"{dt.datetime.fromisoformat(iso).timestamp():.6f}"


def prompt(at: str, text: str = f"{MARKER} Summarize my Slack activity.", replies: int = 1) -> dict:
    value = ts(at)
    return {"user": USER, "ts": value, "thread_ts": value, "text": text, "reply_count": replies}


def ai_reply(root: dict, status: str = "complete", parent: str = "") -> dict:
    return {
        "ts": f"{float(root['ts']) + 0.05:.6f}",
        "thread_ts": root["ts"],
        "user": "USLACKBOT",
        "subtype": "ai",
        "ai_context": {"parent_message_ts": parent or root["ts"], "result_status": status},
    }


def history(messages: list, next_cursor: str = "") -> dict:
    return {
        "ok": True,
        "messages": messages,
        "has_more": bool(next_cursor),
        "response_metadata": {"next_cursor": next_cursor},
    }


class FakeSlack:
    """Stand-in for `gh slack api get`. Pages are keyed by cursor; "" is the first page."""

    def __init__(self, pages: dict, threads: dict | None = None, overrides: dict | None = None):
        self.pages = pages
        self.threads = threads or {}
        self.overrides = overrides or {}
        self.calls: list = []

    def __call__(self, command):
        assert command[:4] == ["gh", "slack", "api", "get"], command
        assert command[command.index("--team") + 1] == "github", command
        method = command[4]
        fields = dict(
            command[index + 1].split("=", 1) for index, item in enumerate(command) if item == "-f"
        )
        self.calls.append((method, fields))
        if method in self.overrides:
            return self.overrides[method]
        if method == "auth.test":
            payload = {"ok": True, "user_id": USER}
        elif method == "conversations.history":
            payload = self.pages[fields.get("cursor", "")]
        elif method == "conversations.replies":
            payload = {"ok": True, "messages": self.threads.get(fields["ts"], [])}
        else:
            raise AssertionError(f"unexpected Slack method {method}")
        return 0, json.dumps(payload), ""

    def methods(self) -> list:
        return [method for method, _ in self.calls]


class SlackbotWindowTests(unittest.TestCase):
    def collect(self, slack, now=NOW, **options):
        return window.collect(now, ZONE, run_command=slack, **options)

    def answered(self, *prompts):
        return {item["ts"]: [item, ai_reply(item)] for item in prompts}

    def test_window_starts_at_the_send_time_of_the_newest_answered_prompt(self):
        newest = prompt(
            "2026-11-01T16:34:22-06:00",
            text=f"{MARKER} private detail, through Sunday 2026-11-01 23:59",
        )
        older = prompt("2026-11-01T12:10:29-06:00")
        other_user = {**prompt("2026-11-01T17:00:00-06:00"), "user": "U_OTHER"}
        unmarked = {**prompt("2026-11-01T16:50:00-06:00", text="how do i page git_systems")}
        reply_in_thread = {**prompt("2026-11-01T16:45:00-06:00"), "thread_ts": ts("2026-11-01T09:00:00-06:00")}
        slack = FakeSlack(
            {"": history([other_user, unmarked, reply_in_thread, newest, older])},
            self.answered(newest, older),
        )

        result = self.collect(slack)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["start_source"], "last-check")
        self.assertEqual(result["last_check"]["ts"], newest["ts"])
        self.assertEqual(result["start"], "2026-11-01T16:19:00-06:00")
        self.assertEqual(result["end"], "2026-11-02T08:00:00-06:00")
        self.assertEqual(result["start_text"], "Sunday 2026-11-01 16:19 CST")
        self.assertEqual(result["end_text"], "Monday 2026-11-02 08:00 CST")
        self.assertEqual(
            slack.methods(), ["auth.test", "conversations.history", "conversations.replies"]
        )
        self.assertNotIn("private detail", json.dumps(result))

    def test_prompts_without_a_matching_completed_reply_are_not_checks(self):
        unanswered = prompt("2026-11-02T07:00:00-06:00", replies=0)
        running = prompt("2026-11-01T18:00:00-06:00")
        mismatched = prompt("2026-11-01T17:00:00-06:00")
        answered = prompt("2026-11-01T12:00:00-06:00")
        slack = FakeSlack(
            {"": history([unanswered, running, mismatched, answered])},
            {
                running["ts"]: [running, ai_reply(running, status="in_progress")],
                mismatched["ts"]: [mismatched, ai_reply(mismatched, parent="1.000000")],
                **self.answered(answered),
            },
        )

        result = self.collect(slack)

        self.assertEqual(result["last_check"]["ts"], answered["ts"])
        self.assertEqual(result["history"]["skipped"], {"no-reply": 1, "no-completed-ai-reply": 2})

    def test_history_pages_are_followed_until_an_answered_prompt_is_found(self):
        answered = prompt("2026-10-30T12:00:00-05:00")
        slack = FakeSlack(
            {
                "": history([{"user": USER, "ts": ts("2026-11-01T10:00:00-06:00"), "text": "question"}], "page-2"),
                "page-2": history([answered]),
            },
            self.answered(answered),
        )

        result = self.collect(slack)

        self.assertEqual(result["last_check"]["ts"], answered["ts"])
        self.assertEqual(result["history"]["pages_read"], 2)
        self.assertEqual(slack.calls[2], ("conversations.history", {"channel": window.DEFAULT_CHANNEL, "limit": "200", "cursor": "page-2"}))

    def test_without_a_prior_check_the_window_starts_at_the_requested_start(self):
        result = self.collect(FakeSlack({"": history([])}))
        self.assertEqual(result["start_source"], "requested-range")
        self.assertEqual(result["fallback_reason"], "no-prior-check")
        self.assertEqual(result["start"], "2026-11-02T00:00:00-06:00")
        self.assertIsNone(result["last_check"])

        explicit = self.collect(
            FakeSlack({"": history([])}), fallback_start=window.parse_start("2026-10-30", ZONE)
        )
        self.assertEqual(explicit["start"], "2026-10-30T00:00:00-05:00")

    def test_too_many_unanswered_prompts_report_the_scan_limit(self):
        unanswered = [
            prompt(f"2026-10-{day:02d}T12:00:00-05:00", replies=0) for day in range(30, 10, -1)
        ]
        result = self.collect(FakeSlack({"": history(unanswered)}))
        self.assertEqual(result["fallback_reason"], "scan-limit-reached")
        self.assertEqual(result["history"]["prompts_found"], window.MAX_PROMPT_CHECKS)

    def test_slack_failures_return_the_requested_start_and_an_error(self):
        failures = {
            "auth.test": (1, "", "not logged in"),
            "conversations.history": (0, json.dumps({"ok": False, "error": "missing_scope"}), ""),
        }
        for method, response in failures.items():
            with self.subTest(method=method):
                result = self.collect(FakeSlack({}, overrides={method: response}))
                self.assertEqual(result["status"], "unavailable")
                self.assertEqual(result["start_source"], "requested-range")
                self.assertEqual(result["fallback_reason"], "history-unavailable")
                self.assertIn(method, result["errors"][0]["error"])

    def test_overlap_is_subtracted_in_utc_across_the_daylight_saving_change(self):
        # 01:10 CST is the second 01:10 on 2026-11-01. The overlap lands in CDT, one hour of offset away.
        answered = prompt("2026-11-01T01:10:00-06:00")
        slack = FakeSlack({"": history([answered])}, self.answered(answered))

        result = self.collect(slack)

        self.assertEqual(result["start"], "2026-11-01T01:55:00-05:00")
        self.assertEqual(result["end"], "2026-11-02T08:00:00-06:00")

    def test_window_is_never_shorter_than_the_overlap(self):
        recent = prompt("2026-11-02T08:01:00-06:00")  # after NOW: clock skew
        slack = FakeSlack({"": history([recent])}, self.answered(recent))

        result = self.collect(slack)

        self.assertEqual(result["start"], "2026-11-02T07:45:00-06:00")
        self.assertEqual(result["end"], "2026-11-02T08:00:00-06:00")

    def test_cli_prints_json_and_rejects_invalid_options(self):
        slack = FakeSlack({"": history([])})
        output = io.StringIO()
        with patch.object(window, "default_run_command", slack), patch.object(
            window, "current_time", return_value=NOW
        ), contextlib.redirect_stdout(output):
            code = window.main(["--timezone", "America/Chicago"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["start"], "2026-11-02T00:00:00-06:00")

        for arguments in (["--timezone", "Mars/Base"], ["--overlap-minutes", "0"], ["--marker", " "]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(window.main(arguments), 2)


if __name__ == "__main__":
    unittest.main()
