"""E495: exact-rational envelope for mixed-sign two-component timestamps.

This is generic numerical representation research only. It does not model
projectiles, trajectories, firearms, targets or physical timing calibration.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Timestamp(ctypes.Structure):
    _fields_ = [("hi", ctypes.c_double), ("lo", ctypes.c_double)]


def value(t: Timestamp) -> Fraction:
    return Fraction.from_float(t.hi) + Fraction.from_float(t.lo)


def sign(x: Fraction) -> int:
    return (x > 0) - (x < 0)


def load_library(temp_dir: str):
    compiler = shutil.which("gcc") or shutil.which("cc")
    if compiler is None:
        raise RuntimeError("no C compiler available")
    library = str(Path(temp_dir) / "libtime2_e495.so")
    subprocess.run(
        [
            compiler,
            "-std=c11",
            "-O2",
            "-fPIC",
            "-shared",
            "-fno-fast-math",
            str(ROOT / "src" / "time2.c"),
            "-lm",
            "-o",
            library,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    lib = ctypes.CDLL(library)
    lib.bl_time2_make.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(Timestamp),
    ]
    lib.bl_time2_make.restype = ctypes.c_int
    lib.bl_time2_add_strict.argtypes = [
        Timestamp,
        Timestamp,
        ctypes.POINTER(Timestamp),
    ]
    lib.bl_time2_add_strict.restype = ctypes.c_int
    lib.bl_time2_compare.argtypes = [Timestamp, Timestamp]
    lib.bl_time2_compare.restype = ctypes.c_int
    return lib


def make(lib, hi: float, lo: float = 0.0) -> Timestamp:
    out = Timestamp()
    if not lib.bl_time2_make(hi, lo, ctypes.byref(out)):
        raise ValueError(f"input pair rejected by bl_time2_make: {hi.hex()}, {lo.hex()}")
    return out


def two_component_witness(exact: Fraction) -> tuple[str, str] | None:
    """Sufficient canonical hi/lo witness; absence is not proof of impossibility."""
    try:
        hi = float(exact)
    except OverflowError:
        hi = math.copysign(sys.float_info.max, sign(exact))
    if not math.isfinite(hi):
        hi = math.copysign(sys.float_info.max, sign(exact))
    residual = exact - Fraction.from_float(hi)
    try:
        lo = float(residual)
    except OverflowError:
        return None
    if not math.isfinite(lo):
        return None
    if Fraction.from_float(hi) + Fraction.from_float(lo) != exact:
        return None
    return hi.hex(), lo.hex()


def _cases(random_cases: int, seed: int = 495):
    # Structured cancellation, subnormal, and overflow-adjacent controls.
    min_sub = math.ulp(0.0)
    yield (2.0**53, 1.0, 2.0**-54, 0.0, "positive_sub_low_resolution")
    yield (2.0**53, 1.0, -(2.0**-54), 0.0, "negative_sub_low_resolution")
    yield (1.0, 0.0, -1.0, 0.0, "exact_cancellation")
    yield (min_sub, 0.0, min_sub, 0.0, "minimum_subnormal_addition")
    yield (min_sub, 0.0, -min_sub, 0.0, "minimum_subnormal_cancellation")
    yield (sys.float_info.max, 0.0, min_sub, 0.0, "max_plus_min_subnormal")
    yield (sys.float_info.max, 0.0, -min_sub, 0.0, "max_minus_min_subnormal")
    yield (sys.float_info.max, 0.0, sys.float_info.max, 0.0, "overflow_rejection")

    for exponent in range(-100, 101, 5):
        hi = math.ldexp(1.0, exponent)
        yield (hi, math.ldexp(1.0, exponent - 53), -hi, -math.ldexp(1.0, exponent - 54), f"near_cancel_{exponent}")
        yield (-hi, -math.ldexp(1.0, exponent - 52), hi, math.ldexp(1.0, exponent - 55), f"negative_near_cancel_{exponent}")

    rng = random.Random(seed)
    for index in range(random_cases):
        exponent = rng.randint(-500, 500)
        base_sign = rng.choice((-1.0, 1.0))
        delta_sign = rng.choice((-1.0, 1.0))
        base_hi = base_sign * math.ldexp(rng.uniform(1.0, 2.0), exponent)
        base_gap = rng.randint(53, 1000)
        base_lo = rng.choice((-1.0, 1.0)) * math.ldexp(rng.uniform(0.5, 1.0), exponent - base_gap)
        delta_exp = exponent - rng.randint(1, 100)
        delta_hi = delta_sign * math.ldexp(rng.uniform(1.0, 2.0), delta_exp)
        delta_gap = rng.randint(53, 1074)
        delta_lo = rng.choice((-1.0, 1.0)) * math.ldexp(rng.uniform(0.5, 1.0), delta_exp - delta_gap)
        yield (base_hi, base_lo, delta_hi, delta_lo, f"random_{index}")


def run_campaign(*, random_cases: int = 4096, seed: int = 495) -> dict:
    with tempfile.TemporaryDirectory() as temp:
        lib = load_library(temp)
        total = accepted = rejected = exact_accepted = inexact_accepted = 0
        direction_failures = output_mutations_on_reject = false_rejections_with_witness = 0
        witness_count = 0
        error_ulp_values: list[float] = []
        worst = None
        boundary = []

        for base_hi, base_lo, delta_hi, delta_lo, label in _cases(random_cases, seed):
            base = make(lib, base_hi, base_lo)
            delta = make(lib, delta_hi, delta_lo)
            base_exact = value(base)
            delta_exact = value(delta)
            exact_sum = base_exact + delta_exact
            expected_direction = sign(delta_exact)
            sentinel = make(lib, 17.0, -0.25)
            out = Timestamp(sentinel.hi, sentinel.lo)
            status = int(lib.bl_time2_add_strict(base, delta, ctypes.byref(out)))
            total += 1

            witness = two_component_witness(exact_sum)
            witness_count += int(witness is not None)
            if status:
                accepted += 1
                actual = value(out)
                exact = actual == exact_sum
                exact_accepted += int(exact)
                inexact_accepted += int(not exact)
                actual_direction = sign(actual - base_exact)
                direction_failures += int(actual_direction != expected_direction)
                if not exact:
                    anchor = out.hi if out.hi != 0.0 else out.lo
                    ulp = Fraction.from_float(math.ulp(anchor))
                    error_ulp = float(abs(actual - exact_sum) / ulp)
                    error_ulp_values.append(error_ulp)
                    if worst is None or error_ulp > worst["error_ulp"]:
                        worst = {
                            "case": label,
                            "base_hi": base.hi.hex(),
                            "base_lo": base.lo.hex(),
                            "delta_hi": delta.hi.hex(),
                            "delta_lo": delta.lo.hex(),
                            "result_hi": out.hi.hex(),
                            "result_lo": out.lo.hex(),
                            "error_ulp": error_ulp,
                            "two_component_witness": witness,
                        }
            else:
                rejected += 1
                output_mutations_on_reject += int(value(out) != value(sentinel))
                if witness is not None and expected_direction != 0:
                    false_rejections_with_witness += 1

            if label in {
                "positive_sub_low_resolution",
                "negative_sub_low_resolution",
                "exact_cancellation",
                "minimum_subnormal_addition",
                "minimum_subnormal_cancellation",
                "max_plus_min_subnormal",
                "max_minus_min_subnormal",
                "overflow_rejection",
            }:
                boundary.append({
                    "case": label,
                    "accepted": bool(status),
                    "exact_sum_has_canonical_two_component_witness": witness is not None,
                    "direction": expected_direction,
                    "output_unchanged_on_reject": value(out) == value(sentinel) if not status else None,
                    "result": [out.hi.hex(), out.lo.hex()] if status else None,
                })

        error_ulp_values.sort()
        def percentile(p: float):
            if not error_ulp_values:
                return None
            return error_ulp_values[min(len(error_ulp_values) - 1, int(math.ceil(p * len(error_ulp_values))) - 1)]

        source_sha = hashlib.sha256((ROOT / "src" / "time2.c").read_bytes()).hexdigest()
        return {
            "schema": "ballisticslab/e495/time2-mixed-sign-oracle/v1",
            "seed": seed,
            "random_cases": random_cases,
            "total_cases": total,
            "source_sha256": source_sha,
            "counts": {
                "accepted": accepted,
                "rejected": rejected,
                "exact_accepted": exact_accepted,
                "inexact_accepted": inexact_accepted,
                "direction_failures": direction_failures,
                "output_mutations_on_reject": output_mutations_on_reject,
                "canonical_two_component_witnesses": witness_count,
                "rejections_despite_canonical_witness": false_rejections_with_witness,
            },
            "accepted_inexact_error_ulp": {
                "count": len(error_ulp_values),
                "median": percentile(0.5),
                "p95": percentile(0.95),
                "p99": percentile(0.99),
                "max": max(error_ulp_values) if error_ulp_values else None,
                "worst_case": worst,
            },
            "boundary_cases": boundary,
            "claim": "GENERIC_TWO_COMPONENT_DIRECTIONAL_ADMISSION_AND_ERROR_ENVELOPE_ONLY",
            "limitations": [
                "A canonical two-component witness is a sufficient witness, not a complete proof that no alternative pair exists.",
                "Exact rational arithmetic is the oracle for represented input values; it is not physical time accuracy.",
                "No trajectory, projectile, firearm, targeting or production behavior is tested.",
                "The current API promises directional admission, not exact rational addition.",
                "The deterministic randomized cohort is a computational stress test, not an operational failure-rate estimate.",
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--random-cases", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=495)
    parser.add_argument("--output", type=Path, default=Path("e495_time2_receipt.json"))
    args = parser.parse_args()
    receipt = run_campaign(random_cases=args.random_cases, seed=args.seed)
    args.output.write_text(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))
    return 0 if receipt["counts"]["direction_failures"] == 0 and receipt["counts"]["output_mutations_on_reject"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
