"""E493 research-only advisory-lock identity diagnostic, not writer quiescence.

A POSIX flock is advisory and attaches to an opened inode. This read-only
probe compares that inode with the current pathname at one instant. It does
not acquire locks, authenticate writers, fence generations, clean up files,
or authorize checkpoint promotion. A matching result can race with a rename.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import stat


@dataclass(frozen=True)
class LockIdentity:
    status: str  # same_inode, replaced, inspection_error
    detail: str
    descriptor_inode: tuple[int, int] | None = None
    pathname_inode: tuple[int, int] | None = None


def inspect_lock_identity(fd: int, lock_path: Path) -> LockIdentity:
    """Compare an already-open descriptor to a non-followed pathname.

    This is an observation, NOT a lock ownership check. Caller must separately
    trust the directory and its writers; no result establishes quiescence.
    """
    if type(fd) is not int or fd < 0 or os.name != 'posix':
        return LockIdentity('inspection_error', 'invalid descriptor or non-POSIX host')
    try:
        opened = os.fstat(fd)
        named = os.lstat(lock_path)
        opened_id = (opened.st_dev, opened.st_ino)
        named_id = (named.st_dev, named.st_ino)
        if not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(named.st_mode):
            return LockIdentity('replaced', 'descriptor or pathname is not a regular file', opened_id, named_id)
        if opened_id != named_id:
            return LockIdentity('replaced', 'pathname now refers to a different inode', opened_id, named_id)
        return LockIdentity('same_inode', 'instantaneous inode match only; writers and races unverified', opened_id, named_id)
    except (OSError, ValueError, TypeError):
        return LockIdentity('inspection_error', 'cannot safely inspect descriptor/pathname')
