# E491 | Local permission checks do not authenticate checkpoint issuers

Date: 2026-11-02. Research-only continuation of E490, stacked on draft PR #36.

## Falsifiable engineering question

Can a read-only POSIX descriptor walk check a caller-chosen snapshot root and each child directory/file for local owner UID and group/world write bits, while rejecting symlinked descendants and traversal, without modifying the snapshot?

**Yes for the tested synthetic local POSIX filesystem.** The E491 probe opens the root using the E490 no-follow helper, then inspects each descendant through `dir_fd` and `fstat`. A caller supplies the expected UID and independently trusted root. It returns only `consistent`, `rejected`, or `inspection_error`; it neither reads snapshot bytes nor authorizes recovery.

## Local experiment and negative control

A locally reconstructed E490 helper and the E491 research module passed **10/10** synthetic Python unittest cases on POSIX, including: regular 0700/0600 path; group-writable directory; world-writable root; group-writable file; wrong expected UID; symlinked descendant; parent traversal; absent file; absolute relative-path rejection; and external hard-link provenance.

**Critical negative result:** A file created outside the caller-chosen root, then hard-linked into a 0700/0600 path, passes all local UID/mode checks. Therefore a successful result **cannot** establish checkpoint issuer identity or provenance. This counterexample is preserved as a passing regression test. Local permission bits also do not prove power-loss durability or immutable pathname identity.

The local tests were executed against the E491 source and a reconstructed, source-equivalent E490 helper. This is **not** full-repository validation; exact-head GitHub Actions is required. E491 adds its own Python 3.13 workflow running E477, E487, E490 and E491 tests.

## Strict limitations

- The caller must independently trust the root path and expected UID. This audit does not establish either.
- POSIX discretionary permission checks do not account for ACLs, privileged writers, hostile mount namespaces, network filesystems, or changes after an inode is opened.
- A hard link to externally created data can pass; no issuer signature or authenticated checkpoint is verified.
- The function never writes, deletes orphan files, promotes snapshots, modifies production publishing, or changes ballistics physics.
- No destructive merge, deployment, external email, or recovery action is authorized by this result.

## Next gate

Specify an independent authenticated checkpoint issuer and a cooperative writer-quiescence protocol. Test both against malicious hard-link and non-cooperating writer controls before considering cleanup or promotion. Keep this PR draft and unmerged.
