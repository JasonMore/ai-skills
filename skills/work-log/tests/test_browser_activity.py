"""Synthetic-only tests for Dia visit evidence. Never read real browser data."""

from __future__ import annotations

import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts/browser_activity.py"
SPEC = importlib.util.spec_from_file_location("browser_activity", MODULE_PATH)
assert SPEC and SPEC.loader
browser = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(browser)
UTC = dt.timezone.utc
ZONE = ZoneInfo("America/Chicago")
PR = "https://github.com/github/example/pull/12"


def timestamp(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


class BrowserActivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="work-log-browser-test-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        (self.root / "Local State").write_text(json.dumps({"profile": {"last_used": "Work"}}))
        self.snapshot_paths = []
        temporary_directory = tempfile.TemporaryDirectory

        def track_snapshot(*args, **kwargs):
            self.assertNotIn("dir", kwargs)
            directory = temporary_directory(*args, **kwargs)
            path = Path(directory.name).resolve()
            self.assertFalse(path.is_relative_to(Path.cwd()))
            self.snapshot_paths.append(path)
            return directory

        snapshot_patch = patch.object(browser.tempfile, "TemporaryDirectory", side_effect=track_snapshot)
        snapshot_patch.start()
        self.addCleanup(snapshot_patch.stop)

    def history(self, profile: str = "Work", visits: list | None = None, wal: bool = False):
        directory = self.root / profile
        directory.mkdir(exist_ok=True)
        db = sqlite3.connect(directory / "History")
        if wal:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA wal_autocheckpoint=0")
        db.executescript(
            "CREATE TABLE urls(id INTEGER PRIMARY KEY, url TEXT, title TEXT);"
            "CREATE TABLE visits(id INTEGER PRIMARY KEY, url INTEGER, visit_time INTEGER, visit_duration INTEGER);"
        )
        for index, (at, url) in enumerate(visits or [], 1):
            db.execute("INSERT INTO urls VALUES (?, ?, ?)", (index, url, "PRIVATE TITLE secret-query"))
            db.execute("INSERT INTO visits VALUES (?, ?, ?, ?)",
                       (index, index, browser.chromium_time(timestamp(at)), 999999999))
        db.commit()
        if wal:
            self.addCleanup(db.close)
            return db
        db.close()
        return None

    def collect(self, start="2026-10-27", end="2026-10-27", **kwargs):
        result = browser.collect(
            browser.parse_range_boundary(start, timezone=ZONE),
            browser.parse_range_boundary(end, is_end=True, timezone=ZONE),
            timezone=ZONE, user_data_dir=self.root, **kwargs,
        )
        self.assertTrue(all(not path.exists() for path in self.snapshot_paths))
        return result

    def test_inclusive_dates_exclusive_timestamp_and_date_bounded_query(self):
        self.history(visits=[
            ("2026-10-27T04:59:59Z", PR),
            ("2026-10-27T05:00:00Z", PR),
            ("2026-10-28T04:59:59Z", PR),
            ("2026-10-28T05:00:00Z", PR),
        ])
        result = self.collect()
        self.assertEqual(result["source_status"]["Work"]["visit_rows_in_range"], 2)
        self.assertEqual(result["candidates"][0]["visit_count"], 2)
        self.assertEqual(self.collect(end="2026-10-27T05:00:01Z")["candidates"][0]["visit_count"], 1)

    def test_midnight_and_dst_grouping(self):
        self.history(visits=[
            ("2026-11-01T04:59:59Z", PR),
            ("2026-11-01T05:00:00Z", PR),
            ("2026-11-01T06:30:00Z", PR),
            ("2026-11-01T07:30:00Z", PR),
            ("2026-11-02T05:59:59Z", PR),
            ("2026-11-02T06:00:00Z", PR),
        ])
        result = self.collect(start="2026-10-31", end="2026-11-01")
        self.assertEqual([item["visit_count"] for item in result["candidates"]], [1, 4])
        begin = browser.parse_range_boundary("2026-11-01", timezone=ZONE)
        end = browser.parse_range_boundary("2026-11-01", is_end=True, timezone=ZONE)
        self.assertEqual(end - begin, dt.timedelta(hours=25))
        spring_begin = browser.parse_range_boundary("2026-03-08", timezone=ZONE)
        spring_end = browser.parse_range_boundary("2026-03-08", is_end=True, timezone=ZONE)
        self.assertEqual(spring_end - spring_begin, dt.timedelta(hours=23))

    def test_pr_subpages_single_visit_and_visit_only_evidence(self):
        self.history(visits=[("2026-10-27T12:00:00Z", PR + "/files?secret=query#fragment")])
        item = self.collect()["candidates"][0]
        self.assertEqual(item["source"]["url"], PR)
        self.assertEqual(item["context_sources"], [{"type": "github-pr", "id": "github/example#12", "url": PR}])
        self.assertEqual(item["role"], "visitor")
        self.assertEqual(item["event_type"], "browser-visit")
        self.assertEqual(item["confidence"], "high")
        self.assertEqual(item["event_sources"], [])
        self.assertIn("Visit evidence only", " ".join(item["summary_facts"]))
        self.assertNotIn("Submitted", json.dumps(item))
        for private in ("PRIVATE TITLE", "secret", "query", "fragment", "999999999", "visit_duration"):
            self.assertNotIn(private, json.dumps(item))

    def test_repeated_visits_source_stability_and_profile_namespaces(self):
        self.history(visits=[("2026-10-27T12:00:00Z", PR)])
        original = self.collect()["candidates"][0]
        with sqlite3.connect(self.root / "Work/History") as db:
            db.execute("INSERT INTO visits VALUES (2, 1, ?, 0)",
                       (browser.chromium_time(timestamp("2026-10-27T13:00:00Z")),))
        self.history("Other", [("2026-10-27T12:01:00Z", PR)])
        item = self.collect(profiles=["Work", "Other"])["candidates"][0]
        self.assertEqual(item["event_id"], original["event_id"])
        self.assertEqual(item["visit_count"], 3)
        sources = [item["source"], *item["event_sources"]]
        self.assertEqual(len({source["id"] for source in sources}), 3)
        self.assertTrue(all(source["event_at"] for source in sources))
        self.assertNotEqual(browser.source_id(self.root, "Work", 1, 2),
                            browser.source_id(self.root / "another", "Work", 1, 2))
        self.assertNotEqual(browser.source_id(self.root, "A:B", 1, 2),
                            browser.source_id(self.root, "A", 1, 2))

    def test_canonical_privacy_and_owner_boundaries(self):
        bad = [
            "file:///github/example", "https://github.com.evil/github/example",
            "https://evil.github.com/github/example", "https://github.com/other/example",
            "https://github.com/github-spoof/example", "https://github.com/github/settings",
            PR + "/oauth/callback", PR + "/%73ettings", PR + "/%2574oken",
            "https://user:pass@github.com/github/example", "https://github.com:444/github/example",
            "https://github.com/github/example/unknown", "https://github.com/github/../other",
            PR + "/login", PR + "/access_token", PR + "/password/reset",
            PR + "/auth", PR + "/oauth2", "https://github.com/github//example",
            "https://github.com/github/example\\settings", PR + "/%0a",
        ]
        for url in bad:
            with self.subTest(url=url):
                self.assertIsNone(browser.canonical_page(url, "github", {"github.com"})[0])
        for suffix in ("", "/files", "/commits", "/checks"):
            self.assertEqual(browser.canonical_page(PR + suffix + "?q=private#private", "github", set())[0], PR)
        self.assertEqual(browser.canonical_page("https://github.com/github/example/blob/main/docs/usage.md", "github", set())[0],
                         "https://github.com/github/example/blob/main/docs/usage.md")

    def test_exact_host_opt_in(self):
        self.assertEqual(browser.canonical_page("https://work.example/docs?q=secret#x", "github", {"work.example"})[0],
                         "https://work.example/docs")
        for url in ("https://sub.work.example/docs", "https://work.example.evil/docs",
                    "https://work.example/settings", "https://work.example/oauth/callback",
                    "https://me@work.example/docs"):
            self.assertIsNone(browser.canonical_page(url, "github", {"work.example"})[0])
        self.assertIsNone(browser.canonical_page("https://work.example/docs", "github", set())[0])

    def test_default_profile_only_and_explicit_profiles_without_local_state(self):
        self.history(visits=[("2026-10-27T12:00:00Z", PR)])
        self.history("Personal", [("2026-10-27T12:00:00Z", PR + "/files")])
        result = self.collect()
        self.assertEqual(result["profile_coverage"]["selected"], ["Work"])
        self.assertEqual(result["candidates"][0]["visit_count"], 1)
        (self.root / "Local State").unlink()
        self.assertEqual(self.collect()["status"], "unavailable")
        self.assertEqual(self.collect(profiles=["Work"])["status"], "ok")

    def test_invalid_last_used_does_not_guess(self):
        self.history()
        for state in ({}, {"profile": {"last_used": "../Work"}}, {"profile": {"last_used": ["Work"]}},
                      {"profile": {"last_used": ""}}):
            (self.root / "Local State").write_text(json.dumps(state))
            self.assertEqual(self.collect()["status"], "unavailable")
        (self.root / "Local State").write_text("not json")
        self.assertEqual(self.collect()["status"], "unavailable")

    def test_empty_success_missing_malformed_and_partial_profiles(self):
        self.history()
        empty = self.collect()
        self.assertEqual((empty["status"], empty["candidate_count"]), ("ok", 0))
        missing = self.collect(profiles=["Missing"])
        self.assertEqual(missing["status"], "unavailable")
        malformed = self.root / "Broken"
        malformed.mkdir()
        (malformed / "History").write_text("not SQLite; PRIVATE TITLE ?secret=42")
        partial = self.collect(profiles=["Work", "Broken", "Missing"])
        self.assertEqual(partial["status"], "partial")
        self.assertEqual(partial["profile_coverage"]["successful"], 1)
        self.assertEqual(len(partial["errors"]), 2)
        self.assertNotIn("secret", json.dumps(partial["errors"]))

    def test_partial_failure_preserves_visits(self):
        self.history(visits=[("2026-10-27T12:00:00Z", PR)])
        result = self.collect(profiles=["Missing", "Work"])
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["candidate_count"], 1)

    def test_selected_profile_cannot_escape_root(self):
        self.history()
        (self.root / "Alias").symlink_to(self.root.parent, target_is_directory=True)
        result = self.collect(profiles=["Alias", "Work"])
        self.assertEqual(result["status"], "partial")
        self.assertFalse(result["source_status"]["Alias"]["ok"])
        self.assertEqual(result["profile_coverage"]["successful"], 1)

    def test_snapshot_permission_error_is_safe(self):
        self.history()
        with patch.object(browser.shutil, "copyfile", side_effect=PermissionError("PRIVATE URL ?secret=x")):
            result = self.collect()
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["errors"][0]["error"], "History snapshot permission denied")
        self.assertNotIn("secret", json.dumps(result))

    def test_wal_snapshot_cleanup_and_source_unchanged(self):
        self.history(visits=[("2026-10-27T12:00:00Z", PR)], wal=True)
        files = list((self.root / "Work").iterdir())
        before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in files}
        result = self.collect()
        self.assertEqual(result["candidate_count"], 1)
        self.assertTrue((self.root / "Work/History-wal").exists())
        self.assertEqual(before, {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in files})
        self.assertTrue(self.snapshot_paths)
        self.assertTrue(all(not path.exists() for path in self.snapshot_paths))

    def test_exclusive_live_lock_uses_copy_not_live_sqlite(self):
        self.history(visits=[("2026-10-27T12:00:00Z", PR)])
        db = sqlite3.connect(self.root / "Work/History")
        try:
            db.execute("BEGIN EXCLUSIVE")
            self.assertEqual(self.collect()["candidate_count"], 1)
        finally:
            db.close()

    def test_snapshot_retries_changed_files_and_cleans_failed_snapshot(self):
        self.history()
        original = browser.file_states
        calls = 0

        def changed(path):
            nonlocal calls
            calls += 1
            states = original(path)
            if calls % 2 == 0:
                states[""] = (0, 0, calls, 0)
            return states

        with patch.object(browser, "file_states", side_effect=changed):
            result = self.collect()
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(calls, 6)
        self.assertTrue(all(not path.exists() for path in self.snapshot_paths))
        with patch.object(browser.sqlite3, "connect", side_effect=sqlite3.OperationalError("locked ?secret=query")):
            result = self.collect()
        self.assertNotIn("secret", json.dumps(result))
        self.assertEqual(result["status"], "unavailable")
        self.assertTrue(all(not path.exists() for path in self.snapshot_paths))

    def test_skipped_counts_and_limits(self):
        self.history(visits=[
            ("2026-10-27T12:00:00Z", "https://personal.example/path?secret=42"),
            ("2026-10-27T13:00:00Z", "https://github.com/github/example/settings"),
        ])
        result = self.collect()
        self.assertEqual(result["skipped"], {"unapproved_host": 1, "sensitive_route": 1})
        self.assertEqual(result["status"], "ok")
        self.assertTrue(any("Private browsing" in item for item in result["limits"]))
        self.assertNotIn("secret", json.dumps(result))

    def test_cli_and_invalid_inputs(self):
        self.history()
        args = ["--start", "2026-10-27", "--end", "2026-10-27", "--timezone", "America/Chicago",
                "--user-data-dir", str(self.root)]
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(browser.main(args), 0)
            self.assertEqual(json.loads(stdout.getvalue())["status"], "ok")
        for extra in (["--timezone", "Invalid/Zone"], ["--owner", "../github"],
                      ["--allow-host", "https://work.example"], ["--end", "2026-10-26"],
                      ["--start", "2026-10-27T12:00:00"]):
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(browser.main(args + extra), 2)


if __name__ == "__main__":
    unittest.main()
