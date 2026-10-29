# Local harness — changelog (English)

> Translation of `CHANGELOG.md` (Portuguese is the original). Paths are anonymized.

## 2026-09-25 — core 1.0 candidate

- Verifiable baseline, comments fixed with no change to active values.
- Short global guidance, typed routing, receipts, eight fixtures, selective retrieval, handoff, opt-in profiles, worktree inventory, external adapter switched off.
- A microsample and one E02 pair (high vs medium effort) completed. No route promoted. Fixed plugins installed. E04/E08 validation in the app and longitudinal observation are still pending.

## 2026-09-25 — local release candidate

- 19 harness tests and the E01/E02/E05 gates passed. 17 structural negative controls for E03/E04/E08 were detected. Factual and human review still pending.
- Selective retrieval (H06) streams files, flags missing sources and expands long lines. The global default and seven routes stay on baseline.
- Recorded in `releases/20260925T1420Z-core-candidate/receipt.json`. A candidate is not production validation.
- H04 fixed so it no longer reports success on truncated JSONL, zero on a cumulative reset, or impossible sub-counts. Five saved streams were reprocessed with no divergence.
- One-call E03 canary not accepted: it claimed five opened sources, but the CLI trace held no five identifiable openings. 156,342 input tokens. The candidate failed the quality gate and was not promoted.
- Gate H05 revised: a claim of an opened source requires an observable receipt per URL. The saved E03 canary now also fails the structural gate. 20 tests and 18 negative controls passed.

## 2026-09-25 — local candidate v2

- E03 with sources attributed by the harness, E04 contract v2 and E08 fixture v1.1 passed canaries limited to text/state. The initial failures stay in the historical receipts.
- 20 tests, 18 negative controls, 11 CLI receipts and a rollback with hashes. Seven routes stay on baseline.
- Recorded in `releases/20260925T1516Z-core-candidate-v2/receipt.json`. Still pending: observation of ten real tasks or a two-week window, human review and MUSE exposure in the app. Production not validated.

## 2026-09-25 — local candidate v6 and later checks

- Candidate v6 enabled observer H15, restricted to the release. 26 tests passed. No real task recorded yet, so production validation is still pending.
- The full 115-record manifest restored 73 baseline hashes and re-applied 73 active hashes on an isolated copy. The 26 tests passed after re-applying. The app process and external plugin state were not reverted in this rehearsal.
- Four historical staged references were repaired from later backups with the same SHA-256. The manifest no longer points at the overwritten versions.
- H12 preserved the three worktrees. NEXUS references were checked: one path is missing, the other exists but has no `.codex/hooks.json`. No reference was deleted.
- A local skills probe found explicitly referenced paths for 21 of 26 skills in tool arguments. That does not prove productive use, disuse of the others, or token savings, so no skill was disabled.
- Seven routes stayed on baseline. H07/H13 were not promoted. H15 is waiting for longitudinal observation of real tasks.

## 2026-09-25 — E07: literal argv verified

- The fake provider now echoes the arguments it received. The test confirms an exact round-trip of an argument with spaces, quotes, shell metacharacters and backslashes, plus the stdin text.
- 27 harness tests passed. The manifest holds 118 change records. Rollback was rehearsed on an isolated copy. No external provider was called.

## 2026-09-25 — local candidate v7

- Recorded in `releases/20260925T1627Z-core-candidate-v7/receipt.json` after the E07 fix. The active suite passed 27 tests. Seven routes remain on baseline.
- Observer H15 is still restricted to the release with no eligible real task. The longitudinal window and the total-cost review are still pending. This candidate is not production validation.
