"""E465: exact Fraction oracle for generic two-component timestamps.

No projectile, firearm, target or physical trajectory inputs.
"""
import ctypes
from fractions import Fraction
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Timestamp(ctypes.Structure):
    _fields_ = [("hi", ctypes.c_double), ("lo", ctypes.c_double)]


def value(t):
    return Fraction.from_float(t.hi) + Fraction.from_float(t.lo)


class Time2OracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cc = shutil.which("gcc") or shutil.which("cc")
        if not cc:
            raise unittest.SkipTest("C compiler unavailable")
        library = str(Path(cls.temp.name) / "libtime2.so")
        subprocess.run(
            [cc, "-std=c11", "-O2", "-fPIC", "-shared", "-fno-fast-math",
             str(ROOT / "src/time2.c"), "-lm", "-o", library],
            check=True, capture_output=True,
        )
        cls.lib = ctypes.CDLL(library)
        cls.lib.bl_time2_make.argtypes = [
            ctypes.c_double, ctypes.c_double, ctypes.POINTER(Timestamp)
        ]
        cls.lib.bl_time2_make.restype = ctypes.c_int
        cls.lib.bl_time2_add.argtypes = [
            Timestamp, Timestamp, ctypes.POINTER(Timestamp)
        ]
        cls.lib.bl_time2_add.restype = ctypes.c_int
        cls.lib.bl_time2_compare.argtypes = [Timestamp, Timestamp]
        cls.lib.bl_time2_compare.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def make(self, hi, lo=0.0):
        t = Timestamp()
        self.assertEqual(self.lib.bl_time2_make(hi, lo, ctypes.byref(t)), 1)
        return t

    def add(self, a, b):
        t = Timestamp()
        self.assertEqual(self.lib.bl_time2_add(a, b, ctypes.byref(t)), 1)
        return t

    def test_frozen_single_subulp_steps(self):
        rng = random.Random(465)
        exact = scalar_stalls = monotone = 0
        for _ in range(2048):
            exp = rng.randint(20, 100)
            base = float(2 ** exp)
            step = float(2 ** (exp - rng.randint(53, 100)))
            a, b = self.make(base), self.make(step)
            result = self.add(a, b)
            exact += value(result) == Fraction.from_float(base) + Fraction.from_float(step)
            scalar_stalls += base + step == base
            monotone += self.lib.bl_time2_compare(result, a) > 0
        self.assertEqual((exact, scalar_stalls, monotone), (2048, 2048, 2048))

    def test_frozen_positive_sequences(self):
        rng = random.Random(465)
        for _ in range(512):
            exp = rng.randint(20, 80)
            current = self.make(float(2 ** exp))
            oracle = value(current)
            for _ in range(16):
                step = float(2 ** (exp - rng.randint(53, 90)))
                nxt = self.add(current, self.make(step))
                self.assertGreater(self.lib.bl_time2_compare(nxt, current), 0)
                oracle += Fraction.from_float(step)
                current = nxt
            self.assertEqual(value(current), oracle)

    def test_admission_and_hex_roundtrip(self):
        a = self.make(float(2 ** 53), 1.0)
        restored = self.make(float.fromhex(a.hi.hex()), float.fromhex(a.lo.hex()))
        self.assertEqual(value(a), value(restored))
        self.assertGreater(self.lib.bl_time2_compare(a, self.make(float(2 ** 53))), 0)


if __name__ == "__main__":
    unittest.main()
