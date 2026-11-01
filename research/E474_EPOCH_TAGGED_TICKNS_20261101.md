# E474 | Versioned, epoch-tagged integer-nanosecond envelope

Date: 2026-11-01. **Generic numerical timestamp research only.** No integration into trajectory, targeting, physical-control, production, or deployment systems.

## Falsifiable question

E473's signed-int64 nanosecond value is exact within range but has no epoch identity. Two values with different caller-defined zero points can be subtracted without detection. Can a strictly opt-in representation reject such mismatches and unsupported wire versions/scales while preserving E473's exact arithmetic and atomic failure behavior?

## Frozen contract

- `BlEpochTickNs` holds a `BlTickNs` and a **nonzero** caller-managed `uint32_t epoch_id`. Epoch ID equality is required for subtraction. Addition of a duration preserves the epoch ID. Arithmetic overflow rejects without modifying the output.
- Version-1 wire encoding is **16 bytes**: `BT` magic (2), version `1` (1), nanosecond scale code `1` (1), epoch ID (4, unsigned big-endian), signed nanoseconds (8, big-endian two's complement). It is canonical across machine byte order.
- Decoding requires an explicit nonzero expected epoch ID. It rejects mismatches, invalid magic/version/scale, and null pointers without changing the output. It never converts between epochs.
- Epoch IDs are **identifiers, not physical clock definitions**. The caller must assign unique IDs to different epoch semantics and distribute an authoritative registry. Equal IDs with different underlying definitions remain undetectable. No UTC, leap seconds, time zones, clock drift, or calibration are inferred.
- The envelope has **no checksum or authentication**. A mutated tick payload can be decoded successfully with a different value. This is a preserved negative result, not a solved integrity problem.
- The 16-byte envelope doubles E473's raw eight-byte wire size. The int64 range limit remains approximately 292.47 years at nanosecond resolution. No production API changes.

## Offline reproduction

```sh
gcc -std=c11 -O2 -Wall -Wextra -Werror -pedantic -fsanitize=undefined -fno-sanitize-recover=all -Isrc src/tickns.c src/tickns_epoch.c tests/test_tickns_epoch.c -o /tmp/e474_gcc && /tmp/e474_gcc
clang -std=c11 -O2 -Wall -Wextra -Werror -pedantic -fsanitize=undefined -fno-sanitize-recover=all -Isrc src/tickns.c src/tickns_epoch.c tests/test_tickns_epoch.c -o /tmp/e474_clang && /tmp/e474_clang
python3 research/e474_epoch_oracle.py gcc clang
```

Both GCC and Clang standalone UBSan-instrumented C executables passed. The Python exact-arithmetic and byte oracle used seed **474**, **4,096** random signed-int64 pairs and **121** edge pairs, totaling **4,217** per compiler.

| Per compiler | GCC | Clang |
|---|---:|---:|
| Canonical wire round trips | 4,217 | 4,217 |
| Addition accepted / overflow rejected | 3,202 / 1,015 | 3,202 / 1,015 |
| Difference accepted / overflow rejected | 3,192 / 1,025 | 3,192 / 1,025 |
| Cross-epoch decode + arithmetic rejections | 8,434 | 8,434 |
| Mutated magic/version/scale rejections | 12 | 12 |
| Oracle mismatches | 0 | 0 |
| Payload corruption that **was not detected** | 1 explicit control | 1 explicit control |

These are synthetic stress-case counts, not real-world rates. All rejection checks preserved caller outputs. The first local C compilation failed due to an incorrect `-I` include path; correcting the path produced passing GCC and Clang runs. The oracle uses unsanitized shared libraries because sanitizer-instrumented standalone C executables are the direct undefined-behavior check.

## Scope and next discriminating test

This is a prototype layered on E473's opt-in generic timestamp module. The existing `BlTime2` API, callers, storage, runtime, and production workflows are unchanged. No full inherited repository suite or exact-head CI was run. Before integration, specify epoch-ID governance, version migration, corrupt-payload protection if needed, and unbiased native performance/storage comparisons. Do not merge this stacked research branch until the epoch registry contract is reviewed.
