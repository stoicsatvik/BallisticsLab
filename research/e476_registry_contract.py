"""E476 reference-only immutable namespace/epoch registry.

No authenticity, consensus, network sync, leap-second conversion or v1 migration.
The v2 C envelope only transports opaque namespace and epoch IDs; callers
must supply and independently validate the semantic definitions.
"""
from dataclasses import dataclass
import json


@dataclass(frozen=True)
class EpochDefinition:
    origin: str
    timescale: str
    clock_standard: str
    leap_policy: str

    def canonical(self) -> bytes:
        fields = (self.origin, self.timescale, self.clock_standard, self.leap_policy)
        if any(not isinstance(field, str) or not field.strip() for field in fields):
            raise ValueError("all epoch semantic fields must be nonempty strings")
        return json.dumps({
            "clock_standard": self.clock_standard,
            "leap_policy": self.leap_policy,
            "origin": self.origin,
            "timescale": self.timescale,
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


class EpochRegistry:
    def __init__(self, namespace_id: bytes):
        if not isinstance(namespace_id, bytes) or len(namespace_id) != 16 or not any(namespace_id):
            raise ValueError("namespace must be a nonzero 16-byte value")
        self.namespace_id = namespace_id
        self._entries: dict[int, bytes] = {}

    def register(self, epoch_id: int, definition: EpochDefinition) -> bool:
        if not isinstance(epoch_id, int) or isinstance(epoch_id, bool) or not 1 <= epoch_id <= 0xFFFFFFFF:
            raise ValueError("epoch_id must be a nonzero uint32")
        canonical = definition.canonical()
        previous = self._entries.get(epoch_id)
        if previous is not None and previous != canonical:
            return False
        self._entries[epoch_id] = canonical
        return True

    def validate(self, namespace_id: bytes, epoch_id: int, definition: EpochDefinition) -> bool:
        return namespace_id == self.namespace_id and self._entries.get(epoch_id) == definition.canonical()

    def import_entries(self, namespace_id: bytes, entries: dict[int, EpochDefinition]) -> bool:
        """Atomic import; reject namespace mismatches or conflicting redefinition."""
        if namespace_id != self.namespace_id:
            return False
        staged = self._entries.copy()
        for epoch_id, definition in entries.items():
            if not isinstance(epoch_id, int) or isinstance(epoch_id, bool) or not 1 <= epoch_id <= 0xFFFFFFFF:
                return False
            canonical = definition.canonical()
            if epoch_id in staged and staged[epoch_id] != canonical:
                return False
            staged[epoch_id] = canonical
        self._entries = staged
        return True


def migrate_v1_without_authoritative_mapping(*_args: object) -> None:
    raise ValueError("v1 has no namespace; explicit trusted epoch mapping required")


if __name__ == "__main__":
    ns_a = bytes(range(1, 17))
    ns_b = bytes(range(1, 16)) + b'\x11'
    a = EpochDefinition("origin A", "ns", "monotonic", "not applicable")
    b = EpochDefinition("origin B", "ns", "monotonic", "not applicable")
    collided_id = 1781595200
    registry = EpochRegistry(ns_a)
    assert registry.register(collided_id, a)
    assert registry.register(collided_id, a)
    assert not registry.register(collided_id, b)
    assert registry.validate(ns_a, collided_id, a)
    assert not registry.validate(ns_b, collided_id, a)
    assert not registry.validate(ns_a, collided_id, b)
    assert not registry.import_entries(ns_b, {collided_id: a})
    assert not registry.import_entries(ns_a, {collided_id: b, 2: a})
    assert not registry.validate(ns_a, 2, a)  # failed import must be atomic
    assert registry.import_entries(ns_a, {2: a})
    assert registry.validate(ns_a, 2, a)
    for invalid in (b'', bytes(16), bytes(15), bytes(17)):
        try:
            EpochRegistry(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid namespace admitted")
    for invalid in (0, -1, 0x100000000, True):
        try:
            registry.register(invalid, a)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid epoch ID admitted")
    try:
        migrate_v1_without_authoritative_mapping(collided_id)
    except ValueError:
        pass
    else:
        raise AssertionError("untrusted v1 migration admitted")
    print("E476 registry contract: PASS (immutable conflicts, namespace isolation, atomic import, migration rejection)")
