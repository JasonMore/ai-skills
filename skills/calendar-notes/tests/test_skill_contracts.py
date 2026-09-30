from pathlib import Path
import re
import unittest


SKILLS_DIR = Path(__file__).resolve().parents[2]
SKILL_NAMES = {
    "calendar-notes": "calendar-notes",
    "update-daily-snippet": "update-daily-snippet",
    "meeting-notes-skill": "meeting-notes",
}


class LinkedNoteContractTest(unittest.TestCase):
    def test_skill_structure_and_local_links(self):
        for directory, name in SKILL_NAMES.items():
            skill_dir = SKILLS_DIR / directory
            with self.subTest(skill=name):
                text = (skill_dir / "SKILL.md").read_text()
                self.assertTrue(text.startswith("---\n"))
                self.assertIn(f"\nname: {name}\n", text)
                self.assertLess(len(text.splitlines()), 200)
            for path in skill_dir.rglob("*.md"):
                text = path.read_text()
                for link in re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", text):
                    if "://" in link:
                        continue
                    with self.subTest(document=path.name, link=link):
                        self.assertTrue((path.parent / link).is_file())

    def test_shared_date_rules_cover_empty_sections_and_boundaries(self):
        text = (
            SKILLS_DIR / "calendar-notes/references/date-sections.md"
        ).read_text()
        for rule in (
            "Ignore headings inside fenced code blocks.",
            "after YAML",
            "next date heading, not the next topic heading",
            "An empty section is a valid target.",
            "including old bullets",
            "Do not add a summary",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, text)

    def test_calendar_repairs_existing_links_and_persists_notes(self):
        text = (SKILLS_DIR / "calendar-notes/SKILL.md").read_text()
        for rule in (
            "Include links already present",
            "Ensure each linked note has the event's date section.",
            "and linked notes",
            "Return no-op only when calendar bullets and all linked date sections exist.",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, text)

    def test_daily_workflow_requires_linked_date_sections(self):
        text = (SKILLS_DIR / "update-daily-snippet/SKILL.md").read_text()
        self.assertIn("exist in every linked note", text)
        self.assertIn("Report a missing section as a calendar", text)
        self.assertIn("Calendar targets include linked notes", text)

    def test_meeting_summaries_do_not_require_handwritten_notes(self):
        text = (SKILLS_DIR / "meeting-notes-skill/SKILL.md").read_text()
        for rule in (
            "Handwritten notes are optional.",
            "Create it when no notes were taken.",
            "before the next date heading",
            "If its summary",
            "<!-- meeting-summary: SOURCE_ID -->",
            "Do not invent a summary",
            "Invoke `persist-work-notes` once",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, text)


if __name__ == "__main__":
    unittest.main()
