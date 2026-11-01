"""Frozen E471 signed-step representability audit. No physical/weapon application."""
import ctypes
from fractions import Fraction
import math
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
class T(ctypes.Structure):
    _fields_ = [("hi", ctypes.c_double), ("lo", ctypes.c_double)]

def val(x):
    return Fraction.from_float(x.hi) + Fraction.from_float(x.lo)

def audit(compiler):
    with tempfile.TemporaryDirectory() as d:
        so = Path(d)/"libtime2.so"
        subprocess.run([compiler,"-std=c11","-O2","-Wall","-Wextra","-Werror","-pedantic","-fno-fast-math","-fPIC","-shared",str(ROOT/"src/time2.c"),"-lm","-o",str(so)],check=True)
        lib=ctypes.CDLL(str(so))
        lib.bl_time2_make.argtypes=[ctypes.c_double,ctypes.c_double,ctypes.POINTER(T)]
        lib.bl_time2_make.restype=ctypes.c_int
        lib.bl_time2_add_strict.argtypes=[T,T,ctypes.POINTER(T)]
        lib.bl_time2_add_strict.restype=ctypes.c_int
        lib.bl_time2_compare.argtypes=[T,T]
        lib.bl_time2_compare.restype=ctypes.c_int
        def make(x):
            t=T()
            assert lib.bl_time2_make(x,0,ctypes.byref(t))
            return t
        rng=random.Random(1471)
        total=accepted=rejected=inexact=wrong_direction=untouched_fail=0
        for _ in range(1024):
            exponent=rng.randrange(10,101)
            start=math.ldexp(rng.uniform(1,2),exponent)
            state=make(start)
            for _ in range(16):
                k=rng.randrange(1,105)
                delta=rng.choice([-1.,1.])*rng.uniform(0.5,2.0)*math.ldexp(1.0,exponent-k)
                if not math.isfinite(delta) or delta==0: continue
                step=make(delta)
                out=T(1234567.0,0.0)
                status=lib.bl_time2_add_strict(state,step,ctypes.byref(out))
                total+=1
                if status:
                    accepted+=1
                    before=val(state)
                    after=val(out)
                    true=before+val(step)
                    inexact+=after!=true
                    wrong_direction+=(after-before>0)!=(delta>0) or ((after-before<0)!=(delta<0))
                    state=out
                else:
                    rejected+=1
                    untouched_fail+=not(out.hi==1234567.0 and out.lo==0.0)
        assert total==16384
        assert wrong_direction==0 and untouched_fail==0
        boundary_accept=boundary_reject=0
        base=T(2.0**53,1.0)
        for k in range(45,71):
            for sign in (-1.0,1.0):
                for _ in range(16):
                    step=make(sign*2.0**(-k))
                    out=T(1234567.0,0.0)
                    status=lib.bl_time2_add_strict(base,step,ctypes.byref(out))
                    boundary_accept+=bool(status)
                    boundary_reject+=not status
                    if status:
                        assert (val(out)>val(base))==(sign>0)
                    else:
                        assert out.hi==1234567.0 and out.lo==0.0
        assert inexact > 0 and boundary_reject > 0
        return dict(compiler=compiler,total=total,accepted=accepted,rejected=rejected,inexact_accepted=inexact,wrong_direction=wrong_direction,failed_out_mutations=untouched_fail,boundary_total=boundary_accept+boundary_reject,boundary_accepted=boundary_accept,boundary_rejected=boundary_reject)

if __name__=='__main__':
    for c in sys.argv[1:] or ['gcc','clang']:
        print(audit(c))
