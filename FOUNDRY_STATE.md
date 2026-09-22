# BallisticsLab — Unified Foundry State

## Mission
Build a rigorous educational firearms-adjacent engineering lab spanning projectile physics, numerical simulation, measurement/statistics, high-level mechanism literacy, public-source legal research, military-technology context, and historical forensic case studies.

The project is for scientific, legal, historical, and engineering literacy. It must not become an operational weapons manual.

## Claim discipline
Use these labels for every substantive result:
- **PROVEN** — reproduced or derived with tests/data.
- **SUPPORTED** — credible evidence exists but the repo has not independently reproduced it.
- **NOT YET PROVEN** — hypothesis or planned claim.
- **REJECTED** — contradicted by evidence/testing.
- **BLOCKED** — requires data, access, tooling, legal clarification, or approval.

Never fabricate measurements, incident details, military capabilities, or legal conclusions.

## Active streams

### 1. Physics + simulation
Current baseline: analytical 2D vacuum projectile model in C with momentum and kinetic-energy helpers.

#### v0.2 numerical evidence
- Branch: `foundry/numerical-vacuum-integrator`
- Draft PR: #7
- Exact validated implementation head: `1e6cf5ddfcb0eaf4d980eb5f0672582a4a6f3c2a`
- GitHub Actions: `C CI` run `35619490999` completed successfully on that exact head.
- Capability: reusable constant-gravity numerical integrator with configurable `dt`, structured `time/x/y/vx/vy` samples, interpolated ground crossing, explicit sample ownership, deterministic CSV serialization, and deterministic analytical-vs-numerical comparison.
- Validation: deterministic tests compare impact time, range, and sampled apex with the existing analytical vacuum model, check ground termination and CSV schema, and reject invalid inputs.
- Claim: **SUPPORTED** for these committed synthetic vacuum-model software contracts. Real-world projectile prediction is **NOT YET PROVEN** and outside this increment.
- Safety boundary: no firearm-specific parameters, targeting, sight corrections, atmospheric correction, optimization, or real-world firing solutions.

#### v0.3 generic statistics substrate
- Branch: `foundry/generic-statistics`
- Stacked draft PR: #8 (base: `foundry/numerical-vacuum-integrator`)
- Exact validated implementation head: `a9b34138f76c2480357f437a27eb727cbdc3543f`
- GitHub Actions: `C CI` run `35754552162` completed successfully on that exact head.
- Capability: numerically stable mean/sample variance/stddev, deterministic interpolated p05/p50/p95, seeded reproducible uniform/normal sampling, and fail-closed handling of non-finite/undersized samples and invalid distribution parameters.
- Validation: deterministic C tests are wired into the existing `make test` gate and passed exact-head CI.
- Claim: **SUPPORTED** for this bounded generic statistics software contract. Monte Carlo uncertainty propagation itself is **NOT YET PROVEN** until implemented and validated separately.
- Safety boundary: descriptive statistics and synthetic random sampling only; no firearm-specific parameters, targeting, sight corrections, atmospheric correction, optimization, lethality analysis, or real-world firing solutions.

Priority sequence:
1. preserve the validated v0.2 and generic-statistics evidence packages until merge approval exists
2. add seeded Monte Carlo uncertainty propagation using generic synthetic measurement fixtures only
3. generic aerodynamic drag models only if they remain non-operational and educational
4. measurement/error analysis
5. visualizations and reproducible notebooks

Keep models generic and educational. Do not produce real-world firing solutions, sight corrections, target engagement calculators, or optimization for harming people.

### 2. Mechanics + firearm literacy
Study conceptually:
- cartridge anatomy and terminology
- action-cycle families
- feed / chamber / lock / fire / unlock / extract / eject cycle
- bolt, recoil, blowback, gas-operated, lever/pump, and manually operated systems at a high level
- materials, tolerances, fouling, heat, wear, reliability, recoil, ergonomics, and failure modes
- historical platform evolution and engineering trade-offs

Allowed output: diagrams, abstractions, terminology maps, reliability models, historical comparisons, and non-construction-level mechanism explanations.

Do not provide construction dimensions, manufacturing recipes, conversion/modification instructions, improvised weapons guidance, suppressor construction, automatic-fire conversion, or methods to defeat safety systems.

### 3. India law + safety
Use primary official sources first: India Code, Ministry of Home Affairs, Gazette notifications, Arms Act, Arms Rules, and current official amendments.

Track definitions/categories, age/training rules, licensing concepts, shooting-sport pathways, transport/storage at a high level, prohibited/restricted categories, amendment dates and provenance. Do not search for acquisition loopholes, evasion, false paperwork, illegal sourcing, or licensing bypasses.

### 4. Public historical/forensic case studies
Maintain sourced case studies only for completed, publicly documented incidents where they teach physics, evidence handling, engineering, law, or system failure. Separate verified timeline, publicly established system identity, documented evidence, uncertainty, lesson, and source quality. Never reconstruct attack plans, firing positions, vulnerabilities, evasion routes, targeting procedures, or actionable replication guidance.

### 5. Military systems literacy
Study military technology only at systems/historical level: families and development, logistics/standardization, environmental reliability, human factors, sensing/communications/protection/mobility/sustainment, broad doctrine, procurement, industrial base and lifecycle economics. No tactical attack planning, target selection, weakness exploitation, explosive design, armour-defeat recipes, or lethality optimization.

## Current issues
- #1 v0.2: time-step trajectory simulator and CSV output — implementation + exact-head CI evidence present in draft PR #7; unmerged
- #2 v0.3: generic statistics substrate now exact-head validated in stacked draft PR #8; Monte Carlo propagation remains pending
- #3 law: primary-source India firearms law map

## Highest-EV next moves
1. Preserve PRs #7 and #8 as validated evidence packages; do not merge without explicit approval.
2. Continue #2 with seeded Monte Carlo propagation over deliberately generic synthetic measurement fixtures, with deterministic fixtures and convergence checks.
3. Add a structured source/provenance schema for legal and historical notes.
4. Build a non-operational mechanism taxonomy.
5. Add the first historical case study only after the sourcing template exists.

## Validation rules
- physics claims require derivation, test, or cited source
- numerical work requires deterministic fixtures and error bounds
- legal claims require exact source + date checked
- historical/incident claims require multi-source corroboration when disputed
- military capability claims must distinguish public fact from estimate
- simulations must state assumptions and limitations

## Public-repo boundary
This repository is public. Never commit private personal data, credentials, leaked material, private security information, restricted manuals, graphic media, or sensitive operational details.

## Foundry reporting
Whenever the Unified Parallel Foundry advances BallisticsLab, record branch/commit/PR, exact increment, tests/validation, sources, claim status, safety boundary, blocker and highest-EV next move.
