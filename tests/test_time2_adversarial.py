"""E466: non-operational numerical precision boundary of two-component timestamps.

This test deliberately preserves negative exactness and strict-order results;
it does not imply a trajectory or physical timing accuracy claim.
"""
import ctypes
from fractions import Fraction
import math
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Timestamp(ctypes.Structure):
    _fields_ = [("hi", ctypes.c_double), ("lo", ctypes.c_double)]


def rational(t):
    return Fraction.from_float(t.hi) + Fraction.from_float(t.lo)


class AdversarialTime2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("gcc") or shutil.which("cc")
        if compiler is None:
            raise unittest.SkipTest("C compiler unavailable")
        cls.temp = tempfile.TemporaryDirectory()
        library = str(Path(cls.temp.name) / "libtime2.so")
        subprocess.run(
            [compiler, "-std=c11", "-O2", "-fPIC", "-shared", "-fno-fast-math",
             str(ROOT / "src/time2.c"), "-lm", "-o", library],
            check=True, capture_output=True,
        )
        cls.lib = ctypes.CDLL(library)
        cls.lib.bl_time2_make.argtypes = [ctypes.c_double, ctypes.c_double,
                                          ctypes.POINTER(Timestamp)]
        cls.lib.bl_time2_make.restype = ctypes.c_int
        cls.lib.bl_time2_add.argtypes = [Timestamp, Timestamp,
                                         ctypes.POINTER(Timestamp)]
        cls.lib.bl_time2_add.restype = ctypes.c_int
        cls.lib.bl_time2_compare.argtypes = [Timestamp, Timestamp]
        cls.lib.bl_time2_compare.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def make(self, hi, lo=0.0):
        result = Timestamp()
        self.assertEqual(self.lib.bl_time2_make(hi, lo, ctypes.byref(result)), 1)
        return result

    def add(self, a, b):
        result = Timestamp()
        self.assertEqual(self.lib.bl_time2_add(a, b, ctypes.byref(result)), 1)
        return result

    def test_positive_increment_below_low_component_resolution_stalls(self):
        base = self.make(float(2**53), 1.0)
        delta = self.make(2.0**-54)
        result = self.add(base, delta)
        self.assertGreater(rational(base) + rational(delta), rational(base))
        self.assertEqual(rational(result), rational(base))
        self.assertEqual(self.lib.bl_time2_compare(result, base), 0)

    def test_frozen_mixed_sign_non_power_of_two_cohort_is_not_exact(self):
        rng = random.Random(1465)
        total = inexact = rejects = order_failures = 0
        for _ in range(1024):
            exponent = rng.randrange(10, 101)
            start = math.ldexp(rng.uniform(1, 2), exponent)
            state = self.make(start)
            oracle = Fraction.from_float(start)
            for _ in range(16):
                k = rng.randrange(1, 105)
                scale = math.ldexp(1.0, exponent - k)
                delta = rng.choice([-1.0, 1.0]) * rng.uniform(0.5, 2.0) * scale
                if not math.isfinite(delta) or delta == 0:
                    continue
                result = Timestamp()
                status = self.lib.bl_time2_add(state, self.make(delta),
                                               ctypes.byref(result))
                total += 1
                if not status:
                    rejects += 1
                    continue
                oracle += Fraction.from_float(delta)
                inexact += rational(result) != oracle
                comparison = self.lib.bl_time2_compare(result, state)
                order_failures += (comparison > 0) != (delta > 0) or (
                    (comparison < 0) != (delta < 0)
                )
                state = result
        self.assertEqual((total, rejects, order_failures), (16384, 0, 0))
        self.assertGreater(inexact, 1000)


if __name__ == "__main__":
    unittest.main()
