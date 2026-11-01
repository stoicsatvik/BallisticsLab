"""E473 generic fixed-nanosecond timestamp C versus Python exact-int oracle."""
import ctypes
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src' / 'tickns.c'
NS = 10**9
MIN = -(1 << 63)
MAX = (1 << 63) - 1
YEAR = 365 * 24 * 3600

class Tick(ctypes.Structure):
    _fields_ = [('nanoseconds', ctypes.c_int64)]

def exercise(compiler, seed=473, count=16384):
    with tempfile.TemporaryDirectory() as td:
        so = Path(td) / 'libtickns.so'
        subprocess.run([compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic',
                        '-fPIC', '-shared',
                        str(SRC), '-o', str(so)], check=True, capture_output=True)
        lib = ctypes.CDLL(str(so))
        lib.bl_tickns_add.argtypes = [Tick, ctypes.c_int64, ctypes.POINTER(Tick)]
        lib.bl_tickns_add.restype = ctypes.c_int
        lib.bl_tickns_difference.argtypes = [Tick, Tick, ctypes.POINTER(ctypes.c_int64)]
        lib.bl_tickns_difference.restype = ctypes.c_int
        lib.bl_tickns_from_parts.argtypes = [ctypes.c_int64, ctypes.c_uint32, ctypes.POINTER(Tick)]
        lib.bl_tickns_from_parts.restype = ctypes.c_int
        lib.bl_tickns_to_parts.argtypes = [Tick, ctypes.POINTER(ctypes.c_int64), ctypes.POINTER(ctypes.c_uint32)]
        lib.bl_tickns_to_parts.restype = ctypes.c_int
        lib.bl_tickns_encode_be.argtypes = [Tick, ctypes.POINTER(ctypes.c_ubyte)]
        lib.bl_tickns_encode_be.restype = ctypes.c_int
        lib.bl_tickns_decode_be.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(Tick)]
        lib.bl_tickns_decode_be.restype = ctypes.c_int

        rng = random.Random(seed)
        edges = [MIN, MIN+1, -NS-1, -NS, -NS+1, -1, 0, 1, NS-1, NS, NS+1, MAX-1, MAX]
        samples = [(rng.randint(MIN, MAX), rng.randint(MIN, MAX)) for _ in range(count)]
        samples += [(a,b) for a in edges for b in edges]
        counts = {'cases':len(samples), 'add_accepted':0, 'add_rejected':0, 'diff_accepted':0, 'diff_rejected':0,
                  'roundtrips':0, 'mismatches':0}
        for a,b in samples:
            output = Tick(73)
            result = lib.bl_tickns_add(Tick(a), b, ctypes.byref(output))
            truth = a + b
            expected = MIN <= truth <= MAX
            assert bool(result) == expected and output.nanoseconds == (truth if expected else 73), (a,b,truth,result,output.nanoseconds)
            counts['add_accepted' if expected else 'add_rejected'] += 1

            diff = ctypes.c_int64(73)
            result = lib.bl_tickns_difference(Tick(a), Tick(b), ctypes.byref(diff))
            truth = a-b
            expected = MIN <= truth <= MAX
            assert bool(result) == expected and diff.value == (truth if expected else 73)
            counts['diff_accepted' if expected else 'diff_rejected'] += 1

            sec = ctypes.c_int64(73)
            nano = ctypes.c_uint32(73)
            assert lib.bl_tickns_to_parts(Tick(a), ctypes.byref(sec), ctypes.byref(nano))
            assert (sec.value, nano.value) == divmod(a, NS)
            rebuilt = Tick(73)
            assert lib.bl_tickns_from_parts(sec.value, nano.value, ctypes.byref(rebuilt))
            assert rebuilt.nanoseconds == a
            wire = (ctypes.c_ubyte * 8)()
            assert lib.bl_tickns_encode_be(Tick(a), wire)
            assert bytes(wire) == a.to_bytes(8, 'big', signed=True)
            decoded = Tick(73)
            assert lib.bl_tickns_decode_be(wire, ctypes.byref(decoded))
            assert decoded.nanoseconds == a
            counts['roundtrips'] += 1

        # Explicit out-of-range epochs and subsecond fields, with atomic failure.
        invalid = [(-9223372037, 145224191), (9223372036, 854775808), (0, NS), (MAX, 0), (MIN, 0)]
        for seconds, nano in invalid:
            out = Tick(73)
            assert not lib.bl_tickns_from_parts(seconds, nano, ctypes.byref(out)) and out.nanoseconds == 73
        assert 100 * YEAR * NS <= MAX < 300 * YEAR * NS
        return {'compiler':compiler,'seed':seed, **counts, 'invalid_parts_rejected':len(invalid),
                'horizon_100y_fits':True,'horizon_300y_fits':False}

if __name__ == '__main__':
    for compiler in sys.argv[1:] or ['gcc','clang']:
        print(json.dumps(exercise(compiler), sort_keys=True))
