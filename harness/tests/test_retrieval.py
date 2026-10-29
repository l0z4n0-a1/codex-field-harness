import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from retrieval import find, read_lines


class RetrievalTests(unittest.TestCase):
    def test_error_after_initial_limit_recovered(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "log.txt"
            path.write_text("\n".join([f"ERROR routine {i}" for i in range(8)] + ["ERROR critical late failure"]), encoding="utf-8")
            first = find([path], "ERROR")
            self.assertTrue(first["truncated"])
            self.assertEqual(first["total_hits"], 9)
            self.assertTrue(any("critical late" in x["excerpt"] for x in find([path], "ERROR", expand=True)["hits"]))

    def test_expansion_recovers_long_line_and_missing_source_is_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "log.txt"
            missing = pathlib.Path(temp) / "missing.txt"
            path.write_text("ERROR " + "x" * 300 + " critical tail", encoding="utf-8")
            first = find([path, missing], "ERROR")
            self.assertFalse(first["truncated"])
            self.assertTrue(first["hits"][0]["line_truncated"])
            self.assertEqual(first["missing_paths"], [str(missing)])
            self.assertIsNotNone(first["expand_command"])
            expanded = find([path, missing], "ERROR", expand=True)
            self.assertIn("critical tail", expanded["hits"][0]["excerpt"])
            self.assertFalse(expanded["hits"][0]["line_truncated"])
            with self.assertRaises(ValueError):
                find([path], "ERROR", limit=0)

    def test_exact_line_range_recovers_context_without_other_hits(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "log.txt"
            path.write_text("INFO start\nERROR first\nDETAIL cause\nERROR later\n", encoding="utf-8")
            section = read_lines(path, 2, 3)
            self.assertEqual([row["text"] for row in section["lines"]], ["ERROR first", "DETAIL cause"])
            self.assertTrue(section["complete_range"])
            self.assertFalse(read_lines(path, 4, 5)["complete_range"])
            with self.assertRaises(ValueError):
                read_lines(path, 0, 1)
            with self.assertRaises(FileNotFoundError):
                read_lines(path.with_name("absent.txt"), 1, 1)


if __name__ == "__main__":
    unittest.main()
