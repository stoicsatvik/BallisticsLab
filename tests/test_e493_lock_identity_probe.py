"""E493 synthetic POSIX lock counterexamples. All writes stay in temp dirs."""
import fcntl
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from e493_lock_identity_probe import inspect_lock_identity


def _lock_holder(lock_path: str, ready, release, exit_abruptly=False):
    """Spawn-safe lock holder; never touches repository/production paths."""
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        st = os.fstat(fd)
        ready.put((st.st_dev, st.st_ino))
        if not release.wait(5):
            raise RuntimeError('parent did not release synthetic holder')
        if exit_abruptly:
            os._exit(71)
    finally:
        os.close(fd)


@unittest.skipUnless(os.name == 'posix' and hasattr(fcntl, 'flock'), 'POSIX flock required')
class LockIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.lock = self.root / 'writer.lock'
        self.lock.write_bytes(b'')

    def open_fd(self):
        fd = os.open(self.lock, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        self.addCleanup(os.close, fd)
        return fd

    def holder(self, abrupt=False):
        ctx = multiprocessing.get_context('spawn')
        ready, release = ctx.Queue(), ctx.Event()
        process = ctx.Process(target=_lock_holder, args=(str(self.lock), ready, release, abrupt))
        process.start()
        self.addCleanup(self._stop_holder, process, release)
        inode = ready.get(timeout=8)
        return process, release, inode

    @staticmethod
    def _stop_holder(process, release):
        release.set()
        process.join(timeout=8)
        if process.is_alive():
            process.terminate()
            process.join(timeout=8)

    def test_matching_descriptor_is_only_instantaneous(self):
        result = inspect_lock_identity(self.open_fd(), self.lock)
        self.assertEqual(result.status, 'same_inode')
        self.assertIn('writers and races unverified', result.detail)

    def test_path_replaced_with_new_regular_inode(self):
        fd = self.open_fd()
        os.replace(self.lock, self.root / 'old.lock')
        self.lock.write_bytes(b'')
        result = inspect_lock_identity(fd, self.lock)
        self.assertEqual(result.status, 'replaced')
        self.assertNotEqual(result.descriptor_inode, result.pathname_inode)

    def test_path_replaced_with_symlink(self):
        fd = self.open_fd()
        old = self.root / 'old.lock'
        os.replace(self.lock, old)
        self.lock.symlink_to(old)
        self.assertEqual(inspect_lock_identity(fd, self.lock).status, 'replaced')

    def test_absent_path_and_invalid_fd_fail_closed(self):
        fd = self.open_fd()
        self.lock.unlink()
        self.assertEqual(inspect_lock_identity(fd, self.lock).status, 'inspection_error')
        self.assertEqual(inspect_lock_identity(-1, self.lock).status, 'inspection_error')
        self.assertEqual(inspect_lock_identity(True, self.lock).status, 'inspection_error')

    def test_directory_path_rejected(self):
        fd = self.open_fd()
        os.replace(self.lock, self.root / 'old.lock')
        self.lock.mkdir()
        self.assertEqual(inspect_lock_identity(fd, self.lock).status, 'replaced')

    def test_cooperating_second_process_cannot_take_held_inode(self):
        process, release, _ = self.holder()
        fd = os.open(self.lock, os.O_RDWR)
        try:
            with self.assertRaises(BlockingIOError):
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(fd)
        release.set()
        process.join(timeout=8)
        self.assertEqual(process.exitcode, 0)

    def test_uncooperative_writer_bypasses_advisory_lock(self):
        process, release, _ = self.holder()
        # This writer does not participate in flock; it can modify the
        # locked inode despite the other process holding LOCK_EX.
        self.lock.write_bytes(b'uncooperative mutation')
        self.assertEqual(self.lock.read_bytes(), b'uncooperative mutation')
        release.set()
        process.join(timeout=8)
        self.assertEqual(process.exitcode, 0)

    def test_replaced_lockfile_allows_two_simultaneous_exclusive_locks(self):
        process, release, old_inode = self.holder()
        old_path = self.root / 'old.lock'
        os.replace(self.lock, old_path)
        self.lock.write_bytes(b'')
        new_fd = os.open(self.lock, os.O_RDWR)
        try:
            fcntl.flock(new_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            new_stat = os.fstat(new_fd)
            self.assertNotEqual(old_inode, (new_stat.st_dev, new_stat.st_ino))
            # The old holder is still alive while a second exclusive lock
            # succeeds on the same pathname's replacement inode.
            self.assertTrue(process.is_alive())
        finally:
            fcntl.flock(new_fd, fcntl.LOCK_UN)
            os.close(new_fd)
            release.set()
        process.join(timeout=8)
        self.assertEqual(process.exitcode, 0)

    def test_abrupt_holder_exit_releases_kernel_lock_not_writer_quiescence(self):
        process, release, _ = self.holder(abrupt=True)
        release.set()
        process.join(timeout=8)
        self.assertEqual(process.exitcode, 71)
        fd = os.open(self.lock, os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


if __name__ == '__main__':
    unittest.main(verbosity=2)
