# E493 | Advisory locks do not prove writer quiescence

Date: 2026-11-02. Research-only continuation of E492, stacked on draft PR #38.

## Falsifiable question

Can an exclusive POSIX `flock` on a conventional lockfile, combined with a descriptor/pathname inode comparison, establish that all writers have stopped and a checkpoint is safe to promote or clean up?

**No.** In nine synthetic POSIX tests, a cooperative contender was excluded while an uncooperative writer modified the locked inode, and replacing the lockfile pathname allowed two simultaneously held exclusive locks on distinct inodes. The read-only diagnostic detects a replaced pathname **at the instant of inspection** but cannot fence later renames or noncooperating writers.

## Reproduction and observed outcomes

```bash
python -m py_compile research/e493_lock_identity_probe.py tests/test_e493_lock_identity_probe.py
python -m unittest discover -s tests -p 'test_e493_lock_identity_probe.py' -v
```

Python 3.13.5, Linux local run: **9/9 PASS**, including the following falsification controls:

| Control | Observed result | What it does not prove |
| --- | --- | --- |
| Two cooperative contenders, one held inode | Second `LOCK_EX|LOCK_NB` rejected | No uncooperative writer exists |
| Uncooperative writer while holder owns exclusive lock | Same locked file was modified | Advisory lock is a write barrier |
| Lockfile renamed and recreated | Second exclusive lock succeeded while first holder remained alive | Lock pathname is a unique fencing token |
| Abrupt holder process exit | Kernel lock released; another process acquired it | All other writers have quiesced |
| Descriptor/pathname identity comparison | Replaced inode and symlink rejected; unchanged inode reported | No rename can occur immediately after inspection |

All test writes and process deaths are confined to `tempfile.TemporaryDirectory()`. No repository files or production snapshots are modified by the experiment. Tests use `multiprocessing` spawn and explicit bounded synchronization.

## Diagnostic boundary

`research/e493_lock_identity_probe.py` is **read-only**. It compares an already-open descriptor's `(st_dev, st_ino)` to a non-followed pathname's `(st_dev, st_ino)`, and rejects missing paths, symlinks, directories, and invalid descriptors. A `same_inode` status is a transient observation only. The module does **not** acquire locks, prove ownership, issue fencing tokens, enforce writer cooperation, authenticate checkpoints, persist anti-rollback state, delete or promote snapshots, or provide a security guarantee.

The experiments run on one Linux filesystem and do not model NFS, cross-host consensus, real power failure, ACL bypass, privileged adversaries, or scheduler-wide races. Passing tests establish only the stated synthetic counterexamples.

## Engineering implication and next gate

Automatic orphan cleanup or checkpoint promotion must remain disabled. A future design needs a trusted single-writer authority or externally enforced fencing/lease mechanism, independent issuer authentication, durable anti-rollback state, and explicit crash/restart experiments. A conventional lockfile plus a one-time inode check is insufficient. Keep this PR draft, stacked and unmerged.
