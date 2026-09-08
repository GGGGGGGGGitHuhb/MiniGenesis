# V0.1/S2 Builder Work Report 001

## 1. Conclusion

- Role: Builder (Hephaestus)
- Date: 2026-09-07
- Version / Stage: V0.1 / S2 Resource World and Lifecycle
- Report status: Final
- Workflow: Ready for Review
- Branch: `codex/v0.1-s2`, base `df98562`
- Result: Approved S2 implementation and Builder validation complete. Final full suite: **190 passed in 55.62s**. Separate slow suite: **2 passed, 188 deselected in 15.96s**. No known outstanding product requirement or proposed debt.
- Acceptance boundary: This is Builder evidence, not independent Reviewer acceptance. V0.1 remains In Progress. No commit or push was performed by Builder.

## 2. Authority, inputs and route

Approved authority, unchanged by Builder:

| Document | SHA-256 |
|---|---|
| `docs/leader/designs/V0.1/S2-design.md` | `66f25751ac6cf8ff1d281ab361ba309adff941f50179087c802d6437855c0af2` |
| `docs/reviewer/reviews/V0.1/S2-review.md` | `9902653533263181b1b8dd2c3bfc1cac4970ec141a69518818ee97a3e9ae79a6` |

Approval: Leader S2 report 002, recording the user's explicit approval of report 001. Reworks and debt: none. Consulted original S1 implementation/tests, S1 Builder report 001, S1 Reviewer PASS report 001, ROADMAP V0.1, S2 preparation/approval package and current worktree. Existing dirty Leader/Reviewer documents were preserved.

Read the explicitly invoked global `orchestrate-olympus-stage/SKILL.md` and configured `builder.toml`. No applicable AGENTS.md or project Builder guide exists; used `plan-project-docs/references/role-guides/builder-guide-template.md` as the disclosed fallback. No project permission or role document was invented.

Execution is already inside WSL2 Linux, native repository and writable root `/mnt/e/01_Projects/VSCode/MiniGenesis`. Builder venv/temp/cache live under `build/s2-execution/builder`. No Windows/UNC route or system package installation was used. Commands required per-command escalation because the ordinary command launcher reported ENOENT; no broad interpreter/shell grant was requested.

Actual validation environment: Linux 6.6.87.2-microsoft-standard-WSL2 x86_64 / glibc 2.39, Python **3.12.3**, pip **26.2.1**, PyYAML **6.0.3**, pytest **9.1.1**, pluggy **1.6.0**. Editable `minigenesis 0.1.0.dev0` resolves to this checkout's `src/minigenesis/__init__.py`. Build dependencies were installed in pip isolation. This is current WSL evidence; Windows/Python 3.13.9 results are historical S1 evidence only.

## 3. Implementation and milestones

| Milestone | Actual result |
|---|---|
| M1 | Frozen WorldConfig/AgentConfig, exact paired schema, all bounds/work budget, strict types and direct S2 construction; original 60 tests plus first S2 config matrix: 145 passed. |
| M2 | Agent IDs and baseline intents; World-only settlement; integer ledger; sorted then shuffled live schedule; explicit eight-phase pipeline; 24 focused lifecycle/action/fault tests passed. |
| M3 | Deeply immutable latest successful snapshot; exact v2 projection/digest and v1 compatibility; same-seed trajectories, container order, different-seed competition, mixed A-B-A, failure latch; M2+M3: 30 passed. |
| M4 | Example/README, isolated native installation, final expanded 190-test suite, separate real slow run, CLI raw bytes/errors, evidence and this report. |

While native dependencies installed, the coordinator authorized writing M2/M3 code concurrently with preparation of M1 validation. No milestone was declared passed until its actual tests passed. Final regression covers the integrated result; no behavior or acceptance criterion was reduced.

Modified existing modules: `config.py` adds immutable paired S2 config and validation while preserving three-argument S1 calls; `rng.py` adds run-local shuffle; `simulation.py` orchestrates phases and latches failure; `summary.py` projects read-only state and v2 output while preserving v1; `cli.py` adds S2 text and retains exit contracts. Added `actions.py`, `agent.py`, `scheduler.py`, `ledger.py`, `world.py` according to approved responsibility boundaries. `pyproject.toml` only adds the slow marker; no runtime dependencies added. Added the exact approved S2 YAML example, four S2 test modules, this report, breakdown and raw evidence. README states implementation awaiting independent review.

World pays HARVEST cost before transfer, including zero-resource/zero-harvest applied actions. Insufficient energy refuses without transfer and still reaches metabolism. All intents observe one post-inflow resource amount; later HARVEST stays HARVEST after competition exhausts resource. Death is deferred until all metabolism/aging ends, settles once, returns remaining energy, and excludes dead IDs from later schedules. Empty populations keep injecting and advancing ticks. Snapshot publication and tick increment occur only after verification and projection succeed; failure forbids step/run and successful summary.

## 4. Configuration and output evidence

Run configuration: `examples/v0.1/s2-resource-world.yaml`, exactly the approved 30-tick example. `world` input fields are 0..1000000; Agent count/energy/age bounds are 1..1000, 1..1000000 and 1..100000; tick bound 1..100000 and work product <=1000000. Count/energy cumulative ledger values are not truncated to input limits.

Raw exact JSON is in `docs/builder/evidence/V0.1/S2/s2-resource-world-a.stdout` and `-b.stdout`; stderr files are empty. Final state:

- tick 30; resource 310; living 0; dead 3; living energy 0;
- each ID 0,1,2 has energy 0, age 20, alive false;
- ledger: initial resource 100 + initial Agent energy 30 + inflow 300 = world resource 310 + living energy 0 + dissipated 120.

| Contract | stdout file SHA-256 (includes LF) | Summary digest (excludes digest field and LF) |
|---|---|---|
| S1 v1 example | `4de55827ebbd9719a6bc42d8f426cf72307a0172603c3ba0090c2bbe166f6b34` | `93deab1c067673d192661637a2938bd919c768a8392d69d3513cf32fa10f12cb` |
| S2 v2 example | `e09a9aeb8e105b75efac9086d5b60717cc3c605078108c17f193e323724adb9e` | `da4da75ccc16e0b1d50bbc641ceedcfab4fe9ed00c06feae46e4b0b977992fc4` |

Both examples ran twice as real CLI subprocesses, compared byte-for-byte, and had digest independently recomputed using stdlib json/hashlib. S1 exact historical stdout hash is retained in an additional regression test. S2 field-order test constructs its expected nested object from hand values and compares the complete serialized bytes, not only dictionary equality. Changing harvest_amount with an identical final state still changes digest through complete config inclusion.

Competition trace (`competition-trajectories.json`) records each tick state and schedule for seed 1, seed 7, seed 1. Orders for seed 1: `[1,2,0], [2,0,1], [0,2,1], [0,2,1]`; seed 7: `[2,0,1], [2,0,1], [1,2,0], [2,0,1]`. First and third full traces match. Tests additionally compare mixed S1/S2 A-B-A, module RNG state, reversed World container order and zero/one-Agent RNG non-consumption.

## 5. Independently expected small ledger cases

Tests use direct expected numeric tuples, plus an independent equality derived from the returned per-Agent energies. Each row below is `(world resource, Agent energy, age, cumulative dissipated, alive)`; inflow is zero in these cases.

| Case / input | tick 0 | tick 1 | tick 2 |
|---|---|---|---|
| Normal: resource10, energy10, harvest4, action1, metabolism1 | (10,10,0,0,T) | (6,12,1,2,T) | (2,14,2,4,T) |
| Scarce: resource2, energy10, other values same | (2,10,0,0,T) | (0,10,1,2,T) | (0,9,2,3,T) |
| Metabolic death: resource0, energy1 | (0,1,0,0,T) | (0,0,1,1,F) | (0,0,1,1,F) |
| Age death: resource0, energy5, max_age1 | (0,5,0,0,T) | (4,0,1,1,F) | (4,0,1,1,F) |
| Simultaneous death: resource0, energy1, max_age1 | (0,1,0,0,T) | (0,0,1,1,F) | (0,0,1,1,F) |

Additional action tests cover zero/scarce/exact/abundant resource, zero harvest, WAIT, insufficient cost, exactly affordable cost with temporary zero energy, unknown ID/action and dead Agent, no mutation on refusal, repeated death settlement and frozen dead age. An instrumented two-Agent test checks all intents precede all transfers, both see injected resource 1, and the second action pays cost despite harvesting zero.

Fault evidence: unit tests corrupt initial_resource after tick 1, assert tick stays 1 and previous immutable snapshot identity stays unchanged, then assert step/run/summary reject. Projection failure and internal illegal action also latch failure. A real CLI subprocess corrupts resource at tick 1: exit **1**, stdout **0 bytes**, stderr includes all ledger terms and `left=140, right=141`, with no correction. Raw `ledger-fault.stderr` and harness command are retained.

## 6. Long-run dynamic and memory evidence

Both real 100000-tick scenes ran in the complete suite and again with `-m slow`. No mocked main loop or saved long trajectory. Every initial/completed state is checked against independently summed live energies. Instrumentation wraps real World methods and counts results and actual metabolism energy changes.

| Scene | Separate slow elapsed | Applied actions / harvested units | Metabolism calls / units | Final resource / dissipated |
|---|---|---|---|---|
| Approved example, ticks=100000 | 6.216957738 s | 60 / 240 | 60 / 60 | 1000010 / 120 |
| Approved long-lived single Agent | 7.218056423 s | 100000 / 100000 | 100000 / 100000 | 10 / 100000 |

The example agents die at tick 20 and subsequent ticks continue inflow. The long-lived Agent has energy 10 through tick 99999, performs one real harvest and metabolism every tick, and dies at age 100000 with all 10 remaining energy returned. Final summary digests are respectively `31a67eac9ecede61c4a11f6260a34164842158089094f21c3bc4f4eba949b95e` and `7aa4c123f7d577242deb85a9fd10b3254629e91b7263d3a2cc61b2f87da22e86`.

| Scene | tick checkpoints | Retained modeled state bytes | tracemalloc current bytes (separate slow run) |
|---|---|---|---|
| Example | 1000 / 10000 / 100000 | 5040 / 5040 / 5040 | 640 / 46190 / 46590 |
| Live | 1000 / 10000 / 100000 | 4635 / 4635 / 4635 | 704 / 1136 / 1536 |

Agent container and latest snapshot each retain exactly 3 or 1 entries. Retained-size traversal covers product slots/mappings/sequences; opaque random.Random internal storage is fixed and is not an exhaustive process RSS measurement. tracemalloc includes test/pytest activity; example's one-time ~45 KiB rise is not product history, with only 400 B further rise between 10k and 100k. The harness retains only counters and three observations; the product retains no event/trajectory list. No cross-platform or benchmark speed promise is made.

## 7. Commands, exits and raw evidence

All commands below run at the native repository root with:

```sh
export TMPDIR="$PWD/build/s2-execution/builder/tmp"
export TEMP="$TMPDIR" TMP="$TMPDIR"
export PIP_CACHE_DIR="$PWD/build/s2-execution/builder/cache"
export PYTHONPYCACHEPREFIX="$PWD/build/s2-execution/builder/cache/pycache"
```

`PY` in the table abbreviates the actual executable `build/s2-execution/builder/venv/bin/python`; it is not a hidden alternate interpreter. Each pytest command also supplied its own `--basetemp=build/s2-execution/builder/tmp/<name>` and `-o cache_dir=build/s2-execution/builder/cache/pytest`. Full exact final commands:

```sh
build/s2-execution/builder/venv/bin/python -m pytest --capture=sys -rP --basetemp=build/s2-execution/builder/tmp/pytest-full-final -o cache_dir=build/s2-execution/builder/cache/pytest
build/s2-execution/builder/venv/bin/python -m pytest --capture=sys -rP -m slow --basetemp=build/s2-execution/builder/tmp/pytest-slow-final -o cache_dir=build/s2-execution/builder/cache/pytest
build/s2-execution/builder/venv/bin/python docs/builder/evidence/V0.1/S2/validate.py
```

Evidence root: `docs/builder/evidence/V0.1/S2/`.

| Actual command / operation | Exit | Result / evidence |
|---|---|---|
| `/usr/bin/python3.12 -m venv build/s2-execution/builder/venv` | 1 | ensurepip absent; partial isolated venv created, no system modification. Tool output retained in session and environment-issues.txt. |
| `curl --fail --location https://bootstrap.pypa.io/get-pip.py --output build/s2-execution/builder/get-pip.py` | 0 | Official PyPA bootstrap downloaded to workspace only. |
| `PY build/s2-execution/builder/get-pip.py` | 0 | `bootstrap.log`; pip installed only in venv. |
| `PY -m pip install -e '.[dev]'` | 0 | `install.log`; fresh native isolated installation resolves current checkout. |
| Early pytest before install completed | 1 | Missing pytest; `m1-s1-regression.log`, not a product failure or passing run. |
| Initial pytest default fd capture | 1 | `m1-final.log`, `m2.log`: anonymous temporary-file truncate FileNotFoundError on mounted workspace, no tests collected. |
| `PY -m pytest --capture=sys tests/test_config.py tests/test_simulation.py tests/test_summary.py tests/test_cli.py tests/test_determinism.py tests/test_s2_config.py ...` | 0 | `m1-sys.log`: 145 passed / 40.14s, including original 60. |
| `PY -m pytest --capture=sys tests/test_lifecycle.py tests/test_world_determinism.py ...` | 0 | `m23-sys.log`: 30 passed / 2.87s. |
| First full `PY -m pytest --capture=sys -rP ...` | 0 | `full-001.log`: 177 passed / 57.47s, both slow scenes. |
| Final full command above | 0 | `full-final.log`: 190 passed / 55.62s. |
| Separate slow command above | 0 | `slow-final.log`: 2 passed / 188 deselected / 15.96s. |
| Evidence harness above | 0 | `cli-validation.log`: v1/v2 CLI repeats each exit 0; text exit 0; expected fault child exit 1; complete independent assertions pass. |
| `git diff --check`; original five S1 test file diff | 0 | No whitespace errors; no S1 test edits. Scope search only matched English word mutation in a scheduler docstring, no excluded capability. |

Known route correction for Reviewer: use **`--capture=sys`** on all pytest commands in this mounted WSL workspace, with role-local temp/cache. Default fd capture uses an anonymous/unlinked tempfile whose truncate failed on this route. The original failure logs are retained. This changes pytest output capture only, not test selection/assertions, and is not a waived acceptance item.

## 8. REQ / AC / RV traceability

| Requirement | Tests and executed evidence | AC / RV |
|---|---|---|
| REQ-01 | `test_s2_config.py` every numeric min/max/outside/type, strict sections, direct object pairing/validation, exact budget and allocation-before-failure; original config/CLI safety tests; full-final | AC-01/06; RV-01/07/09 |
| REQ-02 | `test_lifecycle.py` hand tables, repeat settlement, frozen dead age; `test_world_determinism.py` stable IDs and dead scheduling; full-final | AC-01/04; RV-02/05 |
| REQ-03 | lifecycle instrumented phase order; scheduler container/seed/0-1 RNG tests; both stability scenes with actual counters; trajectory JSON | AC-01/03/06; RV-02/06/07 |
| REQ-04 | lifecycle harvest parameterization, WAIT/insufficient, no mutation for invalid/dead, paid-zero boundary, exhausted competition; m23/full-final | AC-01/02; RV-03/04 |
| REQ-05 | five hand-calculated lifecycle tables, once-only death/frozen age, returned energy; every-tick slow assertions | AC-01/02/04; RV-04/05 |
| REQ-06 | independent_balance in small/long cases, corrupt-ledger failure latch, actual CLI fault error accounts; ledger-fault.stderr | AC-02/06; RV-04/07 |
| REQ-07 | exact independently constructed v2 bytes, historical exact v1 hash, nested immutable snapshots, same-seed/mixed A-B-A, full CLI byte comparisons and digest recompute | AC-03/06; RV-06/07/09 |
| Scope | Code/dependency inspection, original S1 host-capability test plus S2 guarded host-capability test, no new runtime dependencies; README pending-review boundary | AC-05; RV-08/09 |

## 9. Incomplete work, risks and Reviewer handoff

Builder work remaining: none known. Independent Reviewer acceptance and Leader closeout remain mandatory. No debt disposition is requested. Approved Design/Review/ROADMAP and Leader/Reviewer reports were not changed by Builder. README and breakdown reflect Builder completion only.

Implementation matches approved interfaces, tick order, costs, ledger identity, schema/field order and scope. Internal type names, mapping organization and duplicate read-only verification are implementation details. Current Windows and Python 3.11/3.13+ execution were not run; actual WSL 3.12 evidence is reported honestly, as authorized by Leader report 002. Memory observations prove bounded retained product containers on required scenes, not arbitrary platform memory bounds.

Reviewer should create a separate native environment, inherit the known `--capture=sys` route, inspect the real phase ordering/immutable publication, independently hand-calculate balances and digest, rerun full and separate slow suites and actual CLI fault behavior, and verify the live scene's 100000 calls. Evidence includes `validate.py` to reproduce CLI checks; acceptance must not merely repeat this report.
