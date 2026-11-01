# E486 | Multi-process publication and process-death boundaries

Date: 2026-11-02. Research-only continuation of E484, stacked on draft PR #33. No production API changes, merge, deployment, external outreach, or trusted-checkpoint promotion.

## Falsifiable question

Does E477's POSIX no-overwrite hard-link publication still produce one complete winner when eight **separate processes** race? Does an abrupt process death at either side of the hard-link operation leave a clean directory? Does a visible destination after process death prove durable publication?

## Executed local experiment

Three new POSIX-only unittest methods in `tests/test_e486_multiprocess_crash_boundaries.py`:

1. Eight forked child processes simultaneously publish eight **individually valid** pinned-registry snapshots with distinct epoch origins. One process must report publication; seven must receive `FileExistsError`; the destination must equal the winning snapshot and pass `load_pinned` with its digest and namespace.
2. A child calls `os._exit(41)` instead of executing the hard-link syscall. Expected negative: no final destination exists, but one private `.e477-*` temporary file survives because Python `finally` cannot execute.
3. A child calls `os._exit(42)` on the second `fsync`, after `os.link`. Expected negative: the destination is visible and validates against the trusted digest, **and** an orphaned temporary file remains. Visibility is not proof of persistence after power loss.

The abrupt exits are intentional **process-death simulations**, not hardware crashes. Temporary files are created mode 0600 by E477, but may consume storage or retain snapshot contents until a separately designed cleanup procedure runs.

## Observed results

- Local Linux/POSIX Python 3.13: **3/3 tests passed** in approximately 0.1-0.2 seconds; Python compilation passed.
- Eight-process race: exactly one complete winner, seven no-overwrite losers, no temporary files after ordinary completion.
- Before-link exit: zero destinations and one orphaned temporary file.
- After-link/pre-directory-sync exit: one valid visible destination and one orphaned temporary file.
- The new test's committed Git blob is `c8343dcd75ce92245b9af09ef25a3c85823f867c`, verified against the locally executed file.
- **Validation limitation:** local tests used a source-equivalent reconstruction of E477's `publish_once` and relevant snapshot operations, plus a reduced E476 registry dependency. This is not a complete exact GitHub checkout or full inherited test run. Exact-head CI is not claimed.

A Python 3.13 `fork()`-in-multithreaded-process deprecation warning was observed during the eight-process test. The tests currently require POSIX `fork` and `O_DIRECTORY`; they intentionally skip unsupported environments. A safer spawn/forkserver test design is a future portability gate.

## Engineering implication

The no-overwrite guarantee survives the exercised local multi-process race, but **cleanup does not survive abrupt process death**. A recovery path must independently distinguish (a) no destination, (b) visible but not durability-confirmed destination, and (c) validated snapshot under a separately trusted checkpoint. Cleanup of orphaned `.e477-*` files must avoid deleting a concurrent live publisher's temporary file; blind glob deletion is unsafe.

No issuer authenticity, actual power-loss durability, network filesystem behavior, distributed consistency, or authoritative namespace governance has been established. Digest pinning does not authenticate the issuer.

## Next gate

Design a read-only publication-recovery probe with explicit outcome states and a conservative stale-temp cleanup policy, then test under real filesystem process boundaries. Preserve the E477 API and keep all stacked PRs draft/unmerged until trust and durability governance are defined.
