# E490 | Parent-symlink traversal falsifies final-component-only O_NOFOLLOW

Date: 2026-11-02. Research-only continuation of E487, stacked on draft PR #35.

## Falsifiable question and reproduced negative result

E487's read-only publication probe opened the snapshot with O_NOFOLLOW but did not pin parent directory components. On Linux/POSIX, a path `alias/snapshot.json` where `alias` is a symlink to a real directory still opens successfully under `os.open(path, O_NOFOLLOW)`. A local synthetic filesystem control reproduced this exact limitation: the old final-only open read the target through a symlinked parent. This is a path-trust defect in the research probe, **not** evidence of snapshot forgery, persistence failure, or an exploit against production software.

## Narrow additive fix

- Add `research/e490_nofollow_path.py` to open every ancestor directory with O_DIRECTORY|O_NOFOLLOW through descriptor-relative `openat` semantics, then open the final file with O_NOFOLLOW|O_NONBLOCK.
- Change only the research-only E487 probe to call the new helper. Existing read limits, digest validation, namespace checks and five-state result semantics remain unchanged.
- Reject `..` traversal and platforms without the required POSIX descriptor-relative features. Do not delete, retry, promote, authenticate or mutate publication state.
- Add 11 deterministic tests: valid nested paths, symlinked parent/ancestor/final components, parent traversal, absent path, directory root, FIFO, direct-probe integration, and a negative inode/pathname replacement demonstration.
- Add a branch-scoped GitHub Actions Python 3.13 workflow to run E477, E487 and E490 tests rather than relying on unrelated C CI.

## Validation and preserved limits

Before commit, the independent local helper prototype passed **8/8** synthetic POSIX tests. The existing final-only O_NOFOLLOW bypass was reproduced separately. Exact-head GitHub Actions run [#41371218322](https://github.com/stoicsatvik/BallisticsLab/actions/runs/41371218322) **SUCCEEDED** at commit `041b276df1967acb71c18fa4e7cee7236376eb51`: 12/12 E477 tests, 13/13 E487 tests, and 11/11 E490 tests (36/36 total), plus compilation of all four research modules. Concurrent exact-head E409 and C CI workflows also succeeded (runs #41371218298 and #41371218207). This is synthetic Linux/POSIX regression evidence, not physical crash durability, hostile-filesystem proof, or issuer authentication.

The fix protects against symlink traversal during descriptor-relative path opening. It does **not** establish trusted directory ownership, stable pathname identity after opening, hard-link provenance, issuer authentication, safe orphan cleanup, power-loss durability, or safety on hostile/network filesystems. A writer can rename or replace the path after opening; the fd still refers to the previously opened inode. The new test preserves that negative result.

No ballistic physics, operational guidance, live registry, checkpoint promotion, deployment, external outreach, or production publisher is changed. Keep the PR draft and unmerged pending review.
