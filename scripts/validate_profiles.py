#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.packs.loader import load_profiles

profiles = load_profiles(ROOT)
for p in profiles:
    for obs in p.observation_types:
        if "." not in obs:
            raise SystemExit(f"Invalid observation type: {obs}")
print(f"OK profiles={len(profiles)}")
