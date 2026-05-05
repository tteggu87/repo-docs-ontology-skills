# Roadmap

Updated: 2026-05-05

## Near-term

- keep `docs/` aligned whenever CLI surfaces, workbench routes, or truth boundaries change
- make closed ingest reporting routine enough that operators can see registered, updated, skipped, not-applicable, and pending artifacts after each source-processing pass
- extend source-family coverage only through explicit manifest mappings plus tested parser support
- continue using the workbench as a bounded operator surface rather than a browser-owned authoring system

## Next useful additions

- add more intelligence artifacts only where they reduce confusion:
  - route-level entities if the workbench surface grows materially
  - handler docs if cross-surface workflows become harder to follow
  - schema excerpts if canonical DuckDB or graph materialization contracts become operator-facing
- add a lightweight validator script if doc/intelligence drift becomes frequent enough to justify automation

## Known gaps

- there is no repo-local validator yet for `docs/` plus `intelligence/` alignment
- the closed ingest contract is documented, but there is not yet a dedicated `pipeline-check` command for producing the completion report automatically
- only `docs/CURRENT_STATE.md` existed before this refresh, so the portal is still young
- the incremental ingest path is intentionally narrow and not yet a generic multi-family ingest framework
- the workbench route set is documented, but the frontend remains optional and sidecar-only
