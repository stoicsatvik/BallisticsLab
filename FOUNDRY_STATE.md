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

Priority sequence:
1. reusable time-step integrator + CSV output
2. analytical-vs-numerical validation
3. uncertainty propagation + Monte Carlo statistics
4. generic aerodynamic drag models
5. measurement/error analysis
6. visualizations and reproducible notebooks

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

Track:
- definitions and categories
- age/training rules
- licensing concepts
- shooting-sport pathways
- transport/storage rules at a high level
- prohibited/restricted categories
- amendment dates and source provenance

Do not search for acquisition loopholes, evasion methods, false paperwork, illegal sourcing, or ways to bypass licensing.

### 4. Public historical/forensic case studies
Maintain a sourced case-study library for completed, publicly documented incidents, including selected assassinations, shootings, military incidents, accidents, and forensic investigations when they teach physics, evidence handling, engineering, law, or system failure.

For each case, separate:
- verified timeline
- weapon/system identification only when publicly established
- publicly documented forensic evidence
- uncertainty / disputed claims
- engineering or legal lesson
- source quality

Do not reconstruct attack plans, optimal firing positions, security vulnerabilities, evasion routes, targeting procedures, or actionable replication guidance. Do not track protected people for future attack risk or build live targeting intelligence.

### 5. Military systems literacy
Study military technology at a systems level:
- small-arms families and historical development
- logistics and ammunition standardization
- reliability in environmental conditions
- human factors
- sensing, communications, protection, mobility, and sustainment concepts
- doctrine only at a broad historical/organizational level
- procurement, industrial base, and lifecycle economics

Prefer official manuals released for public education, museums, government reports, declassified material, academic research, and reputable historical sources.

Do not provide tactical attack planning, target selection, exploitation of military/security weaknesses, explosive design, armour-defeat recipes, or instructions for increasing lethality.

## Current issues
- #1 v0.2: time-step trajectory simulator and CSV output
- #2 v0.3: uncertainty and Monte Carlo statistics
- #3 law: primary-source India firearms law map

## Highest-EV next moves
1. Finish #1 with deterministic tests against the analytical baseline.
2. Add a structured source/provenance schema for legal and historical notes.
3. Build a non-operational mechanism taxonomy.
4. Add the first historical case study only after the sourcing template exists.

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
Whenever the Unified Parallel Foundry advances BallisticsLab, record:
- branch / commit / PR
- exact capability or research increment
- tests / validation
- sources used
- claim status
- safety/public-boundary check
- blocker
- highest-EV next move
