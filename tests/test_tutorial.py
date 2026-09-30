from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TutorialTests(unittest.TestCase):
    def test_inline_reference_files_match_source(self):
        text = (ROOT / "TUTORIAL.md").read_text()
        blocks = re.findall(
            r"\*\*`([^`]+)`\*\*\n\n```bitbake\n(.*?)\n```", text, re.S
        )
        self.assertGreaterEqual(len(blocks), 12)
        for filename, content in blocks:
            with self.subTest(filename=filename):
                self.assertEqual((ROOT / filename).read_text(), content + "\n")

    def test_local_document_links_exist(self):
        for document in ("README.md", "TUTORIAL.md", "VALIDATION.md"):
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", (ROOT / document).read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(document=document, target=target):
                    self.assertTrue((ROOT / target.split("#", 1)[0]).exists())


if __name__ == "__main__":
    unittest.main()
