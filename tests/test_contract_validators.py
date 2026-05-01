from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class ContractValidatorTests(unittest.TestCase):
    def run_validator(self, script: str) -> None:
        result = subprocess.run(
            [sys.executable, script],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_docs_and_intelligence_validators(self) -> None:
        self.run_validator("scripts/validate_repo_docs_intelligence.py")
        self.run_validator("scripts/validate_intelligence.py")
        self.run_validator("scripts/validate_workbench_manifest.py")
        self.run_validator("scripts/validate_profiles.py")
        self.run_validator("scripts/validate_registries.py")


if __name__ == "__main__":
    unittest.main()
