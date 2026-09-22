import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "import_kb_deck.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "import_kb_deck"

SPEC = importlib.util.spec_from_file_location("import_kb_deck", SCRIPT)
IMPORTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(IMPORTER)


def flattened(sections):
    slides = []
    for section in sections:
        slides.append(section["lesson"])
        slides.extend(section["cases"])
    return slides


class ImportKbDeckTests(unittest.TestCase):
    def test_fmx_and_per_slide_fixtures_match_title_order_and_note_counts(self):
        kb_dir = FIXTURES / "per-slide"
        kb_manifest = IMPORTER.load_manifest(kb_dir / "SECTIONS.json")
        kb_sections, _, _ = IMPORTER.build_sections(kb_dir, kb_manifest)

        fmx_dir = FIXTURES / "fmx"
        fmx_manifest = IMPORTER.load_manifest(fmx_dir / "SECTIONS.json")
        fmx_sections, _, _, _ = IMPORTER.build_fmx_sections(
            fmx_manifest, (fmx_dir / "slides.md").read_text(encoding="utf-8")
        )

        kb_slides = flattened(kb_sections)
        fmx_slides = flattened(fmx_sections)
        self.assertEqual([slide["title"] for slide in kb_slides],
                         [slide["title"] for slide in fmx_slides])
        self.assertEqual(len(kb_slides), 3)
        self.assertEqual(sum(bool(slide.get("notes")) for slide in kb_slides), 3)
        self.assertEqual(sum(bool(slide.get("notes")) for slide in fmx_slides), 3)
        self.assertEqual(fmx_slides[0]["notes"], "Open with the shared question.")

    def test_both_fixture_modes_exit_zero(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for fixture in ("per-slide", "fmx"):
                output = Path(temp_dir) / f"{fixture}.html"
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), str(FIXTURES / fixture),
                     "--out", str(output)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(output.is_file())
                self.assertIn("slides=3", result.stdout)

    def test_malformed_manifest_fails_clearly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "bad.html"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(FIXTURES / "malformed"),
                 "--out", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("error: malformed SECTIONS.json", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
