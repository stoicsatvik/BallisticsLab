# E487 | Read-only snapshot publication recovery probe

Date: 2026-11-02. Research-only continuation of E486, stacked on draft PR #34. No production publisher, physics, trajectory, checkpoint, deployment or hidden-data changes.

## Question and implementation

Can a diagnostic distinguish a missing destination, a visible unverified file, a visible canonical snapshot matching a caller-supplied digest and namespace, and a visible invalid file without claiming crash durability or issuer authenticity?

The new research/e487_publication_recovery_probe.py opens one descriptor with POSIX O_NOFOLLOW and O_NONBLOCK, checks fstat for a regular file and E477's 1 MiB bound, and uses the existing pinned loader. It never publishes, retries, promotes checkpoints, scans temporary files, or deletes anything. Filesystem reads can still update access timestamps on some mounts.

States: absent; visible_unverified; visible_pin_valid_durability_unknown; visible_pin_rejected; inspection_error. A partial digest/namespace is an inspection error, not a success. A matching digest is meaningful only when independently trusted by the caller.

## Executed results

- Local Linux/POSIX Python 3.13.5: 13/13 new synthetic tests passed; 12/12 inherited E477 tests also passed (25/25 combined); Python compilation succeeded.
- E476 source, E477 source, and E477 native test files were reconstructed byte-for-byte from GitHub and verified against exact Git blob hashes fb25588, 713d3c7, and 2d94bf9.
- New source and test blobs were locally tested and verified against committed Git blobs c7ee031 and 2a2d08.
- Controls: absent, unpinned, pinned valid, digest mismatch, namespace mismatch, malformed data under matching digest, incomplete pin, symlink, FIFO, oversize, injected post-link fsync failure, orphan preservation, and attacker-supplied digest.
- E486's two previously triggered exact-head workflows (E409 and C CI) had both succeeded on ddd42a5 when checked. E487 exact-head CI and full inherited suite were not yet verified.

## Preserved negative results

1. A post-link directory-fsync failure raises but can leave a visible, pin-valid destination. The probe labels it visible_pin_valid_durability_unknown, **not** durable or authoritatively published.
2. A forged canonical snapshot passes when its attacker-controlled digest is supplied, and fails under the original digest. Hash agreement is not issuer authentication or an authoritative latest checkpoint.
3. An orphaned .e477-* temporary file can coexist with an absent or visible destination. The probe does not delete it: a filename pattern does not establish that the writer is dead.
4. An opened inode is not proof that the pathname still refers to that inode later. O_NOFOLLOW protects only the final path component; parent symlinks, hostile directory ownership, hard links, network filesystems, concurrent in-place writes, and power-loss persistence are outside this test.
5. Windows and systems without the required POSIX flags fail closed. No signed issuer, checkpoint authority, distributed consistency, or physical power-loss test is claimed.

## Next gate

Define independently authenticated latest-checkpoint issuance, directory ownership and a quiescence protocol before automatic promotion or orphan cleanup. Never blindly glob-delete .e477-* files. Keep the stacked research PRs draft and unmerged.
