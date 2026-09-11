# Firearm Mechanics — Systems View

This document studies firearms as mechanical systems at a conceptual level. It deliberately avoids construction dimensions, modification procedures, performance optimization, or instructions for defeating safety/legal controls.

## 1. Functional decomposition

A repeating firearm has to solve several mechanical functions reliably:

1. store ammunition
2. present a cartridge to the action
3. place it in the chamber
4. support/lock the system for the pressure event
5. initiate the cartridge when intentionally commanded
6. contain and direct expanding gas through the barrel
7. unlock when appropriate for the design
8. extract the spent case
9. eject or otherwise clear it
10. reset/cock the mechanism and feed the next cartridge where applicable

Thinking this way is more useful than memorizing model names. Different firearm architectures are different engineering solutions to the same function graph.

## 2. Action families

### Manually operated

Examples include single-shot, bolt-action, lever-action and pump-action systems. Human input performs much of the cycle between shots.

### Self-loading / semiautomatic

Energy from firing is used to perform part of the mechanical cycle. One deliberate trigger actuation corresponds to one discharge in the semiautomatic case.

Conceptual energy sources include:

- recoil-driven mechanisms
- gas-operated mechanisms
- simple pressure/recoil relationships used in some blowback-type systems

We care here about **energy flow and timing**, not design recipes.

## 3. Engineering variables

Useful high-level variables include:

- mass and inertia of moving components
- spring forces
- friction
- material strength and fatigue
- thermal expansion
- manufacturing tolerances
- contamination
- lubrication state
- ammunition consistency

These create a reliability problem rather than a single-equation problem.

## 4. Reliability as probability

Suppose a mechanism succeeds independently with probability `p` on each cycle. An intentionally simplified model gives the probability of `n` successful cycles as:

```text
P(all n succeed) = p^n
```

Real mechanisms are not independent Bernoulli trials, but this illustrates why small reliability differences compound over many cycles.

## 5. Tolerance stacks

Manufactured parts are never exact. If several dimensions contribute to a final clearance or alignment, their tolerances combine.

This is a general mechanical-engineering concept and should be studied using harmless example mechanisms first: shafts, bearings, sliders and linkages.

## 6. Thermal thinking

A mechanical system that repeatedly releases energy experiences heating. Temperature can change:

- dimensions through thermal expansion
- lubricant behavior
- material properties
- friction

That makes firearms a useful case study in coupled mechanical + thermal systems, without needing to construct one.

## 7. Questions to answer later

1. What functions are common to manually operated and self-loading systems?
2. Why are timing and energy budgets central to repeating mechanisms?
3. How do tolerances interact with dirt, heat and friction?
4. Why does reliability have to be treated statistically rather than as a binary property?
5. What trade-offs appear between mass, complexity, reliability and controllability?
