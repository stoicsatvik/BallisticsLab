"""E493/E494 research-only advisory-lock identity diagnostic, not writer quiescence.

A POSIX flock is advisory and attaches to an opened inode. This read-only
probe compares that inode with a no-follow opened pathname at one instant.
No path component may be a symlink. It does not acquire locks, authenticate
writers, fence generations, clean up files, or authorize promotion. A matching
result can still race with a rename, and hard links remain indistinguishable.
"""
from dataclasses import dataclass
import errno
import os
from pathlib import Path
import stat

from e490_nofollow_path import open_snapshot_nofollow


@dataclass(frozen=True)
class LockIdentity:
    status: str  # same_inode, replaced, inspection_error
    detail: str
    descriptor_inode: tuple[int, int] | None = None
    pathname_inode: tuple[int, int] | None = None


def inspect_lock_identity(fd: int, lock_path: Path) -> LockIdentity:
    """Compare an already-open descriptor with a no-follow pathname.

    This is an observation, NOT a lock ownership check. The caller must
    independently trust the root and writers; no result proves quiescence.
    """
    if type(fd) is not int or fd < 0 or os.name != 'posix':
        return LockIdentity('inspection_error', 'invalid descriptor or non-POSIX host')
    try:
        opened = os.fstat(fd)
        try:
            named_fd = open_snapshot_nofollow(Path(lock_path))
        except OSError as error:
            if error.errno == errno.ELOOP:
                return LockIdentity('replaced', 'symlink rejected by no-follow open')
            raise
        try:
            named = os.fstat(named_fd)
        finally:
            os.close(named_fd)
        opened_id = (opened.st_dev, opened.st_ino)
        named_id = (named.st_dev, named.st_ino)
        if not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(named.st_mode):
            return LockIdentity('replaced', 'descriptor or pathname is not a regular file', opened_id, named_id)
        if opened_id != named_id:
            return LockIdentity('replaced', 'pathname now refers to a different inode', opened_id, named_id)
        return LockIdentity('same_inode', 'instantaneous inode match only; writers and races unverified', opened_id, named_id)
    except (OSError, ValueError, TypeError):
        return LockIdentity('inspection_error', 'cannot safely inspect descriptor/pathname')
