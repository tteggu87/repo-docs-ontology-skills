import json
import tempfile
import unittest
from pathlib import Path
from scripts.ingest.adapters.common import stable_unit_id

class TestRegistryHelper(unittest.TestCase):
    def test_stable_unit_id(self):
        a = stable_unit_id('doc1','paragraph',1,'hello')
        b = stable_unit_id('doc1','paragraph',1,'hello')
        self.assertEqual(a,b)
