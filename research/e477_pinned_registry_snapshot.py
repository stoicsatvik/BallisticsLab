"""E477 research-only, SHA256-pinned immutable registry snapshot.

A digest is only useful if supplied from a separately trusted channel. This
module is NOT a registry authority, signature, consensus protocol or clock
conversion service. POSIX hard-link publication is local-filesystem only.
"""
import hashlib
import hmac
import json
import os
import re
import tempfile
from pathlib import Path

from e476_registry_contract import EpochDefinition, EpochRegistry

MAX_BYTES = 1_048_576
MAX_ENTRIES = 4096
FIELDS = frozenset(("clock_standard", "leap_policy", "origin", "timescale"))


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON key")
        obj[key] = value
    return obj


def snapshot_bytes(registry: EpochRegistry) -> bytes:
    if not isinstance(registry, EpochRegistry):
        raise ValueError("expected EpochRegistry")
    if not isinstance(registry.namespace_id, bytes) or len(registry.namespace_id) != 16 or not any(registry.namespace_id):
        raise ValueError("invalid namespace")
    if len(registry._entries) > MAX_ENTRIES:
        raise ValueError("too many entries")
    entries = []
    for epoch_id, canonical in sorted(registry._entries.items()):
        if type(epoch_id) is not int or not 1 <= epoch_id <= 0xFFFFFFFF:
            raise ValueError("invalid epoch ID")
        definition = json.loads(canonical, object_pairs_hook=_unique_pairs)
        if not isinstance(definition, dict) or set(definition) != FIELDS:
            raise ValueError("invalid definition")
        rebuilt = EpochDefinition(**definition)
        if rebuilt.canonical() != canonical:
            raise ValueError("noncanonical definition")
        entries.append({"id": epoch_id, "definition": definition})
    data = _encode({"format": "ballisticslab-epoch-snapshot-v1", "namespace": registry.namespace_id.hex(), "entries": entries})
    if len(data) > MAX_BYTES:
        raise ValueError("snapshot exceeds size cap")
    return data


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_pinned(data: bytes, expected_sha256: str, expected_namespace: bytes) -> EpochRegistry:
    """Fail closed, returning a NEW registry only after complete validation."""
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ValueError("invalid snapshot bytes")
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("invalid trusted digest")
    if not hmac.compare_digest(sha256(data), expected_sha256):
        raise ValueError("digest mismatch")
    registry = EpochRegistry(expected_namespace)
    try:
        payload = json.loads(data.decode("ascii"), object_pairs_hook=_unique_pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"format", "namespace", "entries"}:
        raise ValueError("invalid snapshot structure")
    if payload["format"] != "ballisticslab-epoch-snapshot-v1" or payload["namespace"] != expected_namespace.hex():
        raise ValueError("snapshot format or namespace mismatch")
    entries = payload["entries"]
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        raise ValueError("invalid entry list")
    previous = 0
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"id", "definition"}:
            raise ValueError("invalid entry")
        epoch_id = entry["id"]
        if type(epoch_id) is not int or not previous < epoch_id <= 0xFFFFFFFF:
            raise ValueError("IDs must be nonzero, unique, ascending uint32")
        previous = epoch_id
        definition = entry["definition"]
        if not isinstance(definition, dict) or set(definition) != FIELDS:
            raise ValueError("invalid definition fields")
        try:
            accepted = registry.register(epoch_id, EpochDefinition(**definition))
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid definition values") from exc
        if not accepted:
            raise ValueError("conflicting definition")
    if _encode(payload) != data:
        raise ValueError("noncanonical snapshot encoding")
    return registry


def publish_once(path: Path, data: bytes) -> None:
    """POSIX local atomic no-overwrite publication, not remote durability."""
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ValueError("invalid snapshot bytes")
    path = Path(path)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".e477-", delete=False) as handle:
            temp_path = Path(handle.name)
            os.chmod(temp_path, 0o600)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temp_path, path)  # atomic creation; FileExistsError on overwrite
        if hasattr(os, "O_DIRECTORY"):
            fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
