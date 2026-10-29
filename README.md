# codex-field-harness

**I make my Codex setup fail before I trust it.**

This repository is the evaluation harness I use on my own Codex CLI setup. It holds frozen test cases, deterministic gates, negative controls, run receipts, and a promotion rule: no model route, profile, or instruction change gets promoted without evidence.

It started with a simple problem. I had 1,000+ Codex sessions, 7 role profiles, plugins, skills and AGENTS.md files spread across dozens of repositories, and no honest answer to *"is this setup actually better, or does it just feel better?"*

> Português: [README.pt-BR.md](README.pt-BR.md) · Workshop kit: [workshop/](workshop/)

---

## What's inside

| Piece | What it does | Where |
|---|---|---|
| **8 frozen eval cases (E01–E08)** | Fixed inputs with SHA-256 hashes. The executor sees only the case and the oracle stays hidden. | `harness/evals/` |
| **Deterministic gates** | E01, E02, E05, E06 and E07 are checked by code, not by a model | `harness/evals/static_gate.py`, `check_cases.py` |
| **Negative controls** | Deliberately broken outputs that the gates *must* reject. A gate that can't fail isn't a gate. | `harness/tests/` |
| **Typed routing** | Every model route records surface, CLI version, model, effort, status and escalation trigger | `harness/routing.json`, `routing.py` |
| **Run receipts** | Token usage and terminal events captured per run, with truncated or impossible counts rejected | `harness/collect_usage.py`, `evidence/runs.jsonl` |
| **Permission matrix** | Read-only vs workspace-write profiles, plus what a profile does *not* prove | `harness/permission-matrix.md` |
| **Handoff + state** | Objective, active vs revoked decisions, evidence and next step, kept across sessions | `harness/handoff.py`, `templates/state.md` |
| **Worktree inventory** | Parallel agents in isolated git worktrees, registered and preserved | `harness/worktree_inventory.py` |
| **Release receipts** | 7 candidate releases with hashes and a rollback rehearsed on an isolated copy | `evidence/releases/` |

```bash
python -m pytest -q harness/tests
# 27 passed, 18 subtests passed
```

## The eight cases

Each case targets a failure mode I actually hit while working with coding agents:

| Case | Failure mode it catches | Gate |
|---|---|---|
| E01 | Applies a data rule (dedupe and latest-wins) wrongly on messy rows | deterministic |
| E02 | Fixes a bug but breaks the tests, or "fixes" the tests instead of the code | deterministic (unit tests) |
| E03 | **Claims to have read sources it never opened.** The brief includes a deliberately obsolete claim and an unavailable URL. | static + human review |
| E04 | A plugin prepares a response outside its declared tools | static + human review |
| E05 | Arithmetic done "in the model's head" instead of computed | deterministic |
| E06 | Loses continuity: treats a revoked decision as active after a handoff | deterministic |
| E07 | Shell argument mangling with spaces, quotes, metacharacters or backslashes | deterministic (literal argv round-trip) |
| E08 | Routes a request to the wrong skill, or outside its scope | static + human review |

## Case study: the canary that claimed five sources

This is the result that made the harness worth building.

I ran a one-call canary on **E03** (research with sources). The answer looked good. It cited five sources, it was well written, and it used **156,342 input tokens**.

The gate rejected it. The trace held no five identifiable source openings. The model *said* it had read five sources, and the observable record didn't support it.

What changed:

1. **Gate H05 was revised.** A claim of an opened source now requires an **observable receipt per URL**. Saying it isn't enough.
2. The saved canary was re-run through the stricter gate. It now **also fails structurally**, and that failure is kept as a permanent negative control.
3. The candidate release was **not promoted**. Seven routes stayed on baseline.

What I teach from this: **eloquence is not evidence.** Before a team argues about adoption, it needs a way to tell "the agent did it" from "the agent said it did it".

## Results so far

- 27 harness tests pass (18 subtests). 18 structural negative controls are detected as failures, as the changelog records. Gates E01, E02 and E05 pass.
- An E02 pair (high vs medium reasoning effort) ran. **No route was promoted.** The sample is too small to justify it.
- 7 candidate releases are recorded with hashes. Rollback was rehearsed on an isolated copy (118 change records).
- A skill probe found explicit path references for 21 of 26 skills. **That does not prove productive use**, so no skill was disabled.
- Still pending: human review for E03, E04 and E08, and a longitudinal window of 10 real tasks. **None of this is production validation**, and the harness says so in every release note.

Most routes are marked "configured, not benchmarked" because that is what they are.

## What I learned that I'd tell a Codex customer

1. **A prompt doesn't grant or remove permission.** Profiles and sandbox do. A test that parses a profile doesn't prove the OS sandbox blocked a command. Test the block itself.
2. **Start from a baseline you can roll back to.** Snapshot config, profiles and AGENTS.md before changing anything. My first release candidates failed, and the baseline is why that was cheap.
3. **Deterministic first.** If the answer is countable, count it with code and let the model judge only what needs judgment.
4. **Keep the global AGENTS.md short.** Mine is a handful of lines: cost-aware, minimal context, verify before integrating. Project-specific rules belong in the project.
5. **Use three states: configured, benchmarked, promoted.** Most of my routes are still in the first.

## Product notes I collected along the way

Things I'd want as a Codex power user, written as field feedback:

- **Observable source access in traces.** E03 exists because I couldn't verify "I read these sources" from the CLI trace alone.
- **Machine-readable remaining quota.** No CLI I use exposes it, so routing by budget means guessing.
- **Catalog visibility ≠ account entitlement.** My router only resolves `visibility=list` models. Making entitlement explicit would remove a class of silent fallbacks.
- **Service tier vs model ID.** "priority" is a service tier, never a model ID. Easy for a team to confuse in config.

## Run it on your own setup

1. `python -m pytest -q harness/tests`: the harness verifies itself first.
2. Read `harness/evals/run-plan.md`. It's frozen, and the executor only receives the case.
3. Run a case through your current setup (`codex exec -p <profile> ...`), then check it with `check_cases.py` / `static_gate.py`.
4. Change **one** thing (AGENTS.md, a profile, effort, a skill) and re-run the same case.
5. Write the receipt. Promote only if the gate says so.

The workshop kit in [`workshop/`](workshop/) turns these steps into a 60-minute hands-on session for an engineering team.

## About

I'm **João Lozano**, founder of AIdeas Lab in São Paulo. I build products with Codex and Claude Code every day, including [Sintética](https://sintetica.app), a Codex plugin and ChatGPT app built with the Apps SDK, and I teach people to do the same.

Internal notes in `harness/` are in Portuguese, the language I work in, and the changelog has an English version (`harness/CHANGELOG.en.md`). Glossary: route and profile names are Portuguese: `auditoria` = audit, `codigo` = code, `dissenso` = dissent (second opinion), `mecanico` = mechanical/bulk work. **MUSE** and **Persona Foundry** in some fixtures are my own Codex plugins (a UGC agency plugin and a persona builder), used as realistic test targets.

MIT License.
