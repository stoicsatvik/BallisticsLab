"""E487 research-only read-side probe for local E477 snapshot publication.

This is a diagnostic, not a recovery authority. It never writes, deletes,
retries publication, or claims power-loss durability. A digest is only a
trust anchor if its provenance was independently established by the caller.
"""
from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import stat

from e477_pinned_registry_snapshot import MAX_BYTES, load_pinned, sha256
from e490_nofollow_path import open_snapshot_nofollow


class ProbeState(str, Enum):
    ABSENT = "absent"
    VISIBLE_UNVERIFIED = "visible_unverified"
    VISIBLE_PIN_VALID_DURABILITY_UNKNOWN = "visible_pin_valid_durability_unknown"
    VISIBLE_PIN_REJECTED = "visible_pin_rejected"
    INSPECTION_ERROR = "inspection_error"


@dataclass(frozen=True)
class ProbeResult:
    state: ProbeState
    size: int | None = None
    observed_sha256: str | None = None
    detail: str = ""


def probe_snapshot(path: Path, expected_sha256: str | None = None,
                   expected_namespace: bytes | None = None) -> ProbeResult:
    """Inspect a single opened inode without modifying publication state.

    A matching digest and canonical structure prove only that the *observed*
    bytes match a caller-provided pin. They do not establish issuer authority,
    latest-checkpoint status, stable pathname identity, or crash durability.
    Orphan temporary files are deliberately not enumerated or deleted.
    """
    if (expected_sha256 is None) != (expected_namespace is None):
        return ProbeResult(ProbeState.INSPECTION_ERROR, detail="digest and namespace must be supplied together")
    try:
        fd = open_snapshot_nofollow(Path(path))
    except FileNotFoundError:
        return ProbeResult(ProbeState.ABSENT)
    except (OSError, ValueError):
        return ProbeResult(ProbeState.INSPECTION_ERROR,
                           detail="could not open target and ancestors without following symlinks")

    try:
        with os.fdopen(fd, "rb", closefd=True) as handle:
            metadata = os.fstat(handle.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                return ProbeResult(ProbeState.INSPECTION_ERROR, detail="target is not a regular file")
            if metadata.st_size > MAX_BYTES:
                return ProbeResult(ProbeState.VISIBLE_PIN_REJECTED, size=metadata.st_size,
                                   detail="snapshot exceeds size cap")
            if expected_sha256 is None:
                return ProbeResult(ProbeState.VISIBLE_UNVERIFIED, size=metadata.st_size)
            data = handle.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                return ProbeResult(ProbeState.VISIBLE_PIN_REJECTED, size=len(data),
                                   detail="snapshot exceeds size cap during read")
            digest = sha256(data)
            try:
                load_pinned(data, expected_sha256, expected_namespace)
            except (ValueError, TypeError):
                return ProbeResult(ProbeState.VISIBLE_PIN_REJECTED, size=len(data),
                                   observed_sha256=digest, detail="pin or canonical snapshot validation failed")
            return ProbeResult(ProbeState.VISIBLE_PIN_VALID_DURABILITY_UNKNOWN,
                               size=len(data), observed_sha256=digest)
    except OSError:
        return ProbeResult(ProbeState.INSPECTION_ERROR, detail="could not read target safely")
