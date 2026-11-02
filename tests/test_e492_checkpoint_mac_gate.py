"""Synthetic MAC, replay, hard-link and attacker-chosen-key negative controls."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from e492_checkpoint_mac_gate import issue_test_mac, verify_test_mac, MAX_SNAPSHOT_BYTES


class CheckpointMacTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = b'{"synthetic":"not a trusted registry snapshot"}'
        self.ns = bytes.fromhex('1234567890abcdef1234567890abcdef')
        self.key = b'issuer test key ' + b'K' * 32
        self.mac = issue_test_mac(self.snapshot, self.ns, 7, self.key)

    def verify(self, snapshot=None, mac=None, ns=None, key=None, floor=7):
        return verify_test_mac(self.snapshot if snapshot is None else snapshot,
                               self.mac if mac is None else mac,
                               self.ns if ns is None else ns,
                               self.key if key is None else key, floor)

    def test_synthetic_round_trip(self):
        result = self.verify()
        self.assertEqual(result.status, 'mac_valid')
        self.assertEqual(result.generation, 7)
        self.assertIn('issuer', result.detail)

    def test_snapshot_tampering_rejected(self):
        self.assertEqual(self.verify(snapshot=self.snapshot + b' ').status, 'rejected')

    def test_mac_tampering_rejected(self):
        obj = json.loads(self.mac)
        obj['mac'] = '0' * 64 if obj['mac'] != '0' * 64 else '1' * 64
        forged = json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(self.verify(mac=forged).status, 'rejected')

    def test_wrong_trusted_secret_rejected(self):
        self.assertEqual(self.verify(key=b'Z' * 32).status, 'rejected')

    def test_wrong_namespace_rejected(self):
        self.assertEqual(self.verify(ns=b'Q' * 16).status, 'rejected')

    def test_rollback_rejected_with_trusted_floor(self):
        self.assertEqual(self.verify(floor=8).status, 'rejected')
        self.assertEqual(self.verify(floor=7).status, 'mac_valid')

    def test_rollback_not_prevented_with_reset_floor(self):
        self.assertEqual(self.verify(floor=0).status, 'mac_valid')

    def test_noncanonical_json_rejected(self):
        self.assertEqual(self.verify(mac=self.mac.replace(b',', b', ', 1)).status, 'rejected')

    def test_duplicate_keys_rejected(self):
        malformed = self.mac[:-1] + b',"mac":"' + b'0' * 64 + b'"}'
        self.assertEqual(self.verify(mac=malformed).status, 'inspection_error')

    def test_extra_fields_rejected(self):
        obj = json.loads(self.mac)
        obj['issuer'] = 'self-asserted'
        self.assertEqual(self.verify(mac=json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).status, 'rejected')

    def test_bool_generation_rejected(self):
        with self.assertRaises(ValueError):
            issue_test_mac(self.snapshot, self.ns, True, self.key)

    def test_weak_key_rejected(self):
        with self.assertRaises(ValueError):
            issue_test_mac(self.snapshot, self.ns, 7, b'short')
        self.assertEqual(self.verify(key=b'short').status, 'inspection_error')

    def test_invalid_namespace_rejected(self):
        with self.assertRaises(ValueError):
            issue_test_mac(self.snapshot, b'\0' * 16, 7, self.key)

    def test_snapshot_size_cap(self):
        self.assertEqual(self.verify(snapshot=b'x' * (MAX_SNAPSHOT_BYTES + 1)).status, 'inspection_error')

    def test_attacker_chosen_secret_does_not_authenticate(self):
        attacker = b'A' * 32
        forged = issue_test_mac(self.snapshot, self.ns, 7, attacker)
        self.assertEqual(self.verify(mac=forged).status, 'rejected')
        # If the verifier accepts the attacker's key, the same forgery succeeds.
        self.assertEqual(self.verify(mac=forged, key=attacker).status, 'mac_valid')

    @unittest.skipUnless(hasattr(os, 'link'), 'hard links required')
    def test_unsigned_external_hardlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            outside = Path(td) / 'outside'
            inside = Path(td) / 'inside'
            outside.write_bytes(b'untrusted external snapshot')
            os.link(outside, inside)
            self.assertEqual(inside.stat().st_ino, outside.stat().st_ino)
            self.assertEqual(self.verify(snapshot=inside.read_bytes()).status, 'rejected')

    @unittest.skipUnless(hasattr(os, 'link'), 'hard links required')
    def test_valid_signed_hardlink_still_lacks_path_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            outside = Path(td) / 'outside'
            inside = Path(td) / 'inside'
            outside.write_bytes(self.snapshot)
            os.link(outside, inside)
            self.assertEqual(self.verify(snapshot=inside.read_bytes()).status, 'mac_valid')
            self.assertEqual(inside.stat().st_ino, outside.stat().st_ino)


if __name__ == '__main__':
    unittest.main(verbosity=2)
