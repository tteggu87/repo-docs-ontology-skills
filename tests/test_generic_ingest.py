import tempfile
import unittest
from pathlib import Path

from scripts.generic_ingest import ingest_source
from scripts.ingest.adapters.common import file_document_id
from scripts.ingest.resolver import resolve_family

ROOT = Path(__file__).resolve().parent.parent


class TestGenericIngest(unittest.TestCase):
    def test_resolver_email_not_ambiguous(self):
        fam = resolve_family(ROOT, Path("raw/inbox/email/week18.md"))
        self.assertEqual(fam, "email-md-txt")

    def test_profile_mismatch_errors(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "r.md"
            p.write_text("hello", encoding="utf-8")
            rel = p.relative_to(Path(td)).as_posix()
            # emulate repository shape
            repo = Path(td)
            (repo / "raw/inbox/reports").mkdir(parents=True, exist_ok=True)
            src = repo / "raw/inbox/reports/r.md"
            src.write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                ingest_source(ROOT, src.as_posix(), profile_id="email-analysis")

    def test_education_raw_path_stable_doc_id(self):
        src = ROOT / "raw/inbox/education/test-stable.md"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("# h\n\nbody", encoding="utf-8")
        out = ingest_source(ROOT, src.as_posix(), profile_id="education-analysis", allow_profile_family_mismatch=True)
        self.assertEqual(out["source_family_id"], "education-md-txt")
        expected = file_document_id("raw/inbox/education/test-stable.md")
        # pull the latest document row quickly
        rows = (ROOT / "warehouse/jsonl/documents.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertTrue(any(expected in line for line in rows))


if __name__ == "__main__":
    unittest.main()
