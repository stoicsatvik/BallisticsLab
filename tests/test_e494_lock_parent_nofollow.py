"""E494: lock identity must reject symlinked ancestors; hard links remain a gap."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from e493_lock_identity_probe import inspect_lock_identity


@unittest.skipUnless(os.name == 'posix' and hasattr(os, 'O_NOFOLLOW')
                     and hasattr(os, 'O_DIRECTORY') and os.open in os.supports_dir_fd,
                     'descriptor-relative POSIX no-follow required')
class ParentNoFollowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lock = self.root / 'writer.lock'
        self.lock.write_bytes(b'')
        self.fd = os.open(self.lock, os.O_RDONLY | os.O_NOFOLLOW)
        self.addCleanup(os.close, self.fd)

    def test_immediate_parent_symlink_same_inode_is_rejected(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        # E493's lstat(path) traversed the symlink and returned same_inode.
        self.assertEqual(os.lstat(alias / 'writer.lock').st_ino, os.fstat(self.fd).st_ino)
        self.assertEqual(inspect_lock_identity(self.fd, alias / 'writer.lock').status,
                         'inspection_error')

    def test_ancestor_symlink_same_inode_is_rejected(self):
        parent = self.root / 'parent'
        parent.mkdir()
        (parent / 'alias').symlink_to(self.root, target_is_directory=True)
        self.assertEqual(inspect_lock_identity(self.fd, parent / 'alias' / 'writer.lock').status,
                         'inspection_error')

    def test_parent_traversal_fails_closed(self):
        self.assertEqual(inspect_lock_identity(self.fd, self.root / 'x' / '..' / 'writer.lock').status,
                         'inspection_error')

    def test_hardlink_still_indistinguishable_from_original(self):
        alias = self.root / 'alias.lock'
        os.link(self.lock, alias)
        result = inspect_lock_identity(self.fd, alias)
        self.assertEqual(result.status, 'same_inode')
        self.assertIn('races unverified', result.detail)

    def test_fifo_path_is_rejected_without_blocking(self):
        fifo = self.root / 'pipe.lock'
        os.mkfifo(fifo)
        self.assertEqual(inspect_lock_identity(self.fd, fifo).status, 'replaced')


if __name__ == '__main__':
    unittest.main(verbosity=2)
