# E391 — ULP-neighbour terminal-event stress (2026-10-29)

## Falsifiable question

Does the E365 exact-zero-height endpoint correction preserve successful termination
when a constant-acceleration integration step is one IEEE-754 binary64
representable value below, at, or above a nominal boundary?

This is a **synthetic classroom numerical-integrity** experiment. No weapon
parameters, targeting, firing solutions, drag optimization, field measurements,
or empirical performance claims.

## Frozen protocol

- Code base: E365 draft PR #20, head `74cc3ddf8e54a5860906c241fa745688c5f982bf`.
- New deterministic C test: `tests/test_e391_ulp_boundary.c`, wired into `make test`.
- Speeds: 1, 10, 100 (synthetic model units); angles: 15, 45, 75 degrees.
- Step ratios: 0.5, 1.0, 2.0 times analytical flight duration.
- ULP neighbours: `nextafter(nominal, 0)`, nominal, `nextafter(nominal, +inf)`.
- 3 x 3 x 3 x 3 = **81** fixtures, no random tuning or hidden data.
- On successful outputs: require strict timestamp monotonicity, finite states,
  one zero-height terminal sample, agreement with the independent closed-form
  model within 1e-8 scaled error.
- On rejected outputs: require empty/cleared sample ownership (fail closed).
  Bound the allowed rejection count below 10% to catch broad regressions.

## Reproduced falsification and measured result

The original success-for-every-ULP-neighbour assertion failed on the
**100 / 15-degree / half-flight / one-ULP-below** fixture:
[E391 expected-red CI #40873688028](https://github.com/stoicsatvik/BallisticsLab/actions/runs/40873688028).
The assertion was corrected to preserve this as an explicit rejected case,
rather than silently treating it as a successful numerical trajectory.

[Exact-head CI #40873788048](https://github.com/stoicsatvik/BallisticsLab/actions/runs/40873788048)
on `8f0229865f121a6111a7489be36de3f41bfd4ad6` passed with:

- 81 total ULP-neighbour fixtures;
- **80 accepted, 1 rejected** with samples cleared;
- maximum accepted scaled time error: **1.8034624735141129e-16**;
- maximum accepted scaled horizontal-coordinate error: **2.2297740542853715e-16**;
- maximum accepted scaled apex error: **1.8670817410926112e-16**.

The inherited E274 150-case invariant test also passed in this workflow.
These are deterministic GCC/Ubuntu CI measurements, not general ABI claims.

## Discriminating mechanism hypothesis

An independent binary64 arithmetic reproduction of the rejected fixture gives
a positive near-zero height after two half-flight steps and a subsequent
positive event offset of approximately 2.75e-16 seconds, smaller than the
representable spacing at the current timestamp. The addition `t + tau`
rounds back to `t`, violating the solver's strict `impact_t > t` guard.

**This is a plausible mechanism, not an instrumented proof of which C guard
fired.** The safe current behavior is to reject the unrepresentable event and
free partial samples. Returning a fabricated later timestamp would require an
explicit numerical-resolution policy, not a silent patch.

## Claims and next experiment

- All-neighbour acceptance: **REJECTED** for the tested GCC binary64 cohort.
- 80 accepted fixtures with bounded errors and monotonic states: **SUPPORTED
  IN TESTED SYNTHETIC SOFTWARE**.
- One fail-closed precision-boundary rejection: **OBSERVED**.
- Cross-compiler/ABI invariance, real physical prediction, and general
  numerical correctness: **NOT YET PROVEN**.

Next: instrument the exact failing guard without changing production semantics,
repeat with GCC/Clang and strict `-O0/-O2/-O3`, then compare long-double
reference events. Preserve negative results. Do not loosen fail-closed guards
solely to make a test green.

No main merge, deployment, spending, outreach or physical experimentation.
