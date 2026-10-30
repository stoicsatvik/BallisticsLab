# E409 — Sub-ULP terminal-event guard discrimination (2026-10-30)

## Question and frozen case

E391 observed one fail-closed result in 81 synthetic IEEE-754 binary64 ULP-neighbour fixtures. Is the failure due to an unrepresentable *positive* terminal-event offset, rather than an invalid root, overflow, or an earlier non-progressing integration step?

- Frozen base: E391 draft PR #21, head `41b643430d388a4439056cbd783afd16635646a6`.
- Generic synthetic input: speed=100, angle=15 degrees, step=`nextafter(0.5 * analytic_flight_time, 0)`.
- Production `src/physics.c` is unchanged. The test calls the real `bl_simulate_vacuum` and mirrors its arithmetic step-by-step, asserting all earlier guards are satisfied and the final strict timestamp guard is not.
- Test `tests/test_e409_ulp_guard.c` runs in `make test`. A separate workflow compiles it with GCC and Clang, each at O0/O2/O3.
- No field data, firearm-specific inputs, targeting, optimization, or physical calibration.

## Measured results

The original solver returns -1 with `samples == NULL` and `count == 0`. The mirrored first two steps are finite, monotone and nonterminal; the third step crosses below zero. The root and its interval bounds are finite/valid. The final `impact_t = t + tau` equals `t` in binary64, which violates the production strict `impact_t > t` guard.

| Diagnostic | Observed |
|---|---:|
| Positive terminal offset `tau` | 2.7453263166110802e-16 |
| Binary64 spacing at `t` | 8.8817841970012523e-16 |
| `tau / ulp(t)` | 0.30909626441250193 |
| Binary64 `impact_t == t` | true |
| Long-double `(t + tau) - t` | 2.74519990073329722691e-16 |
| GCC/Clang x O0/O2/O3 | 6/6 same diagnostic |

Local independent C arithmetic reproduction matched the remote numerical values. On GitHub's Linux x86_64 runner, [E409 exact-head cross-compiler CI #40991826690](https://github.com/stoicsatvik/BallisticsLab/actions/runs/40991826690) and [standard C CI #40991826688](https://github.com/stoicsatvik/BallisticsLab/actions/runs/40991826688) both **SUCCESS** at `2c37328641055ab99711ab20e2a2bec1aca37d5a`. The cross-compiler job log contains all six matching values. The full inherited `make test` suite and E308 finite-math checks also passed.

## Interpretation

**SUPPORTED IN TESTED SOFTWARE:** The E391 rejected case is consistent with, and isolated by an operation-by-operation mirror to, the strict binary64 `impact_t > t` guard. The terminal offset is positive but less than half the local ULP. Its loss at binary64 precision is expected rounding, not a negative physical flight duration. A wider local long-double representation can distinguish the offset.

**REJECTED:** The hypothesis that this fixture's rejection is caused by a nonfinite root or a failed earlier step-progress guard.

**NOT YET PROVEN:** All compiler/ABI/architecture generalization; that changing the production event representation improves numerical correctness; any empirical physical accuracy.

The test mirrors the C operations but does not attach a runtime trace to the exact internal production branch. It verifies every preceding predicate and the sole final failing predicate, so the guard identification is strongly supported but not an instrumented proof of control flow.

## Next decisive experiment

Try an isolated *alternative event representation* (e.g. separate step-local offset and global timestamp) against a high-precision oracle on unseen finite cases, measuring how often each approach either fabricates progress or rejects an unrepresentable event. Preserve the existing fail-closed production behavior until a new policy is justified. Test independent ABIs/architectures where legitimately available.

No main merge, deployment, spending, outreach, or real-world firing calculations.
