# v0.2 — numerical vacuum trajectory trace

This module is a classroom numerical-methods exercise. It is not a real-world firing solution, targeting tool, or weapon model.

## Model

The state is `(x, y, vx, vy)` with constant acceleration `(0, -g)`, flat ground at `y = 0`, equal launch/landing elevation, no air resistance, and no wind. The integrator uses explicit Euler:

- `x[n+1] = x[n] + vx[n] * dt`
- `y[n+1] = y[n] + vy[n] * dt`
- `vx[n+1] = vx[n]`
- `vy[n+1] = vy[n] - g * dt`

When a step crosses the ground, the final contact sample is linearly interpolated between the last nonnegative-height state and the first nonpositive-height state. This avoids reporting a below-ground endpoint, but does not make Euler's global error disappear.

## Analytical reference

For launch speed `v` and angle `theta`:

- `vx = v cos(theta)`
- `vy = v sin(theta)`
- `t_f = 2 vy / g`
- `R = vx t_f`
- `H = vy^2 / (2g)`

The existing closed-form function remains the reference. The numerical trace is checked against it rather than replacing it.

## Error and convergence

Explicit Euler is first-order in time. For a fixed physical trajectory, reducing `dt` should reduce the global state error approximately linearly, although the exact observed ratio depends on the ground-crossing interpolation and where the sampled maximum occurs.

For the deterministic software check `v = 20 m/s`, `theta = 45°`, the numerical range errors are:

| Time step | Absolute range error |
|---:|---:|
| 0.08 s | 1.129890 m |
| 0.04 s | 0.564967 m |
| 0.02 s | 0.282521 m |
| 0.01 s | 0.141302 m |
| 0.001 s | 0.014141 m |

The fine-step endpoint is also checked against the analytical reference. These are software-model results, not physical measurements or universal error bounds.

## CSV

`./ballisticslab --csv trajectory.csv 0.01` runs the same interactive generic input prompts and writes `time_s,x_m,y_m,vx_mps,vy_mps` rows. The time step is in seconds. The CLI caps traces at one million samples to bound memory use.

## Limitations

No drag, wind, changing gravity, terrain, spin, object shape, launch mechanism, or environmental calibration is modeled. Mass is used only by the separate momentum and kinetic-energy demonstrations; it does not affect the vacuum trajectory. This is not validated against physical measurements.
