"""E474 generic epoch-tagged nanosecond wire format versus Python byte oracle."""
import ctypes
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MIN = -(1 << 63)
MAX = (1 << 63) - 1

class Tick(ctypes.Structure):
    _fields_ = [('nanoseconds', ctypes.c_int64)]

class EpochTick(ctypes.Structure):
    _fields_ = [('tick', Tick), ('epoch_id', ctypes.c_uint32)]

Wire = ctypes.c_ubyte * 16

def exercise(compiler, seed=474, count=4096):
    with tempfile.TemporaryDirectory() as td:
        so = Path(td) / 'libepoch.so'
        subprocess.run([compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic',
                        '-fPIC', '-shared', '-I' + str(ROOT / 'src'),
                        str(ROOT / 'src' / 'tickns.c'), str(ROOT / 'src' / 'tickns_epoch.c'),
                        '-o', str(so)], check=True, capture_output=True)
        lib = ctypes.CDLL(str(so))
        lib.bl_epoch_tickns_add.argtypes = [EpochTick, ctypes.c_int64, ctypes.POINTER(EpochTick)]
        lib.bl_epoch_tickns_add.restype = ctypes.c_int
        lib.bl_epoch_tickns_difference.argtypes = [EpochTick, EpochTick, ctypes.POINTER(ctypes.c_int64)]
        lib.bl_epoch_tickns_difference.restype = ctypes.c_int
        lib.bl_epoch_tickns_encode.argtypes = [EpochTick, ctypes.POINTER(ctypes.c_ubyte)]
        lib.bl_epoch_tickns_encode.restype = ctypes.c_int
        lib.bl_epoch_tickns_decode.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32,
                                               ctypes.POINTER(EpochTick)]
        lib.bl_epoch_tickns_decode.restype = ctypes.c_int
        rng = random.Random(seed)
        edges = [MIN, MIN + 1, -1000000001, -1000000000, -1, 0, 1,
                 1000000000, 1000000001, MAX - 1, MAX]
        samples = [(rng.randint(MIN, MAX), rng.randint(MIN, MAX)) for _ in range(count)]
        samples += [(a, b) for a in edges for b in edges]
        counts = {'cases': len(samples), 'wire_roundtrips': 0, 'add_accepted': 0,
                  'add_rejected': 0, 'diff_accepted': 0, 'diff_rejected': 0,
                  'cross_epoch_rejected': 0, 'malformed_header_rejected': 0,
                  'oracle_mismatches': 0}
        for a, b in samples:
            epoch = rng.randint(1, 0xFFFFFFFF)
            other = 1 if epoch != 1 else 2
            value = EpochTick(Tick(a), epoch)
            wire = Wire()
            assert lib.bl_epoch_tickns_encode(value, wire)
            expected_wire = b'BT\x01\x01' + epoch.to_bytes(4, 'big') + a.to_bytes(8, 'big', signed=True)
            assert bytes(wire) == expected_wire
            decoded = EpochTick(Tick(73), 73)
            assert lib.bl_epoch_tickns_decode(wire, epoch, ctypes.byref(decoded))
            assert decoded.tick.nanoseconds == a and decoded.epoch_id == epoch
            decoded = EpochTick(Tick(73), 73)
            assert not lib.bl_epoch_tickns_decode(wire, other, ctypes.byref(decoded))
            assert decoded.tick.nanoseconds == 73 and decoded.epoch_id == 73
            counts['cross_epoch_rejected'] += 1
            counts['wire_roundtrips'] += 1

            output = EpochTick(Tick(73), 73)
            ok = lib.bl_epoch_tickns_add(value, b, ctypes.byref(output))
            truth = a + b
            accepted = MIN <= truth <= MAX
            assert bool(ok) == accepted
            assert (output.tick.nanoseconds, output.epoch_id) == ((truth, epoch) if accepted else (73, 73))
            counts['add_accepted' if accepted else 'add_rejected'] += 1

            difference = ctypes.c_int64(73)
            ok = lib.bl_epoch_tickns_difference(value, EpochTick(Tick(b), epoch), ctypes.byref(difference))
            truth = a - b
            accepted = MIN <= truth <= MAX
            assert bool(ok) == accepted
            assert difference.value == (truth if accepted else 73)
            counts['diff_accepted' if accepted else 'diff_rejected'] += 1
            difference.value = 73
            assert not lib.bl_epoch_tickns_difference(value, EpochTick(Tick(b), other),
                                                       ctypes.byref(difference))
            assert difference.value == 73
            counts['cross_epoch_rejected'] += 1

            if counts['malformed_header_rejected'] < 12:
                for position in (0, 1, 2, 3):
                    damaged = Wire.from_buffer_copy(expected_wire)
                    damaged[position] ^= 1
                    output = EpochTick(Tick(73), 73)
                    assert not lib.bl_epoch_tickns_decode(damaged, epoch, ctypes.byref(output))
                    assert output.tick.nanoseconds == 73 and output.epoch_id == 73
                    counts['malformed_header_rejected'] += 1

        # Deliberate negative control: payload corruption is *not* detected by this
        # envelope. This format is a semantic tag, not a checksum or authentication.
        wire = Wire.from_buffer_copy(b'BT\x01\x01' + (42).to_bytes(4, 'big') + (1).to_bytes(8, 'big', signed=True))
        wire[15] ^= 1
        decoded = EpochTick(Tick(73), 73)
        assert lib.bl_epoch_tickns_decode(wire, 42, ctypes.byref(decoded))
        assert decoded.tick.nanoseconds == 0
        return {'compiler': compiler, 'seed': seed, **counts,
                'undetected_payload_mutation': True, 'wire_bytes': 16}

if __name__ == '__main__':
    for compiler in sys.argv[1:] or ['gcc', 'clang']:
        print(json.dumps(exercise(compiler), sort_keys=True))
