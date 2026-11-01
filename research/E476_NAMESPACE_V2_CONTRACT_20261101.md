# E476 | Namespace-tagged timestamp v2 and immutable registry reference

Date: 2026-11-01. Research-only generic numerical timestamp prototype, stacked on E475. No production API, physics trajectory, runtime, deployment or storage changes.

## Hypothesis and frozen negative control

E475 found two distinct synthetic epoch definitions assigned the same 32-bit ID `1781595200`; the E474 v1 subtraction incorrectly accepted the pair as compatible. Can an explicit 128-bit **namespace** reject the same numeric ID across independent registries, and can an immutable registry model reject redefinition within one namespace? Will version migration fail closed rather than silently treating v1 bytes as v2?

## Candidate contract (not a final protocol)

A research-only `BlEpochTickNsV2` holds exact signed int64 nanoseconds, nonzero 32-bit epoch ID, and nonzero 16-byte opaque namespace ID. The 32-byte v2 wire format is: offsets 0..1 magic `BT`; 2 version `2`; 3 scale `1` nanosecond; 4..19 namespace ID; 20..23 big-endian epoch ID; 24..31 big-endian two's-complement tick. `decode` takes the expected namespace and epoch ID and an explicit input length. Version 1, wrong length, wrong namespace, wrong epoch ID, invalid headers and null pointers fail without modifying the output. Checked addition and difference inherit E473's overflow rules.

The Python reference registry requires a nonzero 16-byte namespace and immutable mapping from nonzero uint32 ID to a canonical JSON definition containing origin, timescale, clock standard and leap policy. Conflicting re-registration and cross-namespace imports are rejected; failed imports do not partially update state. No implicit v1 migration is permitted.

**Important:** Namespace IDs are not authenticated, signed or collision-proof. The registry has no durable storage, distributed consensus, trusted allocation, key management or clock conversion. A reused `(namespace, epoch_id)` pair for different semantic definitions remains **undetectable by the v2 C envelope**. The Python model is only a local contract test, not a deployable authority. No integrity checksum exists; payload corruption is still accepted. Thus the v2 format is a containment improvement, not a proof of globally safe epoch semantics.

## Independent local execution

Inputs: exact E475 `src/tickns.c` Git blob `db78e2a89e4d8fd88e07ccb7fd8752c3e2eae623` and `src/tickns.h` Git blob `383484e3eb36a22b297b873c29a7f9c1456da042`, plus the new files.

```sh
for compiler in gcc clang; do
  "$compiler" -std=c11 -O2 -Wall -Wextra -Werror -pedantic \
    -fsanitize=undefined -fno-sanitize-recover=all -Isrc \
    src/tickns.c src/tickns_epoch_v2.c tests/test_tickns_epoch_v2.c \
    -o "/tmp/e476_$compiler" && "/tmp/e476_$compiler"
done
python3 research/e476_registry_contract.py
python3 -m py_compile research/e476_registry_contract.py
```

Both GCC and Clang passed strict C11/UBSan. Each completed 4,096 deterministic seeded round trips and 4,096 wrong-namespace rejections, plus explicit header, length, epoch-ID, null-pointer, overflow, output-preservation and version-rejection assertions. The collision ID from E475 was accepted for same namespace and rejected for different namespaces. The Python registry checks passed, including immutable redefinition, atomic import, invalid namespace/ID and untrusted v1 migration rejection.

**Preserved negative results:** (1) Two different semantic epochs with the *same* namespace and numeric ID still pass the native difference check, demonstrating the requirement for authoritative registry governance. (2) A deliberate tick payload bit flip was decoded successfully, demonstrating the absence of integrity protection. (3) Wire overhead doubled from 16 bytes in v1 to 32 bytes in v2. These are intentional falsification cases, not passing security claims.

## Remaining gates

This experiment has not verified the full inherited repository suite, exact-head CI, persistence, remote registry divergence, authentication, collision resistance, protocol interoperability, native throughput or compatibility with deployed clients. Do not auto-upgrade v1. Before integration, specify authoritative namespace issuance, immutable registry persistence and trust roots, and explicit audited migration mappings; separately benchmark overhead against E473/E474. Keep the PR draft and unmerged.
