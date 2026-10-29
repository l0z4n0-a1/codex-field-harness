# Workshop: Trust, but verify your coding agent (60 min)

> Status: designed from the harness loop, not yet run with an external team. I teach hands-on AI sessions regularly. This specific format is new.

A hands-on session for an engineering team that already uses Codex, or is about to roll it out.
By the end, each pair has measured one change to their own setup, with a receipt.

**Format:** pairs, one laptop each, Codex CLI installed, a repository of their own (or `harness/evals/cases/E02`).
**Works for:** 10 to 80 people. Above 20, add one helper per 10 pairs.

| Min | Block | What happens | Output |
|---|---|---|---|
| 0–5 | **The claim** | Live: a Codex answer that looks right. Then the trace shows it isn't (the E03 canary). | Shared vocabulary: *configured → benchmarked → promoted* |
| 5–15 | **Baseline** | Each pair snapshots config, profile and AGENTS.md, then runs E02 (or one task from their repo) once | Baseline receipt |
| 15–25 | **One change** | Each pair picks ONE change: a short AGENTS.md, a read-only profile, lower effort, or a skill | Written hypothesis: "I expect X because Y" |
| 25–40 | **Re-run + gate** | Same case, same input. The deterministic gate decides. Then a broken output is fed in on purpose to prove the gate can fail. | Receipt + negative control |
| 40–50 | **Readout** | 3 pairs present: what changed, what the gate said, promote or not | Promotion decisions |
| 50–60 | **Your rollout rule** | The team writes its own 3-line promotion rule and where receipts will live | Team adoption rule (1 page) |

## Facilitator notes
- Never let "it feels faster" end a discussion. Ask for the receipt.
- If a pair's change made things worse, celebrate it. It's the cheapest lesson of the day.
- Permissions: run the session with `harness-readonly` first. A prompt doesn't grant permission.
- Language: I run this in Portuguese or English. Slides are optional; the terminal is the slide.

## Take-home
- `harness/` as a starting point.
- The 3-line promotion rule the team wrote.
- One case adapted from their own codebase, added as E09.
