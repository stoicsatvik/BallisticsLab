# BallisticsLab

BallisticsLab is an educational physics and engineering sandbox for studying projectile motion, measurement, statistics, and the high-level mechanics and legal context of firearms.

The project is intentionally **non-operational**: it does not provide weapon-construction instructions, modification guidance, armour-defeat methods, firing solutions, or advice for illegal acquisition/use. The goal is to understand the science and systems safely.

## What this repo will teach

- Newtonian projectile motion
- Momentum and kinetic energy
- Numerical simulation in C
- Measurement uncertainty and statistics
- High-level firearm mechanism concepts
- Safety principles
- Indian firearms law from official sources

## Roadmap

### v0.1 — Projectile physics
- Vacuum trajectory model
- Flight time, range and maximum height
- Momentum and kinetic energy helpers

### v0.2 — Numerical simulation
- Reusable explicit-Euler time-step integration
- Ground-contact interpolation
- CSV output with a configurable time step
- Analytical-reference and convergence tests

### v0.3 — Statistics
- Measurement uncertainty
- Mean, sample variance and standard deviation
- Seeded pseudo-random sampling for reproducible experiments
- Monte Carlo propagation for generic classroom measurement examples

### v0.4 — Aerodynamics
- Generic drag models
- Model limitations and validation

### v0.5 — Mechanics and law notebooks
- Conceptual action-cycle explanations
- Reliability and tolerance concepts at a non-construction level
- India legal-reference notes sourced from official material

## Build

```bash
make
./ballisticslab
```

Or directly:

```bash
cc -std=c11 -Wall -Wextra -pedantic src/main.c src/physics.c src/integrator.c -lm -o ballisticslab
./ballisticslab
```

Generate a generic numerical trace (the same input prompts are used):

```bash
./ballisticslab --csv trajectory.csv 0.01
```

The final argument is the time step in seconds. The CLI caps a trace at one million samples.

Run tests with:

```bash
make test
```

See [docs/numerical-integrator.md](docs/numerical-integrator.md) for the update equations, interpolation, convergence example and limitations.

## Learning rule

Every feature should answer four questions:

1. What physical principle is being modeled?
2. What assumptions are we making?
3. What can make the model wrong?
4. How can we test it?

That keeps this from becoming a collection of cool-sounding firearm vocabulary with no actual engineering underneath it.
