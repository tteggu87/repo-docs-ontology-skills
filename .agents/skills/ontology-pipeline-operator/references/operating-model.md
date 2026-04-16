# Ontology Pipeline Operator Reference

## Best Fit

Use this skill when a repo already has:

- canonical ontology or JSONL registries
- derived graph artifacts
- graph projection exports
- current-state or impact docs
- more than one script that operators are running manually

## Core Invariants

- raw source truth and exploration truth must stay distinct
- graph projection stays read-only
- reports should not regress to claim-only speaker discovery
- validators should see the final synced docs state

## Thin-Wrapper Principle

Prefer:

- one single-entry script that calls existing focused scripts
- one docs sync script
- one validator that checks both data drift and docs drift

Avoid:

- replacing the runtime with a YAML executor
- inventing a second orchestration path when one already exists
