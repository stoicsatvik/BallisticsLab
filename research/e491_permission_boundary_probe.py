"""E491 research-only local POSIX permission audit, not issuer authentication.

Audits the opened directory/file descriptors under a caller-chosen root.
The root and expected UID must be trusted independently. Never promotes,
mutates, cleans up, or authenticates a checkpoint.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat

from e490_nofollow_path import open_snapshot_nofollow


@dataclass(frozen=True)
class PermissionAudit:
    status: str  # consistent, rejected, inspection_error
    detail: str
    checked_components: int = 0


def audit_local_permissions(root: Path, relative: Path, expected_uid: int) -> PermissionAudit:
    """Check local owner and write permissions on root, descendants, and file.

    This is a narrow POSIX discretionary-permission test, not an authority
    check. Hard links, privileged writers, ACLs, mount changes and replaced
    pathnames are outside its guarantees. It does not read file contents.
    """
    path = Path(relative)
    names = path.parts
    if (path.is_absolute() or not names or '..' in names
            or not isinstance(expected_uid, int) or expected_uid < 0):
        return PermissionAudit('inspection_error', 'invalid relative path or expected UID')
    if (os.name != 'posix' or os.open not in os.supports_dir_fd
            or not all(hasattr(os, name) for name in ('O_DIRECTORY', 'O_NOFOLLOW', 'O_NONBLOCK'))):
        return PermissionAudit('inspection_error', 'required POSIX primitives unavailable')
    fd = None
    count = 0
    try:
        fd = open_snapshot_nofollow(Path(root))
        for index, component in enumerate(('.',) + names):
            if index:
                is_dir = index < len(names)
                flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                if is_dir:
                    flags |= os.O_DIRECTORY
                if hasattr(os, 'O_CLOEXEC'):
                    flags |= os.O_CLOEXEC
                child = os.open(component, flags, dir_fd=fd)
                os.close(fd)
                fd = child
            info = os.fstat(fd)
            count += 1
            want_dir = index < len(names)
            if not (stat.S_ISDIR(info.st_mode) if want_dir else stat.S_ISREG(info.st_mode)):
                return PermissionAudit('rejected', 'unexpected filesystem object type', count)
            if info.st_uid != expected_uid:
                return PermissionAudit('rejected', 'owner UID mismatch', count)
            if info.st_mode & 0o022:
                return PermissionAudit('rejected', 'group/world writable component', count)
        return PermissionAudit('consistent', 'local owner/mode checks only; issuer unverified', count)
    except (OSError, ValueError):
        return PermissionAudit('inspection_error', 'safe descriptor inspection failed', count)
    finally:
        if fd is not None:
            os.close(fd)
