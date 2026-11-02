# E494 | Lockfile parent symlink traversal falsifies E493 identity diagnostic

Date: 2026-11-02. Research-only follow-up incorporated into draft PR #39 rather than creating another stacked PR.

## Falsifiable question

Does E493's `os.lstat(lock_path)` protect every ancestor from symlink traversal when comparing an opened lockfile descriptor with its pathname?

**No.** `lstat` does not follow the final component but traverses symlinked parents. In a synthetic temporary directory, a symlink `alias -> trusted_dir` made `lstat(alias/writer.lock)` report the same inode as the open lock descriptor, so E493 would return `same_inode` even though the supplied pathname passed through an untrusted symlinked parent.

## Minimal safe correction

Replace pathname `lstat` with E490's already tested `open_snapshot_nofollow` descriptor-relative traversal, then compare `fstat` on both descriptors. The helper uses `O_DIRECTORY|O_NOFOLLOW` on each ancestor and `O_NOFOLLOW|O_NONBLOCK` on the final component. Close the temporary descriptor in `finally`. Preserve E493's `replaced` result for a final symlink (`ELOOP`), and fail closed with `inspection_error` for symlinked ancestors, unsafe traversal and unavailable primitives. No contents are read.

## Local evidence

- Before correction: the synthetic `lstat(alias/writer.lock)` returned the same inode as the original descriptor (**false-positive `same_inode`**).
- After correction: five new E494 controls passed locally on Linux/Python 3.13.5: immediate-parent symlink, ancestor symlink, `..` traversal, hard-link alias, and FIFO nonblocking rejection.
- E493 synthetic regression suite also passed locally (14 tests in a locally extended version of the prior nine-test suite). Both the committed E494 test blob `bba937a` and updated E493 diagnostic blob `88bc7ad` match the locally executed files.
- Exact-head GitHub Actions status: **pending independent verification** at documentation time. The updated workflow runs inherited E477/E487/E490/E491/E492/E493 plus E494.

## Preserved negative controls and limits

A hard link to the same inode still returns `same_inode`. A path may be renamed after inspection. The caller-supplied root, filesystem/mount namespace, writer identities, cooperative lock discipline and authority are unverified. `flock` remains advisory. The result never establishes writer quiescence, checkpoint issuer authentication, persistent anti-rollback, durable publication, or permission to promote snapshots or delete orphan files.

No production recovery behavior, key provisioning, cleanup, deployment, trajectory or weapon functionality changed.

## Exact-head CI validation

At commit `e4f11519f3ffbf21609586173c6693c51cf5d70a`, GitHub Actions [E493/E494 Python run #41392250743](https://github.com/stoicsatvik/BallisticsLab/actions/runs/41392250743) **SUCCEEDED**: compilation and E477 (12), E487 (13), E490 (11), E491 (10), E492 (17), E493 (9), E494 (5) test steps, **77 tests in total**. [C CI #41392250911](https://github.com/stoicsatvik/BallisticsLab/actions/runs/41392250911) and [E409 #41392250732](https://github.com/stoicsatvik/BallisticsLab/actions/runs/41392250732) also succeeded. These CI results do not establish trusted fencing, multi-host correctness or power-loss durability.
