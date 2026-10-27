# E346 | Gaussian Monte Carlo overflow hidden by a constant callback

**28 October 2026.** Educational numerical-integrity research, not an operational trajectory or weapon-performance study.

## Falsifiable failure mode

The original `stats_monte_carlo_normal` validated finite input parameters and finite *transformed outputs*, but never validated the **generated Gaussian sample** before passing it to a user-supplied transform. A transform that ignores its input (or clamps infinity) can turn an invalid draw into a finite value, causing a success receipt for a simulation with nonfinite intermediate data.

The fixed xorshift64* seed 7 gives a positive first Box–Muller normal deviate (approximately +0.5666978 on the reference IEEE binary64 implementation). For `input_mean=DBL_MAX` and `input_stddev=DBL_MAX`, the first sample overflows. A callback that always returns 1.0 previously hid the invalid draw.

## Changes and controls

- `stats_rng_normal` now returns NaN instead of infinity for an unrepresentable finite-parameter result.
- `stats_monte_carlo_normal` rejects nonfinite draws **before** calling the transform, independently of whether the callback masks them.
- `stats_summary` rejects a sample-count multiplication overflow before allocation.
- The statistics translation unit rejects compiler flags that invalidate its `isfinite` assumptions, matching the physics module's existing finite-math contract.
- Regression: seed-7 overflow with a constant callback must fail. Valid zero-noise constant output must still succeed and have zero variance.

## Claim boundary

The test checks **software numerical integrity under deterministic synthetic extreme inputs**. It does not validate a physical model, empirical uncertainty distribution, compiler ABI portability, or real-world ballistic performance. A finite Gaussian result can still be a poor physical model.

## Validation

Run `make test`, `python tools/e308_finite_math_contract.py` and the existing C CI on the exact E346 branch. Do not promote the claim until the exact-head workflow passes.

**Next:** test numerical overflow and callback isolation on independently selected toolchains, then focus on independently sourced measurement error models rather than additional generic scaffolding.
