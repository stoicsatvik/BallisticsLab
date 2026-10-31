"""Frozen E429 numerical-boundary controls for two-component timestamps."""
import math
import unittest
from fractions import Fraction

from research.e445_two_component_event_time import event_state, run, split_time


class TwoComponentEventTimeTest(unittest.TestCase):
    def test_exact_subulp_recovery(self):
        state = event_state(50, 15, 1)
        self.assertIsNotNone(state)
        t, _, _, tau, _ = state
        self.assertEqual(t + tau, t)
        hi, lo = split_time(t, tau)
        self.assertEqual(hi, t)
        self.assertGreater(lo, 0)
        self.assertEqual(Fraction(hi)+Fraction(lo), Fraction(t)+Fraction(tau))

    def test_exact_non_subulp_recovery(self):
        state = event_state(1, 45, 8)
        self.assertIsNotNone(state)
        t, _, _, tau, _ = state
        hi, lo = split_time(t, tau)
        self.assertEqual(hi, t+tau)
        self.assertEqual(Fraction(hi)+Fraction(lo), Fraction(t)+Fraction(tau))

    def test_hex_roundtrip(self):
        t, _, _, tau, _ = event_state(100, 15, 2)
        hi, lo = split_time(t, tau)
        self.assertEqual((float.fromhex(hi.hex()), float.fromhex(lo.hex())), (hi, lo))

    def test_invalid_input_rejected(self):
        for t, tau in [(0, 0), (0, -1), (math.inf, 1), (0, math.nan)]:
            with self.assertRaises(ValueError):
                split_time(t, tau)

    def test_full_frozen_grid(self):
        result = run()
        self.assertEqual(result["baseline_counts"], {"accepted": 1070,
                           "exact_zero": 6, "subulp_reject": 4})
        self.assertEqual(result["positive_crossings"], 1074)
        self.assertEqual(result["max_pair_roundtrip_error_ulp"], 0)
        self.assertEqual(len(result["subulp_cases"]), 4)
        self.assertEqual(result["two_component_nonmonotone"], 0)


if __name__ == "__main__":
    unittest.main()
