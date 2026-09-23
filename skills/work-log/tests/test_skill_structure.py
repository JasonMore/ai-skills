from pathlib import Path
import re
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_FILE = SKILL_DIR / "SKILL.md"


class SkillStructureTest(unittest.TestCase):
    def test_skill_file_stays_under_200_lines(self):
        self.assertLess(len(SKILL_FILE.read_text().splitlines()), 200)

    def test_frontmatter_has_expected_name(self):
        text = SKILL_FILE.read_text()
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("\nname: work-log\n", text)

    def test_local_markdown_links_exist(self):
        text = SKILL_FILE.read_text()
        links = re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", text)
        self.assertGreater(len(links), 0)
        for link in links:
            with self.subTest(link=link):
                self.assertTrue((SKILL_DIR / link).is_file())

    def test_docs_do_not_use_en_or_em_dashes(self):
        docs = [SKILL_FILE, *(SKILL_DIR / "references").glob("*.md")]
        for path in docs:
            with self.subTest(path=path.name):
                text = path.read_text()
                self.assertNotIn("\N{EN DASH}", text)
                self.assertNotIn("\N{EM DASH}", text)


if __name__ == "__main__":
    unittest.main()
