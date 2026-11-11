# E495 — mixed-sign two-component timestamp error envelope (11 November 2026)

## Question

Does the existing strict signed-step admission guard preserve direction and output atomicity across mixed-sign, near-cancellation, subnormal and overflow-adjacent inputs, and how often are admitted results exact relative to an exact-rational oracle?

## Frozen experiment

- Compile the existing generic src/time2.c with GCC/cc, C11, O2 and -fno-fast-math.
- Compare represented input and output values using Python Fraction.from_float; no decimal approximation is used as the oracle.
- Include fixed positive/negative sub-ULP counterexamples, exact cancellation, minimum subnormals, DBL_MAX-adjacent additions and a deterministic mixed-sign two-component cohort.
- Measure accepted/rejected operations, direction failures, failure-output mutation, exact versus inexact accepted results, canonical two-component witnesses and accepted error in high-component ULPs.
- No production C code is modified. No physical trajectory, weapon, target or firearm behavior is tested.

## Interpretation boundary

The API contract is directional admission, not arbitrary exact rational addition. A canonical two-component witness is sufficient evidence that a sum has a simple exact hi/lo representation; failure to find one is not proof of impossibility. Any accepted-but-inexact result is reported rather than hidden.

## Exact-head result

Pending exact-head Actions. No numerical error envelope is claimed before the receipt is inspected.

## Claim states

- Directional admission and failure atomicity: SUPPORTED only for previously measured E471 cohorts; E495 holdout NOT YET MEASURED.
- Exact rational addition for arbitrary mixed-sign inputs: NOT YET PROVEN and explicitly not promised by the API.
- Physical timing accuracy: NOT CLAIMED.
