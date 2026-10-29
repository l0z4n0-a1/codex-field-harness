import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from handoff import create, resume, save


class HandoffTests(unittest.TestCase):
    def test_resume_hash_revocation_missing_file_and_writer(self):
        fixture = pathlib.Path(__file__).resolve().parents[1] / "evals" / "cases" / "E06" / "input.json"
        facts = json.loads(fixture.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source, handoff = root / "input.txt", root / "state.json"
            source.write_text("v1", encoding="utf-8")
            state = create(facts, [source])
            save(handoff, state, None)
            recovered = resume(handoff)
            self.assertEqual(len(recovered["facts"]), 12)
            self.assertEqual(recovered["decisions"][1]["status"], "revoked")
            with self.assertRaises(RuntimeError):
                save(handoff, recovered, 0)
            source.write_text("v2", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                resume(handoff)
            source.unlink()
            with self.assertRaisesRegex(ValueError, "missing input"):
                resume(handoff)


if __name__ == "__main__":
    unittest.main()
