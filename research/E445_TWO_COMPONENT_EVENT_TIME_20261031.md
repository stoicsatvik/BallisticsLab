# E445 | Two-component generic event-time representability, 31 October 2026

**Scope:** educational, dimensionless constant-acceleration arithmetic. No real-world firing solution, targeting, empirical measurement, weapon optimization, or C production integration.

## Question
E429's frozen adversarial grid identified four positive event offsets smaller than half a binary64 timestamp ULP. A strict scalar timestamp cannot advance without either rejecting the event or inventing a later representable timestamp. Can a two-component (hi, lo) expansion represent the exact sum of the **existing binary64** state time and positive event offset without silently shifting the event?

## Frozen population and controls
- Reused the unchanged E429 10 magnitudes × 9 abstract angles × 12 near-half-step offsets: 1,080 synthetic configurations.
- Original E429 categories were independently re-evaluated on every configuration: 1,070 accepted scalar events, six exact zero endpoints, four sub-ULP strict-time rejections.
- The new source independently mirrors E429's floating arithmetic and checks the first crossing step.
- For every positive crossing, form the exact rational sum of the two input binary64 values using `Fraction`; round once to binary64 `hi`, then round the exact residual to `lo`.
- Compare the pair as an exact rational sum, not by evaluating `hi + lo` in binary64 (which would discard the residual).
- An independent 90-digit Decimal quadratic root is computed from the same binary64 state for an error diagnostic; it is **not** a physical ground truth.

## Executed results
| Quantity | Result |
|---|---:|
| Frozen synthetic configurations | 1,080 |
| Positive event crossings | 1,074 |
| Scalar binary64 accepted | 1,070 |
| Scalar binary64 sub-ULP rejected | 4 |
| Exact zero endpoints (not positive events) | 6 |
| Nonmonotone two-component events | 0 / 1,074 |
| Exact-rational expansion sum errors | 0 / 1,074 |
| Maximum root approximation error / timestamp ULP | 3.55284e-15 |
| Sub-ULP event offset / timestamp ULP | 0.3090962644 |
| Bias if artificially rounded to next scalar timestamp / ULP | 0.6909037356 |

For all four original E429 rejections, `hi == t` and `lo > 0`, so the exact two-component timestamp advances without pretending that the binary64 high component changed. Both components survived exact hexadecimal serialization and deserialization. For all 1,070 previously accepted cases, the high component matched the old scalar timestamp, with a low residual preserving the binary64-input sum.

## Interpretation
- **SUPPORTED IN THE FROZEN SYNTHETIC PYTHON MODEL:** a two-component expansion exactly preserves the arithmetic sum of the *binary64* event-state time and its computed offset on all 1,074 positive crossings; it avoids the four strict scalar-time rejections without an artificial one-ULP forward jump.
- **REJECTED AS A GENERAL FIX:** blindly replacing rejected timestamps with `nextafter(t,+inf)` is not exact, and introduces ~0.691 ULP positive timing bias in the four frozen cases.
- **NOT YET PROVEN:** full C implementation, propagation across subsequent integration steps, portability across libm/compiler/ABI, timestamp comparison/serialization in consumers, performance/memory cost, or physical-model accuracy.
- **Safety boundary:** all quantities are abstract classroom inputs; this is generic numerical representability research only.

## Validation
Locally executed the unchanged E429 source and the new exact-source E445 module. Five E445 unittest cases passed, including the full 1,080-case grid. Python source compilation passed. New GitHub source and test blob SHA values matched the locally executed files. No GitHub Actions were deliberately requested and no full repository C suite was run.

Reproduce on the stacked branch:

```bash
python -m research.e445_two_component_event_time
python -m unittest discover -s tests -p 'test_e445_two_component_event_time.py' -v
```

## Next decisive experiment
Integrate a **generic** two-component event-time abstraction behind an explicit opt-in API and compare it against the unchanged strict binary64 implementation on held-out boundary seeds. Measure downstream monotonicity, energy/state invariants, CSV roundtrip, cost and cross-compiler behavior. Reject the abstraction if a later consumer silently collapses it back to binary64 or the added complexity outweighs measurable correctness gains.
