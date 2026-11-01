"""E472: generic timestamp precision/range audit; no physical application."""
import ctypes
from fractions import Fraction
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NS = 1_000_000_000
I64_MAX = (1 << 63) - 1
YEAR_SECONDS = 365 * 24 * 60 * 60  # explicit 365-day model year

class Time2(ctypes.Structure):
    _fields_ = [("hi", ctypes.c_double), ("lo", ctypes.c_double)]

def exact(value):
    return Fraction.from_float(value.hi) + Fraction.from_float(value.lo)

def benchmark(compiler="gcc", seed=472, samples=4096):
    with tempfile.TemporaryDirectory() as directory:
        library = Path(directory) / "libtime2.so"
        subprocess.run([compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic", "-fno-fast-math", "-fPIC", "-shared", str(ROOT / "src/time2.c"), "-lm", "-o", str(library)], check=True, capture_output=True)
        lib = ctypes.CDLL(str(library))
        lib.bl_time2_make.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.POINTER(Time2)]
        lib.bl_time2_make.restype = ctypes.c_int
        lib.bl_time2_add_strict.argtypes = [Time2, Time2, ctypes.POINTER(Time2)]
        lib.bl_time2_add_strict.restype = ctypes.c_int

        def make_split(ticks):
            seconds, remainder = divmod(ticks, NS)
            result = Time2()
            assert lib.bl_time2_make(float(seconds), float(Fraction(remainder, NS)), ctypes.byref(result))
            return result

        def make_naive(ticks):
            result = Time2()
            assert lib.bl_time2_make(float(Fraction(ticks, NS)), 0.0, ctypes.byref(result))
            return result

        rng = random.Random(seed)
        horizon = 100 * YEAR_SECONDS * NS
        assert horizon <= I64_MAX
        metrics = {name: {"accepted": 0, "rejected": 0, "wrong_direction": 0, "inexact": 0, "max_abs_error_ns": 0.0} for name in ("split", "naive")}
        for _ in range(samples):
            start = rng.randrange(2 * NS, horizon - 2 * NS)
            delta = rng.choice((-1, 1)) * rng.randrange(1, NS + 1)
            target = start + delta
            assert 0 <= target <= horizon and target <= I64_MAX
            truth = Fraction(target, NS)
            for name, constructor in (("split", make_split), ("naive", make_naive)):
                a = constructor(start)
                step = constructor(delta)
                out = Time2(1234567.0, 0.0)
                ok = lib.bl_time2_add_strict(a, step, ctypes.byref(out))
                row = metrics[name]
                if not ok:
                    row["rejected"] += 1
                    assert out.hi == 1234567.0 and out.lo == 0.0
                    continue
                row["accepted"] += 1
                difference = exact(out) - exact(a)
                row["wrong_direction"] += (difference > 0) != (delta > 0)
                error_ns = abs(exact(out) - truth) * NS
                row["inexact"] += error_ns != 0
                row["max_abs_error_ns"] = max(row["max_abs_error_ns"], float(error_ns))
        assert all(row["wrong_direction"] == 0 for row in metrics.values())
        assert sum(row["accepted"] + row["rejected"] for row in metrics.values()) == samples * 2
        ranges = {unit: {"ticks_per_second": rate, "max_positive_years_365d": I64_MAX / (rate * YEAR_SECONDS), "fits_100_year_horizon": horizon // (NS // rate) <= I64_MAX} for unit, rate in (("seconds", 1), ("milliseconds", 1_000), ("microseconds", 1_000_000), ("nanoseconds", NS))}
        return {"compiler": compiler, "seed": seed, "samples": samples, "horizon_years": 100, "int64_nanosecond_ticks_exact": samples, "time2": metrics, "signed_int64_range": ranges, "serialized_bytes_int64": 8, "serialized_bytes_time2": ctypes.sizeof(Time2)}

if __name__ == "__main__":
    for compiler in sys.argv[1:] or ("gcc", "clang"):
        print(json.dumps(benchmark(compiler), sort_keys=True))
