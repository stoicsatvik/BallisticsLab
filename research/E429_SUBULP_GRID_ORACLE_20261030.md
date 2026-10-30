# E429 | Sub-ULP terminal-event prevalence and independent decimal oracle

Date: 2026-10-30. Tier A BallisticsLab. Isolated research branch:
`research/e429-subulp-grid-oracle-20261030`, stacked on E409 draft PR #22.
This is **generic educational constant-acceleration numerical analysis only**,
not an operational weapon model, firing solution, or empirical physics study.

## Discriminating question

E409 demonstrated one legitimate positive terminal-event offset that cannot be
represented as a later binary64 timestamp, causing a fail-closed strict-time
rejection. Does this affect a broad deterministic near-half-duration grid, or
only a narrow set of rounding configurations? Does an independent high-precision
oracle agree that the rejected times are unrepresentable as later binary64
values?

## Frozen inputs and procedure

The standalone Python source `research/e429_subulp_grid_oracle.py` mirrors
E409's time/vertical-state floating-point operations, including the
`hypot`-based positive root and `impact_t > t` guard, but **does not execute
the repository's C implementation**. Ten dimensionless classroom input
magnitudes (0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 50, 100), nine abstract angles
(5, 10, 15, 20, 30, 45, 60, 75, 85 degrees) and 12 offsets
(1–8, 12, 16, 24, 32) from a half-duration step give 1,080 deterministic
configurations. The offset formula is `dt = (T/2)*(1-k*2^-53)`.
This grid is *deliberately adversarial*, not a random operational distribution.

For negative-height crossings, a 90-digit `Decimal` oracle solves the
quadratic from the **exactly represented binary64 state** `(t,y,vy,g)`.
This distinguishes floating-point event representation from discrepancies in
the underlying physical model. No independent measurements are involved.

## Observed results

Independent Python and JavaScript mirrors returned the same status counts:

| Category | Count |
|---|---:|
| Accepted terminal event | 1,070 |
| Exact zero-height endpoint | 6 |
| Positive sub-ULP terminal event rejected | 4 |
| Other guard / invalid root / timeout | 0 |
| Total | 1,080 |

The four rejections were the `(magnitude,angle,offset)` tuples
`(50,15,1)`, `(50,15,2)`, `(100,15,1)`,
`(100,15,2)`. All occur at the third numerical step.
The corresponding positive event offsets were approximately
`1.3726631583055404e-16` and `2.7453263166110807e-16`,
each **0.3090962644 ULP** of its preceding timestamp. Consequently the
binary64 addition rounds to the unchanged timestamp.

The 90-digit independent oracle also rounded all four exact event timestamps
back to the preceding binary64 time. It identified **zero** accepted events
whose oracle event timestamp would round to the preceding time. Maximum
absolute binary64-versus-Decimal root discrepancy over accepted events was
approximately `4.83e-30` in the abstract time units.

Offset-wise: k=1 had 82 accepts, 6 exact endpoints and 2 rejections;
k=2 had 88 accepts and 2 rejections; every k>=3 had 90 accepts.

## Interpretation and claim boundaries

**SUPPORTED IN TWO SOURCE-EQUIVALENT SYNTHETIC MIRRORS:** the E409 strict-time
failure is a genuine representability boundary for these four cases; it is not
evidence that the numerical root is physically invalid. The event cannot be
encoded as a strictly later **binary64 scalar** without moving it to a
different representable timestamp.

**REJECTED FOR THIS GRID:** the assertion that *every* nearby two-step
boundary fails; 1,076 of 1,080 cases did not trigger the sub-ULP guard.

**NOT YET PROVEN:** exact C behavior for all 1,080 cases, portability across
different libm/compiler/ABI implementations, global prevalence, correctness of
a two-component timestamp representation, or empirical physics accuracy.
The 4/1080 fraction is **not a population probability**.

E409's narrower single-case C execution was previously verified in exact-head
CI. E429's new Python file was committed and read back, but **not executed from
the exact GitHub commit or in CI**; the reported numbers come from separately
executed independent Python and JavaScript mirrors. No paid Actions run was
requested.

## Next experiment

Freeze a two-component or extended-precision event-time representation on
unseen finite synthetic cases. Compare monotonicity, round-trip serialization,
terminal-state invariants and memory/cost against the unchanged fail-closed
binary64 contract. Reject any workaround that silently fabricates a later
timestamp. Keep the educational, non-operational boundary.
