"""E487: read-only diagnostic and negative crash/publication-state controls."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from e476_registry_contract import EpochDefinition, EpochRegistry
from e477_pinned_registry_snapshot import MAX_BYTES, publish_once, sha256, snapshot_bytes
from e487_publication_recovery_probe import ProbeState, probe_snapshot

NS = bytes(range(1, 17))


def payload():
    registry = EpochRegistry(NS)
    assert registry.register(7, EpochDefinition("origin", "nanoseconds", "monotonic", "none"))
    return snapshot_bytes(registry)


@unittest.skipUnless(os.name == "posix" and hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_NONBLOCK"),
                     "POSIX no-follow and nonblocking open required")
class RecoveryProbeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "snapshot.json"
        self.data = payload()
        self.pin = sha256(self.data)

    def probe(self, pin=None, namespace=None):
        return probe_snapshot(self.path, pin, namespace)

    def test_absent_destination_is_not_publication_success(self):
        self.assertEqual(self.probe(self.pin, NS).state, ProbeState.ABSENT)

    def test_visible_without_pin_remains_unverified(self):
        self.path.write_bytes(self.data)
        result = self.probe()
        self.assertEqual(result.state, ProbeState.VISIBLE_UNVERIFIED)
        self.assertIsNone(result.observed_sha256)

    def test_valid_pin_does_not_claim_durability_or_issuer_authenticity(self):
        publish_once(self.path, self.data)
        result = self.probe(self.pin, NS)
        self.assertEqual(result.state, ProbeState.VISIBLE_PIN_VALID_DURABILITY_UNKNOWN)
        self.assertEqual(result.observed_sha256, self.pin)
        self.assertEqual(result.size, len(self.data))

    def test_wrong_digest_rejected(self):
        self.path.write_bytes(self.data)
        self.assertEqual(self.probe("0" * 64, NS).state, ProbeState.VISIBLE_PIN_REJECTED)

    def test_wrong_namespace_rejected(self):
        self.path.write_bytes(self.data)
        self.assertEqual(self.probe(self.pin, bytes(range(2, 18))).state,
                         ProbeState.VISIBLE_PIN_REJECTED)

    def test_malformed_content_rejected_even_under_its_own_digest(self):
        malformed = b'{"not":"a registry"}'
        self.path.write_bytes(malformed)
        self.assertEqual(self.probe(sha256(malformed), NS).state,
                         ProbeState.VISIBLE_PIN_REJECTED)

    def test_attacker_supplied_digest_still_passes_for_forged_valid_snapshot(self):
        forged_registry = EpochRegistry(NS)
        assert forged_registry.register(7, EpochDefinition("forged-origin", "nanoseconds", "monotonic", "none"))
        forged = snapshot_bytes(forged_registry)
        self.path.write_bytes(forged)
        self.assertEqual(self.probe(sha256(forged), NS).state,
                         ProbeState.VISIBLE_PIN_VALID_DURABILITY_UNKNOWN)
        self.assertEqual(self.probe(self.pin, NS).state,
                         ProbeState.VISIBLE_PIN_REJECTED)

    def test_partial_pin_is_inspection_error_not_unverified_success(self):
        self.path.write_bytes(self.data)
        self.assertEqual(self.probe(self.pin).state, ProbeState.INSPECTION_ERROR)
        self.assertEqual(self.probe(None, NS).state, ProbeState.INSPECTION_ERROR)

    def test_symlink_rejected_without_following(self):
        other = Path(self.folder.name) / "other.json"
        other.write_bytes(self.data)
        self.path.symlink_to(other)
        self.assertEqual(self.probe(self.pin, NS).state, ProbeState.INSPECTION_ERROR)

    def test_fifo_rejected_without_blocking(self):
        os.mkfifo(self.path)
        self.assertEqual(self.probe(self.pin, NS).state, ProbeState.INSPECTION_ERROR)

    def test_oversize_rejected_without_loading(self):
        with self.path.open("wb") as handle:
            handle.truncate(MAX_BYTES + 1)
        self.assertEqual(self.probe(self.pin, NS).state, ProbeState.VISIBLE_PIN_REJECTED)

    def test_post_link_fsync_failure_is_visible_but_durability_unknown(self):
        real_fsync = os.fsync
        calls = 0
        def fail_directory_sync(fd):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected post-link directory fsync failure")
            return real_fsync(fd)
        with patch("e477_pinned_registry_snapshot.os.fsync", side_effect=fail_directory_sync):
            with self.assertRaisesRegex(OSError, "injected"):
                publish_once(self.path, self.data)
        self.assertEqual(self.probe(self.pin, NS).state,
                         ProbeState.VISIBLE_PIN_VALID_DURABILITY_UNKNOWN)

    def test_orphan_temp_is_not_deleted_or_promoted(self):
        orphan = Path(self.folder.name) / ".e477-orphan"
        orphan.write_bytes(self.data)
        self.assertEqual(self.probe(self.pin, NS).state, ProbeState.ABSENT)
        self.assertTrue(orphan.exists())
        os.link(orphan, self.path)  # models after-link visibility without cleanup
        self.assertEqual(self.probe(self.pin, NS).state,
                         ProbeState.VISIBLE_PIN_VALID_DURABILITY_UNKNOWN)
        self.assertTrue(orphan.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
