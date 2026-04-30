# Built-in Profile Promotion Path

DocTology should keep `email-analysis`, `education-analysis`, and `report-consistency-analysis` as built-in profiles until external reuse creates real pressure.

## Promote to ontology pack v1 only when

- the same profile is reused across multiple repositories
- version compatibility and migrations are required
- external install/update lifecycle is needed
- validator coverage is stable enough to protect consumers
- third-party execution security has an approved model

## Built-in profile vs external pack

- Built-in profile: repo-local, deterministic, simple to debug, no dynamic code loading.
- External pack: versioned distribution surface with lifecycle, compatibility, and security obligations.

Default decision: stay built-in for the personal MVP.
