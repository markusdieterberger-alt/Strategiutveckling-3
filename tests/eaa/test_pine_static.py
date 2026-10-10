from pathlib import Path
import unittest

from eaa.audit import source_audit


class PineStaticTests(unittest.TestCase):
    def test_source_invariants_not_compilation(self):
        result = source_audit(Path(__file__).resolve().parents[2])
        self.assertTrue(all(result["checks"].values()))
        self.assertFalse(result["pine_compiled"])


if __name__ == "__main__":
    unittest.main()
