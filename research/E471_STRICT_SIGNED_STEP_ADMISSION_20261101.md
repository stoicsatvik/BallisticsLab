# E471 | Fail-closed signed-step admission for generic two-component timestamps

Date: 2026-11-01. **Numerical software only**; no trajectory integration, targeting, physical timing calibration, or production deployment.

## Hypothesis and counterexample

E466 showed that a normalized two-component timestamp `(2^53, 1)` plus a positive increment `2^-54` can return the unchanged representation. A caller that assumes every positive addition advances time would silently violate its own strict-order contract. The same problem occurs for sufficiently small negative increments.

**Falsifiable contract:** `bl_time2_add_strict(a, delta, out)` returns success only when the represented result moves in the sign of the *normalized, nonzero* delta, or stays unchanged for a zero delta. It normalizes both caller inputs, uses the existing arithmetic, checks the represented order, and commits to `*out` only on success. Failure leaves `*out` untouched. The existing `bl_time2_add` API remains unchanged for compatibility.

This is an **admission guard**, not arbitrary exact rational addition, an automatic high-precision fallback, or a promise of physical time resolution. A caller must handle failure explicitly and choose an application-specific resolution/fallback policy. The numerical library does not invent a minimum tick size.

## Reproducible offline checks

The starting `src/time2.c` and `src/time2.h` matched exact E465 GitHub blobs `cf10303c9cfeebf4043452d47825c4c7f6f6148f` and `8825e0bd3cc59cc577d8a0767eb95c476c202494` before the changes.

- GCC 14.2 and Clang 17: new C strict-admission tests **PASS** with `-std=c11 -O2 -Wall -Wextra -Werror -pedantic -fno-fast-math`; original E465 C tests **PASS** with both compilers.
- Signed sub-resolution counterexamples: both positive `2^-54` and negative `-2^-54` at `(2^53,1)` are **rejected without modifying the output**. The legacy unchecked API still stalls, as expected. Representable ±1 and zero deltas pass.
- Frozen seed 1471 signed/mixed-scale cohort: **16,384/16,384** additions admitted, **0 wrong-direction admissions**, **0 failure-output mutations**, but **8,598 admitted results differ from the exact rational oracle**. Thus the guard does **not** guarantee exactness.
- Frozen resolution-boundary grid: 26 exponents × 2 signs × 16 repeats = **832** cases. **272 admitted**, **560 rejected** with output preservation. These are deliberately adversarial synthetic inputs, not operational failure frequencies.
- GCC and Clang produced identical counts in the two frozen cohorts.

The signed cohort can contain exactness failures even though all additions advance in the correct direction. This negative result is preserved explicitly to prevent conflating *direction* with *magnitude accuracy*.

## Validation and limitations

The new `research/e471_signed_step_oracle.py` reproduces both frozen cohorts and checks the directional/atomic-output invariants. `tests/test_time2_strict.c` covers deterministic counterexamples, normalization, overflow, nonfinite inputs and the unchanged legacy API. No GitHub Actions job was initiated; exact-head CI, full repository suite, architecture/rounding-mode portability, concurrency, runtime overhead and production integration remain unverified.

**Next discriminating gate:** Compare a fixed-scale integer-tick representation with two-component floating point under identical horizon, minimum-step, overflow and serialization constraints. Report loss of range and quantization error rather than declaring a universal winner. Keep this branch draft and stacked on E465 PR #25.
