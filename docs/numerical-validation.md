# Numerical trajectory validation

## Scope

This module is an educational, generic 2D vacuum-motion model. It assumes a point mass launched from level ground under uniform gravitational acceleration (`g = 9.80665 m/s^2`) with no aerodynamic drag, wind, spin, Earth curvature, terrain, or weapon-specific parameters. It is not a firing-solution or target-engagement calculator.

## Integrator

`bl_simulate_vacuum` advances position and velocity at a configurable fixed `dt` using the constant-acceleration kinematic update:

- `x(t + dt) = x(t) + vx * dt`
- `y(t + dt) = y(t) + vy * dt - 0.5 * g * dt^2`
- `vy(t + dt) = vy(t) - g * dt`

Because acceleration is constant in this deliberately simple model, the per-step state update is analytically exact apart from floating-point rounding. The remaining landing-time/range error comes primarily from linearly interpolating the ground crossing between the last positive-height sample and the first non-positive-height sample.

## Deterministic validation fixture

The test suite compares a generic `10 m/s`, `45 degree` launch against `bl_vacuum_trajectory`, the closed-form vacuum baseline already present in the repository.

Acceptance bounds frozen in tests:

- `dt = 0.01 s`: landing time within `1e-4 s`, range within `1e-3 m`
- `dt = 0.001 s`: landing time within `1e-6 s`, range within `1e-5 m`

The finer step must also generate more samples than the coarse step. Invalid `dt` and insufficient output capacity fail closed.

These tolerances validate this implementation only under the assumptions above. They are not evidence for real-world projectile prediction.

## CSV contract

`bl_write_trajectory_csv` writes deterministic rows with columns:

`time_s,x_m,y_m,vx_mps,vy_mps`

The function serializes previously computed samples only; it performs no optimization or target-related calculation.
