# Built-in Analysis Profiles

These manifests declare **built-in** analysis profiles available inside this repository.

- They are not external plugins.
- Runtime discovery only scans `intelligence/packs/*/pack.yaml` under repo root.
- `status: built_in` means static repo-local capability mapping.

Required fields:
- `profile_id`
- `pack_id`
- `version`
- `status` (`built_in`)
- `source_families`
- `unit_kinds`
- `observation_types`
- `analysis_outputs`
- `capabilities.parse.python`
- `capabilities.analyze.python`
