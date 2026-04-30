import unittest
from pathlib import Path
from scripts.packs.loader import load_profiles, get_profile

ROOT = Path(__file__).resolve().parent.parent

class TestProfileValidator(unittest.TestCase):
    def test_load_profiles(self):
        profiles = load_profiles(ROOT)
        self.assertGreaterEqual(len(profiles), 3)

    def test_get_email(self):
        p = get_profile(ROOT, 'email-analysis')
        self.assertEqual(p.profile_id, 'email-analysis')
