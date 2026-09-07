# V0.1/S2 Builder implementation breakdown

Authority: Approved S2-design.md and S2-review.md; approval S2 Leader report 002.
Role: Builder (Hephaestus). No applicable rework or debt.

| Milestone | Scope / modules | Depends on | Required validation | Status |
|---|---|---|---|---|
| M1 | Paired immutable config and strict bounds, S1 compatibility | Approved baseline | Original 60 tests, S2 input matrix | Passed: 145 tests including original 60 |
| M2 | Agent/actions/world/ledger/scheduler and fixed tick pipeline | M1 pass | Hand-calculated ledger, action rejection, both deaths | Passed with M3: 30 tests |
| M3 | v2 summary, snapshots, determinism, failure state | M2 pass | Exact bytes/digest, trajectories, A-B-A, injected failure | Passed; CLI harness also passed |
| M4 | Example, README, evidence and report | M3 pass | Full and separate slow suite, two 100000-tick paths, CLI | Passed: full 190; separate slow 2; CLI harness exit 0. Ready for Review |

Route: native WSL Linux, `/mnt/e/01_Projects/VSCode/MiniGenesis`; temp/cache/venv under `build/s2-execution/builder`. The command launcher needs per-command escalation after ENOENT. No system installation changes. Python 3.12 lacks ensurepip; official PyPA bootstrap installs pip only into the workspace venv. Raw evidence is retained under `docs/builder/evidence/V0.1/S2`.
