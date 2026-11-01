# E484 | Local snapshot publication race and fault-injection audit

Date: 2026-11-02. Research-only continuation of E477's pinned epoch-registry snapshot. Stacked on draft E477 PR #32. No production runtime, physics, trajectory, external service, or merge.

## Falsifiable question

For E477 `publish_once`, can eight simultaneous writers produce exactly one intact final path without overwrites or leaked temporary files? At which fault boundary does a raised exception cease to imply that no snapshot was published?

## Experiment

Added six deterministic, local POSIX tests in `tests/test_e484_publication_faults.py`:

1. Eight threads synchronize at a barrier and race to publish distinguishable byte payloads. Exactly one must win; the target must match that winner's complete bytes and no `.e477-` temporary files may remain.
2. Inject an `EIO` at the temporary file `fsync`; the destination must not exist and temporary files must be cleaned.
3. Inject an `EIO` at `os.link`; the destination must not exist and temporary files must be cleaned.
4. Inject an `EIO` at the second `fsync`, after the hard link is created. Preserve the **negative result**: `publish_once` raises, but the target already exists with intact, hash-verifiable bytes. The outcome is not an atomic rollback and durability after an actual power loss is unknown.
5. A pre-existing destination cannot be overwritten.
6. An over-limit payload is rejected without creating files.

The concurrent writers use distinguishable bytes solely to test publication atomicity, **not** to claim that those bytes are valid registry snapshots. The post-link negative control uses a valid pinned registry snapshot.

## Executed validation

On the local POSIX execution environment, `python -m unittest discover -s tests -p 'test_e484*.py' -v` completed **6/6 passing** in approximately 0.02 s; Python compilation passed. The E477 publication module used locally was reconstructed byte-for-byte from the GitHub source blob `713d3c724acaf800846a9a47af8cffa25c98c7c4`, and `git hash-object` matched that SHA. The E476 registry dependency was reconstructed source-equivalently for the methods used, **not** as an exact full dependency blob. The new E484 test file's committed blob SHA `29507464c6fdd3bb9d28ae51f0902ed5dc07a038` matches the locally executed file.

No full repository checkout, inherited test suite, exact-head GitHub Actions result, process-kill test, actual power-loss test, network filesystem, Windows portability test, or distributed consistency test is claimed. Eight threads in one process do not prove correctness across processes or hostile filesystems.

## Negative finding and engineering implication

A directory-`fsync` failure after the `os.link` operation can leave an already visible target even though `publish_once` raises `OSError`. Consumers **must not** interpret every publication exception as evidence that no target exists. A retry must check the final path and independently validate its content against the trusted digest and namespace; if the latest trusted checkpoint is unavailable, do not silently infer success or promote the snapshot.

The test does not prove durable persistence after a crash. The expected digest remains a separate trust anchor and is not issuer authentication. No implementation or API semantics were changed in this experiment.

## Next gate

Exercise isolated **multi-process** publication and fault injection around directory sync; design an explicit publication-outcome contract distinguishing `not_published` from `published_but_durability_unconfirmed`, without promising crash durability or changing production callers. Preserve draft/unmerged status until trusted issuer and checkpoint governance exist.
