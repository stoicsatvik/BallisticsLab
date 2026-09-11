# Physics Mental Model

BallisticsLab starts from first principles, not firearm-specific memorization.

## 1. State

For a generic projectile in two dimensions, the minimum state is:

- horizontal position `x`
- vertical position `y`
- horizontal velocity `vx`
- vertical velocity `vy`

With launch speed `v0` and angle `theta`:

```text
vx = v0 cos(theta)
vy = v0 sin(theta)
```

## 2. Vacuum model

Assume:

- constant gravitational acceleration `g`
- no atmosphere
- flat launch/landing height
- projectile behaves as a point mass

Then:

```text
x(t) = v0 cos(theta) t
y(t) = v0 sin(theta) t - 1/2 g t^2
```

For equal launch and landing heights:

```text
flight_time = 2 v0 sin(theta) / g
range       = v0^2 sin(2 theta) / g
max_height  = v0^2 sin^2(theta) / (2 g)
```

These are idealized classroom equations. Real trajectories differ because of aerodynamic drag, wind, geometry, environmental conditions, and measurement error.

## 3. Momentum

Linear momentum is:

```text
p = m v
```

Momentum is useful because it makes you think in terms of conserved system quantities rather than vague ideas like "power."

## 4. Kinetic energy

```text
E_k = 1/2 m v^2
```

Velocity appears squared, so energy is much more sensitive to speed than momentum is.

## 5. Measurement uncertainty

A measured quantity should eventually be treated as a distribution rather than a magical exact number.

For repeated measurements `x_i`:

```text
mean = sum(x_i) / n
variance = sum((x_i - mean)^2) / (n - 1)
standard_deviation = sqrt(variance)
```

This connects directly to the statistics work in the roadmap.

## 6. Next engineering step

Replace the closed-form trajectory with time stepping:

```text
vx(t + dt) = vx(t)
vy(t + dt) = vy(t) - g dt
x(t + dt)  = x(t) + vx dt
y(t + dt)  = y(t) + vy dt
```

Once that works and is tested, generic aerodynamic forces can be introduced.

## Questions to be able to answer

1. Why can horizontal and vertical motion be analyzed separately in the vacuum model?
2. Why does kinetic energy scale with `v^2` while momentum scales with `v`?
3. Which assumptions make the current range equation unrealistic?
4. Why is a numerical simulator useful when a closed-form equation already exists?
5. How would measurement uncertainty propagate into the calculated trajectory?
