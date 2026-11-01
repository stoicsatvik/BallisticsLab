# E473 | Checked C integer-nanosecond timestamp baseline

Date: 2026-11-01. **Generic numerical timestamps only.** No physical timing calibration, trajectory, targeting, weapon optimization, production integration, merge, or deployment.

## Frozen falsifiable contract

Given a caller-defined common epoch and exactly 1 ns/tick, the optional C `BlTickNs` prototype must perform addition and subtraction exactly whenever the mathematical result fits signed int64, and reject overflow without mutating outputs. Converting floor-seconds and subsecond nanoseconds must round-trip every representable tick, including negative epochs and `INT64_MIN`. Canonical 8-byte big-endian signed two's-complement encoding must round-trip and agree with Python's signed 8-byte big-endian encoding. No floating-point conversions are involved.

The epoch is **not encoded**. Consumers must choose and preserve a single epoch and scale across all operands, storage, and transport. No UTC, leap-second, timezone, or clock model is implied. A 100-year horizon at 365 days/year fits int64 ns; 300 years does not. The prototype does not replace `BlTime2` or change existing runtime callers.

## Reproduction and measured results

Run from the E473 branch:

```
gcc -std=c11 -O2 -Wall -Wextra -Werror -pedantic -fsanitize=undefined -fno-sanitize-recover=all src/tickns.c tests/test_tickns.c -o /tmp/e473_gcc && /tmp/e473_gcc
clang -std=c11 -O2 -Wall -Wextra -Werror -pedantic -fsanitize=undefined -fno-sanitize-recover=all src/tickns.c tests/test_tickns.c -o /tmp/e473_clang && /tmp/e473_clang
python3 research/e473_tick_oracle.py gcc clang
```

The two deterministic C executables both printed `E473 deterministic C contracts: PASS`, including UBSan instrumentation. Python seed **473**, **16,384** random signed int64 pairs plus **169** edge-pair combinations = **16,553** cases per compiler. Independent Python integer arithmetic and `int.to_bytes(8, 'big', signed=True)` supplied the oracle.

| Result per compiler | GCC | Clang |
|---|---:|---:|
| Cases / round-trip conversions | 16,553 | 16,553 |
| Addition accepted / rejected | 12,394 / 4,159 | 12,394 / 4,159 |
| Difference accepted / rejected | 12,461 / 4,092 | 12,461 / 4,092 |
| Arithmetic/serialization mismatches | **0** | **0** |
| Explicit invalid floor-second/nanosecond inputs rejected | 5 | 5 |

All rejected operations preserved the sentinel output. The rejection counts are synthetic overflow exposure, **not real-world error rates**. The edge corpus includes `INT64_MIN`, `INT64_MAX`, adjacent values, and negative subsecond boundaries. All representable signed int64 ticks round-trip by the implemented arithmetic rules, but the empirical checks cover only the stated cohort and platform.

## Negative results, toolchain limitation, and scope

- An initial test build failed because the standalone local fixture used an incorrect relative include path. The include path was corrected before validation.
- Initial Clang `ctypes` shared-library loading with UBSan failed due to an unavailable sanitizer runtime symbol. The standalone C test executables **did** pass with UBSan under both compilers; the Python `ctypes` oracle instead loads non-sanitized shared libraries. This is a test-harness/toolchain limitation, not evidence that the C arithmetic failed.
- The `from_parts` implementation originally used `INT64_MAX - base` when `base` could be negative, risking signed overflow in the guard itself. This was corrected to apply the upper-bound subtraction only when `base >= 0` before running the oracle. The final tested implementation avoids this undefined behavior.
- No performance claim: Python/ctypes call overhead makes it an unsuitable native speed benchmark. No ABI/endianness portability beyond canonical wire bytes, concurrency, full inherited repository suite, exact-head CI, or external integration was tested.
- Signed 64-bit nanoseconds remain range-limited. Epoch metadata is intentionally external, so cross-epoch arithmetic cannot be detected by this API. This is a deliberate limitation and a potential integration hazard.

## Next discriminating gate

Design an epoch-tagged/versioned wire envelope and verify cross-epoch rejection, then compare native C throughput and storage cost against `BlTime2` under identical measurement methodology. Do not integrate with physical/trajectory systems until epoch and range contracts are reviewed. Keep this research PR draft and stacked on E472.
