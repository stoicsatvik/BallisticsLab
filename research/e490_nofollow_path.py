"""E490 research-only, fail-closed POSIX open through no-follow directory descriptors.

The returned descriptor pins an inode, not a durable snapshot or a permanent
pathname-to-inode mapping. This helper never writes or cleans up snapshots.
"""
from __future__ import annotations

import os
from pathlib import Path


def open_snapshot_nofollow(path: Path) -> int:
    """Open for bounded read without following symlinks in any path component.

    The caller owns the returned fd. Relative paths are anchored at the current
    working directory at call time; '..' components are rejected.
    """
    if (os.name != "posix"
            or not all(hasattr(os, flag) for flag in
                       ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK"))
            or os.open not in os.supports_dir_fd):
        raise OSError("safe descriptor-relative no-follow open unavailable")
    components = Path(path).parts
    if not components or ".." in components:
        raise ValueError("empty or parent-traversing snapshot path")
    absolute = Path(path).is_absolute()
    names = components[1:] if absolute else components
    if not names:
        raise ValueError("snapshot path names a directory root")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
        file_flags |= os.O_CLOEXEC
    directory_fd = os.open("/" if absolute else ".", directory_flags)
    try:
        for component in names[:-1]:
            child_fd = os.open(component, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
        return os.open(names[-1], file_flags, dir_fd=directory_fd)
    finally:
        os.close(directory_fd)
