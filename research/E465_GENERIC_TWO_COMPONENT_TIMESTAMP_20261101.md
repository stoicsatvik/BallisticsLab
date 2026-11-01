# E465: Generic C two-component timestamp under sub-ULP steps

Date: 2026-11-01. Scope: **numerical representation only**, no physical projectile simulation, weapon calculations, targeting or operational application.

## Falsifiable question

Does a two-component binary64 timestamp preserve strict ordering under small positive increments that round to zero when added to a large scalar timestamp? Can this be reproduced in ordinary C and checked against an independent exact rational oracle, rather than only in E445's Python model?

## Implementation

`src/time2.c` and `src/time2.h` implement a generic C timestamp API: finite-input admission, two-sum normalization, two-component addition, and lexicographic comparison of normalized pairs. They do not modify `src/physics.c` or any trajectory interface. The intended environment is round-to-nearest binary64 without `-ffast-math`; no claim is made for altered rounding modes, flush-to-zero or arbitrary-length exact arithmetic.

## Frozen local tests

Independent `fractions.Fraction.from_float` oracle, seed 465:

- **2,048 single-step cases:** initial times 2^20 through 2^100; increments 53–100 powers of two smaller. Scalar binary64 addition stalled in **2,048/2,048**. Two-component additions retained the exact binary64-input rational sum in **2,048/2,048**, with **0** ordering failures.
- **512 sequences of 16 positive steps:** **512/512** exact final rational sums and **0/8,192** nonmonotone steps.
- **GCC and Clang:** C tests passed at `-O2 -Wall -Wextra -Werror -pedantic -fno-fast-math`. Tests include nonfinite/overflow admission, zero/negative ordering and C99 hexadecimal floating-point roundtrip.
- **Python:** three independent unittest contracts passed locally.

These are synthetic adversarial fixtures, not a prevalence estimate. The generator uses only positive powers of two. This does not prove arbitrary mixed-sign summation, pathological cancellation, compiler portability or exactness for every finite input. The generic timestamp utility is not wired into the existing simulation. No performance benchmark or real-world measurement is claimed.

## Claim state

**SUPPORTED IN FROZEN LOCAL C + EXACT-RATIONAL TESTS** for the specified positive-step cohort. Universal exact arithmetic, cross-platform behavior and physical measurement accuracy **NOT YET PROVEN**.

## Next discriminating tests

1. Freeze independent mixed-sign/non-power-of-two families with exact rational oracle, near-overflow and subnormal boundary controls.
2. Test C compiler, architecture and floating-point environment sensitivity.
3. Benchmark storage/serialization overhead against simple integer ticks.
4. Keep the utility generic and non-operational; no weapon-specific integration.


## E466 independent negative-result audit (2026-11-01)

A separate local test used the **exact GitHub C source blob** `cf10303c9cfeebf4043452d47825c4c7f6f6148f` and header blob `8825e0bd3cc59cc577d8a0767eb95c476c202494`, compiled without fast-math. This is an independent adversarial numerical cohort, not an extension of the original positive-power-of-two claim.

- **Strict positive-order counterexample:** normalized time `(hi=2^53, lo=1)` plus positive `2^-54` is mathematically larger, but the two-component result is bit-identical to the input and `bl_time2_compare` returns **0**. Thus *universal* strict monotonicity under arbitrary positive increments is false.
- **Frozen seed 1465 mixed-sign/non-power-of-two cohort:** 1,024 sequences × 16 operations = **16,384**. Exact rational oracle comparison found **14,759 inexact intermediate results** (90.08%), **1,625 exact**, **0 rejected additions**, and **0 step-sign ordering mismatches** *within this particular cohort*. Both GCC and Clang produced these counts locally. This percentage describes the deliberately adversarial generator, **not real-world error prevalence**.
- A committed reproducible test `tests/test_time2_adversarial.py` preserves both negative findings. Its two unittest methods passed locally with GCC; the exact test blob is `f3836706dec4281bc1bc50cdeba514dba5fb576b`. Exact-head CI and inherited repository suite remain unexecuted.

**Implication:** E465's positive-power-of-two holdout remains valid, but two floating-point components cannot guarantee arbitrary-length exact rational accumulation or arbitrary small positive-step progress. A production-grade generic timestamp contract must state a minimum resolvable increment or provide a fail-closed/fallback representation (for example, integer ticks with an explicit scale). Do not silently claim strict progress for every positive delta. No trajectory or weapon-specific integration was attempted.
