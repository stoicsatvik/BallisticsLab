"""E484 research-only fault injection for E477 POSIX snapshot publication."""
import errno
import os
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from e476_registry_contract import EpochDefinition, EpochRegistry
from e477_pinned_registry_snapshot import load_pinned, publish_once, sha256, snapshot_bytes

NS = bytes(range(1, 17))


def valid_data():
    registry = EpochRegistry(NS)
    assert registry.register(7, EpochDefinition("2000-01-01", "nanoseconds", "monotonic", "none"))
    return snapshot_bytes(registry)


@unittest.skipUnless(os.name == "posix" and hasattr(os, "link"), "POSIX local hard links required")
class PublicationFaultTests(unittest.TestCase):
    def setUp(self):
        self.data = valid_data()

    def test_concurrent_eight_writers_exactly_one_wins(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "snapshot.json"
            barrier = threading.Barrier(8)
            def attempt(index):
                barrier.wait(timeout=10)
                try:
                    publish_once(target, self.data + bytes([index]))
                    return ("winner", index)
                except FileExistsError:
                    return ("lost", index)
            with ThreadPoolExecutor(max_workers=8) as pool:
                outcomes = list(pool.map(attempt, range(8)))
            winners = [index for status, index in outcomes if status == "winner"]
            self.assertEqual(len(winners), 1)
            self.assertEqual(target.read_bytes(), self.data + bytes(winners))
            self.assertEqual([p.name for p in Path(folder).iterdir()], ["snapshot.json"])

    def test_file_fsync_failure_prevents_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "snapshot.json"
            with patch("e477_pinned_registry_snapshot.os.fsync", side_effect=OSError(errno.EIO, "file fsync failed")):
                with self.assertRaises(OSError):
                    publish_once(target, self.data)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_hardlink_failure_prevents_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "snapshot.json"
            with patch("e477_pinned_registry_snapshot.os.link", side_effect=OSError(errno.EIO, "link failed")):
                with self.assertRaises(OSError):
                    publish_once(target, self.data)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(folder).iterdir()), [])

    @unittest.skipUnless(hasattr(os, "O_DIRECTORY"), "directory fsync requires O_DIRECTORY")
    def test_directory_fsync_failure_is_indeterminate_not_rollback(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "snapshot.json"
            real_fsync = os.fsync
            calls = 0
            def fail_second_fsync(fd):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError(errno.EIO, "directory fsync failed")
                return real_fsync(fd)
            with patch("e477_pinned_registry_snapshot.os.fsync", side_effect=fail_second_fsync):
                with self.assertRaises(OSError):
                    publish_once(target, self.data)
            self.assertEqual(calls, 2)
            # Negative result: a raised exception does not imply no publication.
            self.assertEqual(target.read_bytes(), self.data)
            self.assertEqual(list(Path(folder).iterdir()), [target])
            self.assertEqual(snapshot_bytes(load_pinned(target.read_bytes(), sha256(self.data), NS)), self.data)

    def test_existing_target_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "snapshot.json"
            target.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                publish_once(target, self.data)
            self.assertEqual(target.read_bytes(), b"existing")
            self.assertEqual(list(Path(folder).iterdir()), [target])

    def test_invalid_data_does_not_create_temp_or_target(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "snapshot.json"
            with self.assertRaises(ValueError):
                publish_once(target, b"x" * (1_048_576 + 1))
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
