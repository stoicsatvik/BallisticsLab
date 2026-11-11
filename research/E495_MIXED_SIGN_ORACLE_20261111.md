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

Exact-head GitHub Actions run 43015154836 succeeded on commit 463724c92968e6418c6b2d7fecb6ce74357a0261:

- Deterministic unit tests: 2/2 passed. The inherited C CI and GCC/Clang E409 workflows also succeeded at the same head.
- Frozen cohort: 4,186 total operations (8 structured boundaries, 82 near-cancellation cases and 4,096 seeded mixed-sign cases).
- Strict admission accepted 4,183 and rejected 3. There were **0 wrong-direction admissions** and **0 output mutations on rejection**.
- Of 4,183 accepted results, 262 were exact relative to the Fraction oracle and 3,921 were inexact. All 262 canonical two-component witnesses were accepted; zero rejections had a canonical finite-normalized witness.
- The three rejections were the positive and negative sub-low-component-resolution cases and DBL_MAX + DBL_MAX overflow. Minimum-subnormal addition/cancellation and DBL_MAX ± minimum-subnormal were admitted correctly.
- For the 3,921 accepted-inexact results, error measured as a fraction of one ULP of the high component: median 4.4407187013752533e-94, p95 4.485771064403731e-19, p99 1.563860336325389e-17, maximum 2.7413932014134916e-17. This is a high-component-ULP normalization, not a universal relative-error or physical-time bound.
- Receipt artifact 13853105292; compact ZIP SHA-256 is recorded in the Actions run. The script records source SHA-256 f3917dc6361884e7a09fefa07ada61534a93d20b5b194541595ee245ebb73601.
- Outcome: directional admission and failure atomicity SUPPORTED for this frozen cohort. Exact rational addition is NOT SUPPORTED as a general claim; the API does not promise it. The measured inexact residuals are extremely small relative to the high-component ULP in this cohort, but this does not establish portability or application-level accuracy.


## Claim states

- Directional admission and failure atomicity: SUPPORTED only for previously measured E471 cohorts; E495 holdout NOT YET MEASURED.
- Exact rational addition for arbitrary mixed-sign inputs: NOT YET PROVEN and explicitly not promised by the API.
- Physical timing accuracy: NOT CLAIMED.
