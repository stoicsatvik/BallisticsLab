# E477 | Pinned epoch-registry snapshot and rollback falsification

Date: 2026-11-01. Research-only continuation of E476 namespace/epoch registry. Stacked on E476 PR #31; no production, physics, trajectory, runtime, deployment, or database change.

## Falsifiable question

Can an immutable, canonical local registry snapshot with a separately pinned SHA-256 digest reject accidental mutation, truncated files, stale rollback, namespace confusion, duplicate IDs, duplicate JSON keys, and noncanonical encodings? What fails when the attacker controls the expected digest as well as the snapshot?

## Candidate, exact scope

- Added `research/e477_pinned_registry_snapshot.py` using E476's `EpochRegistry` and `EpochDefinition` as the reference semantic model.
- Canonical, versioned JSON with 16-byte namespace and ascending nonzero uint32 epoch IDs, max 4,096 entries and 1 MiB.
- `load_pinned(data, expected_sha256, expected_namespace)` rejects digest mismatch before parsing, rejects duplicate keys/IDs and noncanonical representations, and returns a **new** registry only after complete validation. It never mutates a caller registry on failure.
- `publish_once` uses local POSIX temporary file + fsync + hard-link no-overwrite publication + directory fsync where available. It does not provide distributed consistency or trusted namespace allocation.
- The expected digest **must** be independently trusted and updated intentionally; computing it from the same untrusted file provides no authenticity.

## Executed validation

Locally reconstructed exact E476 source blob `fb25588a831ab921dde4e8fd8e5b47fdc3970574`, plus the new files. Python `unittest discover -s tests -p 'test_e477*.py' -v`: **12/12 passed**; Python `py_compile` passed. The two committed new file blobs were read back from GitHub and matched locally executed files exactly:

- `research/e477_pinned_registry_snapshot.py`: `713d3c724acaf800846a9a47af8cffa25c98c7c4`
- `tests/test_e477_pinned_registry_snapshot.py`: `2d94bf987e1e5d34b9a10793210710cb9d0be635`

Controls: exact round trip; single-byte mutation; truncation; stale rollback under newer trusted digest; wrong namespace; duplicate JSON keys; duplicate IDs; noncanonical encoding; unsupported format; exclusive publication/overwrite rejection; invalid digest; forged definition with attacker-controlled digest.

An exploratory single-process local run with 4,096 entries produced a 509,889-byte snapshot, approximately 52 ms to export and 90 ms to reload on this execution environment. These are **not** statistically controlled performance benchmarks or remote durability measurements.

## Preserved negative result

An attacker can change the semantic definition for epoch ID 7, compute the SHA-256 digest of that forged snapshot, and pass `load_pinned` **if the caller also trusts the attacker-supplied digest**. The same forged bytes fail under the original independently pinned digest. Therefore hash pinning protects only against changes relative to a trusted anchor; it does not authenticate an issuer, guarantee namespace uniqueness, provide anti-rollback without a trusted latest pin, prevent malicious registry creation, or make Python private state tamperproof.

No signatures, trusted keys, distributed consensus, clock/leap conversion, cross-process locking, multi-host durability, hostile-filesystem resistance, or authenticated migration are implemented. POSIX hard-link behavior and directory fsync are not portable to all platforms. No production integration or exact-head CI is claimed.

## Next falsification gate

Test concurrent local publishers and crash-recovery behavior under controlled fault injection; specify a separately trusted, auditable namespace issuer and signed checkpoint/rollback policy before any remote or production integration. Do not auto-migrate untrusted v1 timestamps. Keep this branch/PR draft and unmerged.
