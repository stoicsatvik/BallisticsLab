# E274 | Generic constant-acceleration integrator invariant audit

**Executed:** 2026-10-26 local (2026-10-25 UTC). [Exact-head CI 40235893043](https://github.com/stoicsatvik/BallisticsLab/actions/runs/40235893043) **SUCCESS** at `eee5d3575a4a377809c071cec8bc003127ad318c`.

## Question

Does the existing non-operational constant-gravity numerical integrator preserve analytic event timing, displacement, apex height, energy, and strictly increasing sample times across substantially different time steps?

**Predeclared deterministic grid:** five generic speeds (1, 3, 10, 30, 100 m/s) × five angles (10°, 25°, 45°, 65°, 80°) × six time steps (0.01, 0.05, 0.2, 1, 5, 10 s). **150 synthetic cases; 12,094 numerical samples.** This is a classroom physics consistency test, not a firing-solution tool or experimental projectile measurement.

## Actual CI results

| Numerical invariant | Maximum normalized absolute residual |
|---|---:|
| Analytic flight time | **2.2049001204650182e-14** |
| Analytic horizontal displacement | **5.3622255748352476e-14** |
| Analytic apex height | **4.3223087793755993e-14** |
| Mechanical energy per sample | **6.4028427004814152e-14** |

Normalization is `abs(measured - analytic) / max(1, abs(analytic))`. Every tested event time strictly increased; every final sample had exactly zero height and matched the reported impact event. Existing `make test` suites also passed.

**Claim:** constant-acceleration numerical/analytic agreement **SUPPORTED IN THE 150 SYNTHETIC CONFIGURATIONS**. This is not a global floating-point error bound, aerodynamic validation, sensor validation, or empirical ballistic performance.

**Unresolved:** extreme subnormal/overflow boundaries, alternate C math implementations, realistic measurement noise, air resistance and uncertainty-model coverage. A follow-on high-value test is cross-compiler precision/reproducibility and input-scaling invariance with explicitly bounded arithmetic.

**Safety:** Generic educational kinematics only. No weapons parameters, targeting, lethality, sight corrections or engagement optimization.
