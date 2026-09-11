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
- Time-step integration
- CSV output
- Unit tests

### v0.3 — Statistics
- Measurement uncertainty
- Mean, variance and standard deviation
- Monte Carlo simulation of generic projectile dispersion

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
cc -std=c11 -Wall -Wextra -pedantic src/main.c src/physics.c -lm -o ballisticslab
./ballisticslab
```

Run tests with:

```bash
make test
```

## Learning rule

Every feature should answer four questions:

1. What physical principle is being modeled?
2. What assumptions are we making?
3. What can make the model wrong?
4. How can we test it?

That keeps this from becoming a collection of cool-sounding firearm vocabulary with no actual engineering underneath it.
