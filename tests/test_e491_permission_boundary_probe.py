"""E491 synthetic owner/mode controls and hard-link provenance counterexample."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from e491_permission_boundary_probe import audit_local_permissions


@unittest.skipUnless(os.name == 'posix' and hasattr(os, 'O_NOFOLLOW')
                     and hasattr(os, 'O_DIRECTORY') and hasattr(os, 'O_NONBLOCK')
                     and os.open in os.supports_dir_fd, 'POSIX openat required')
class PermissionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'trusted'
        self.root.mkdir(mode=0o700)
        self.child = self.root / 'nested'
        self.child.mkdir(mode=0o700)
        self.file = self.child / 'checkpoint.json'
        self.file.write_bytes(b'not authenticated')
        self.file.chmod(0o600)
        self.uid = os.getuid()

    def audit(self, rel=Path('nested/checkpoint.json'), uid=None):
        return audit_local_permissions(self.root, rel, self.uid if uid is None else uid)

    def test_regular_owner_and_mode_consistent(self):
        result = self.audit()
        self.assertEqual(result.status, 'consistent')
        self.assertEqual(result.checked_components, 3)

    def test_group_writable_directory_rejected(self):
        self.child.chmod(0o770)
        self.assertEqual(self.audit().status, 'rejected')

    def test_world_writable_root_rejected(self):
        self.root.chmod(0o707)
        self.assertEqual(self.audit().status, 'rejected')

    def test_group_writable_file_rejected(self):
        self.file.chmod(0o660)
        self.assertEqual(self.audit().status, 'rejected')

    def test_mismatched_expected_owner_rejected(self):
        self.assertEqual(self.audit(uid=self.uid + 1).status, 'rejected')

    def test_symlinked_descendant_rejected(self):
        (self.root / 'alias').symlink_to(self.child, target_is_directory=True)
        self.assertEqual(self.audit(Path('alias/checkpoint.json')).status, 'inspection_error')

    def test_parent_traversal_rejected(self):
        self.assertEqual(self.audit(Path('nested/../nested/checkpoint.json')).status, 'inspection_error')

    def test_absent_file_inspection_error(self):
        self.assertEqual(self.audit(Path('nested/missing')).status, 'inspection_error')

    def test_external_hardlink_passes_but_cannot_prove_issuer(self):
        external = Path(self.temp.name) / 'external'
        external.write_bytes(b'created outside the caller chosen root')
        external.chmod(0o600)
        linked = self.child / 'external.json'
        os.link(external, linked)
        result = self.audit(Path('nested/external.json'))
        self.assertEqual(result.status, 'consistent')
        self.assertIn('issuer unverified', result.detail)
        self.assertEqual(external.stat().st_ino, linked.stat().st_ino)

    def test_absolute_path_rejected(self):
        self.assertEqual(self.audit(self.file).status, 'inspection_error')


if __name__ == '__main__':
    unittest.main(verbosity=2)
