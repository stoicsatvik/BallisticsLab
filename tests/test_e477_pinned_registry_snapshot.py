"""E477 deterministic tests and preserved negative control."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from e476_registry_contract import EpochDefinition, EpochRegistry
from e477_pinned_registry_snapshot import load_pinned, publish_once, sha256, snapshot_bytes

NS = bytes(range(1, 17))
A = EpochDefinition("2000-01-01", "nanoseconds", "monotonic", "none")
B = EpochDefinition("1999-01-01", "nanoseconds", "monotonic", "none")


def make_registry(entries=((7, A),)):
    registry = EpochRegistry(NS)
    for epoch_id, definition in entries:
        assert registry.register(epoch_id, definition)
    return registry


def raw(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


class PinnedSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.data = snapshot_bytes(make_registry())
        self.digest = sha256(self.data)

    def test_exact_round_trip(self):
        recovered = load_pinned(self.data, self.digest, NS)
        self.assertTrue(recovered.validate(NS, 7, A))
        self.assertEqual(snapshot_bytes(recovered), self.data)

    def test_byte_flip_rejected(self):
        damaged = bytearray(self.data)
        damaged[-5] ^= 1
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            load_pinned(bytes(damaged), self.digest, NS)

    def test_truncation_rejected(self):
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            load_pinned(self.data[:-1], self.digest, NS)

    def test_rollback_rejected_by_latest_pin(self):
        newer = snapshot_bytes(make_registry(((7, A), (8, B))))
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            load_pinned(self.data, sha256(newer), NS)

    def test_wrong_namespace_rejected(self):
        with self.assertRaisesRegex(ValueError, "namespace mismatch"):
            load_pinned(self.data, self.digest, bytes(range(2, 18)))

    def test_duplicate_json_keys_rejected_even_with_matching_hash(self):
        forged = self.data.replace(b'"format":', b'"format":"duplicate","format":')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            load_pinned(forged, sha256(forged), NS)

    def test_duplicate_ids_rejected_even_with_matching_hash(self):
        payload = json.loads(self.data)
        payload["entries"].append(payload["entries"][0])
        forged = raw(payload)
        with self.assertRaisesRegex(ValueError, "unique"):
            load_pinned(forged, sha256(forged), NS)

    def test_noncanonical_rejected_even_with_matching_hash(self):
        forged = json.dumps(json.loads(self.data), indent=2).encode("ascii")
        with self.assertRaisesRegex(ValueError, "noncanonical"):
            load_pinned(forged, sha256(forged), NS)

    def test_unsupported_format_rejected(self):
        payload = json.loads(self.data)
        payload["format"] = "unknown-v2"
        forged = raw(payload)
        with self.assertRaisesRegex(ValueError, "format"):
            load_pinned(forged, sha256(forged), NS)

    def test_atomic_publish_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "snapshot.json"
            publish_once(path, self.data)
            self.assertEqual(path.read_bytes(), self.data)
            with self.assertRaises(FileExistsError):
                publish_once(path, b"replacement")
            self.assertEqual(path.read_bytes(), self.data)
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_invalid_digest_rejected(self):
        with self.assertRaisesRegex(ValueError, "trusted digest"):
            load_pinned(self.data, "not-a-hash", NS)

    def test_negative_forged_snapshot_with_attacker_digest_passes(self):
        # Deliberate negative result: hash alone cannot authenticate issuer.
        forged = snapshot_bytes(make_registry(((7, B),)))
        self.assertFalse(load_pinned(forged, sha256(forged), NS).validate(NS, 7, A))
        self.assertTrue(load_pinned(forged, sha256(forged), NS).validate(NS, 7, B))
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            load_pinned(forged, self.digest, NS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
