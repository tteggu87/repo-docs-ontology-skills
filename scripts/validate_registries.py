#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def load(name):
    p=ROOT/f'warehouse/jsonl/{name}.jsonl'
    if not p.exists(): return []
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]

docs={x['document_id'] for x in load('documents') if 'document_id' in x}
units=load('content_units')
unit_ids=set()
for u in units:
    uid=u['unit_id']
    if uid in unit_ids: raise SystemExit('duplicate unit_id')
    unit_ids.add(uid)
    if u.get('document_id') not in docs: raise SystemExit('unresolved document_id')
obs=load('observations'); obs_ids=set()
for o in obs:
    oid=o['observation_id']
    if oid in obs_ids: raise SystemExit('duplicate observation_id')
    obs_ids.add(oid)
    if o.get('unit_id') and o['unit_id'] not in unit_ids: raise SystemExit('unresolved observation.unit_id')
print('OK registries')
