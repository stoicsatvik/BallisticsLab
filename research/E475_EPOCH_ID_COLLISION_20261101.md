# E475 | Epoch-ID collision falsification and governance boundary

Date: 2026-11-01. Generic numerical timestamp research only. No integration with trajectory, physical-control, targeting, production, deployment or storage code.

## Question and frozen baseline

E474 introduced a 16-byte, versioned envelope with a nonzero 32-bit caller-assigned epoch_id. Its subtraction and decoder reject **different IDs**, but do not authenticate the meaning of an ID. Does deriving the ID by truncating a deterministic hash of an epoch definition safely avoid cross-epoch arithmetic, or can two distinct definitions receive the same ID and pass E474's guard?

Source-exact E474 C inputs used for the local test (Git blob SHA):
- tickns.c: db78e2a89e4d8fd88e07ccb7fd8752c3e2eae623
- tickns.h: 383484e3eb36a22b297b873c29a7f9c1456da042
- tickns_epoch.c: feef5c6bb259f7ea8d72247b47c3f3ed333fea22
- tickns_epoch.h: 8b840236efdbbb54c3d16f251b1c47601f166ff8

## Reproduction

Run the deterministic Python experiment: python3 research/e475_epoch_id_collision.py

Compile and run the native C negative control using GCC or Clang:

    gcc -std=c11 -O2 -Wall -Wextra -Werror -pedantic -fsanitize=undefined -fno-sanitize-recover=all -Isrc src/tickns.c src/tickns_epoch.c tests/test_epoch_id_collision.c -o /tmp/e475_gcc && /tmp/e475_gcc
    clang -std=c11 -O2 -Wall -Wextra -Werror -pedantic -fsanitize=undefined -fno-sanitize-recover=all -Isrc src/tickns.c src/tickns_epoch.c tests/test_epoch_id_collision.c -o /tmp/e475_clang && /tmp/e475_clang

Seed 475; 200,000 synthetic opaque 128-bit definitions, each prefixed by a fixed namespace. BLAKE2b outputs of 32, 64 and 128 bits are computed separately. No actual epoch semantics or clock metadata are modeled. This is a frozen collision counterexample, not an empirical operational rate.

| Digest width | Observed duplicate IDs | Birthday-model P(at least one collision), n=200,000 |
|---|---:|---:|
| 32 bits | **4** | 0.990501197966016 |
| 64 bits | 0 | 1.0841967508869006e-9 |
| 128 bits | 0 | 5.877442366752667e-29 |

First distinct-definition collision: ID **1781595200**, indices **86288** and **89389**. The Python experiment asserted their underlying definitions differ. It also reproduced 1,000/1,000 overlapping IDs from two independently restarted sequential allocators. A toy local registry rejected conflicting re-registration only because both definitions were available to it.

**Native negative control (GCC and Clang, both UBSan):** The C test uses the collided ID for two intentionally different semantic epochs. E474 subtraction **accepts** them and returns 95 ns; the decoder accepts the second timestamp with that ID. A distinct-ID control rejects subtraction and preserves the output. The C test *passes by reproducing the unsafe admission*, not by proving a fix. Both compilers passed with strict warnings and UBSan, with no reported undefined behavior.

## Implications and proposed contract

1. **Reject** uncoordinated 32-bit hashes as globally unique epoch IDs. Collision resistance is bounded by the wire field width even when the underlying hash is cryptographic. A larger random ID reduces accidental collisions but does not define or authenticate epoch semantics.
2. If retaining v1, require an authoritative immutable registry that allocates nonzero IDs, stores canonical epoch definitions (origin, scale, clock/time standard, leap-second policy if relevant), refuses conflicting re-registration, and distributes registry identity/version with each dataset. Never independently assign the same numeric IDs across unrelated registries.
3. An in-process registry check cannot protect against remote parties lying about definitions, registry divergence, corrupted payloads, or IDs already reused before synchronization. A production contract needs a trust and migration model, potentially a larger namespace or registry identifier in a future wire version.
4. Preserve E474's v1 strict version rejection. Do not silently reinterpret v1 IDs as v2 or convert between epochs without an explicit validated mapping. The current 16-byte format is neither authenticated nor checksummed.

## Scope and next gate

No production C API changed. No PR was merged or deployed. Native C tests reproduce a known failure of semantic governance; Python tests quantify a synthetic hash-collision cohort. Full inherited suite, exact-head CI, actual distributed-registry behavior, hash attack resistance, version migration and performance remain unverified. Next, specify an immutable registry/namespace format and add explicit cross-registry mismatch and version-migration rejection tests before runtime integration.
