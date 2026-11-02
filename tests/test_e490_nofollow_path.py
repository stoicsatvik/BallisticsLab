"""E490: POSIX path-component symlink rejection and inode/path drift controls."""
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from e476_registry_contract import EpochDefinition, EpochRegistry
from e477_pinned_registry_snapshot import sha256, snapshot_bytes
from e487_publication_recovery_probe import ProbeState, probe_snapshot
from e490_nofollow_path import open_snapshot_nofollow


@unittest.skipUnless(
    os.name == "posix" and hasattr(os, "O_DIRECTORY")
    and hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_NONBLOCK")
    and os.open in os.supports_dir_fd,
    "POSIX descriptor-relative no-follow open required",
)
class NoFollowPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.nested = self.root / "parent" / "nested"
        self.nested.mkdir(parents=True)
        self.target = self.nested / "snapshot.json"
        self.target.write_bytes(b"test snapshot bytes")

    def read(self, path):
        with os.fdopen(open_snapshot_nofollow(path), "rb") as handle:
            return handle.read()

    def test_regular_nested_path(self):
        self.assertEqual(self.read(self.target), b"test snapshot bytes")

    def test_symlinked_immediate_parent_rejected(self):
        (self.root / "alias").symlink_to(self.nested, target_is_directory=True)
        with self.assertRaises(OSError):
            self.read(self.root / "alias" / "snapshot.json")

    def test_symlinked_ancestor_rejected(self):
        (self.root / "alias").symlink_to(self.root / "parent", target_is_directory=True)
        with self.assertRaises(OSError):
            self.read(self.root / "alias" / "nested" / "snapshot.json")

    def test_final_symlink_rejected(self):
        (self.root / "alias").symlink_to(self.target)
        with self.assertRaises(OSError):
            self.read(self.root / "alias")

    def test_parent_traversal_rejected(self):
        with self.assertRaises(ValueError):
            self.read(self.nested / ".." / "nested" / "snapshot.json")

    def test_absent_file_remains_absent(self):
        with self.assertRaises(FileNotFoundError):
            self.read(self.nested / "missing.json")

    def test_directory_root_not_a_file(self):
        with self.assertRaises(ValueError):
            self.read(Path("/"))

    def test_fifo_open_is_nonblocking_and_caller_can_reject_type(self):
        fifo = self.root / "fifo"
        os.mkfifo(fifo)
        with os.fdopen(open_snapshot_nofollow(fifo), "rb") as handle:
            self.assertTrue(stat.S_ISFIFO(os.fstat(handle.fileno()).st_mode))

    def test_opened_inode_can_outlive_pathname_replacement(self):
        fd = open_snapshot_nofollow(self.target)
        try:
            self.target.rename(self.nested / "previous.json")
            self.target.write_bytes(b"replacement")
            with os.fdopen(fd, "rb") as handle:
                fd = -1
                self.assertEqual(handle.read(), b"test snapshot bytes")
            self.assertEqual(self.target.read_bytes(), b"replacement")
        finally:
            if fd != -1:
                os.close(fd)

    def test_probe_rejects_symlinked_parent(self):
        registry = EpochRegistry(bytes(range(1, 17)))
        self.assertTrue(registry.register(
            7, EpochDefinition("origin", "nanoseconds", "monotonic", "none")))
        data = snapshot_bytes(registry)
        self.target.write_bytes(data)
        (self.root / "alias").symlink_to(self.nested, target_is_directory=True)
        result = probe_snapshot(self.root / "alias" / "snapshot.json",
                                sha256(data), bytes(range(1, 17)))
        self.assertEqual(result.state, ProbeState.INSPECTION_ERROR)
        self.assertTrue(self.target.exists())

    def test_probe_keeps_valid_direct_path(self):
        namespace = bytes(range(1, 17))
        registry = EpochRegistry(namespace)
        self.assertTrue(registry.register(
            7, EpochDefinition("origin", "nanoseconds", "monotonic", "none")))
        data = snapshot_bytes(registry)
        self.target.write_bytes(data)
        result = probe_snapshot(self.target, sha256(data), namespace)
        self.assertEqual(result.state,
                         ProbeState.VISIBLE_PIN_VALID_DURABILITY_UNKNOWN)


if __name__ == "__main__":
    unittest.main(verbosity=2)
