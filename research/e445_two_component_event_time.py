"""E445: frozen E429 generic event-time representability ablation.

This is dimensionless classroom numerical analysis, not a real-world trajectory
calculator. It compares binary64 timestamps, an exact two-float expansion and
an independently computed Decimal root from the same binary64 event state.
"""
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
import json
import math

from research.e429_subulp_grid_oracle import ANGLES, G, OFFSETS, PI, SPEEDS, classify


def event_state(speed, angle, offset):
    """Mirror E429 arithmetic, returning the first positive crossing state."""
    v0 = speed * math.sin(angle * PI / 180.0)
    dt = (v0 / G) * (1.0 - offset * (2.0 ** -52) / 2.0)
    t = y = 0.0
    vy = v0
    for step in range(8):
        next_t = t + dt
        next_y = y + vy * dt - 0.5 * G * dt * dt
        next_vy = vy - G * dt
        if not all(map(math.isfinite, (next_t, next_y, next_vy))) or next_t <= t:
            return None
        if next_y == 0.0:
            return None
        if next_y < 0.0:
            root = math.hypot(vy, math.sqrt(2.0 * G) * math.sqrt(y))
            tau = ((vy + root) / G if vy >= 0.0
                   else (2.0 * y) / (root - vy))
            if not (math.isfinite(tau) and 0.0 < tau <= dt):
                return None
            return (t, y, vy, tau, step)
        t, y, vy = next_t, next_y, next_vy
    return None


def split_time(t, tau):
    """Round exact binary64 t+tau to hi, then retain its exact low residual."""
    if not all(map(math.isfinite, (t, tau))) or tau <= 0:
        raise ValueError("finite t and strictly positive finite tau required")
    exact = Fraction(t) + Fraction(tau)
    hi = float(exact)
    if not math.isfinite(hi):
        raise OverflowError("timestamp overflow")
    lo = float(exact - Fraction(hi))
    return hi, lo


def run():
    counts = Counter()
    max_pair_error_ulp = 0.0
    max_root_error_ulp = 0.0
    max_nextafter_bias_ulp = 0.0
    rejects = []
    for speed in SPEEDS:
        for angle in ANGLES:
            for offset in OFFSETS:
                old = classify(speed, angle, offset)
                counts[old["status"]] += 1
                state = event_state(speed, angle, offset)
                if old["status"] == "exact_zero":
                    assert state is None
                    continue
                if old["status"] not in ("accepted", "subulp_reject"):
                    raise AssertionError((speed, angle, offset, old))
                if state is None:
                    raise AssertionError("lost positive crossing")
                t, y, vy, tau, step = state
                assert step == old["step"]
                hi, lo = split_time(t, tau)
                exact = Fraction(t) + Fraction(tau)
                restored = Fraction(hi) + Fraction(lo)
                assert restored > Fraction(t)
                assert hi == t + tau
                assert (float.fromhex(hi.hex()), float.fromhex(lo.hex())) == (hi, lo)
                ulp = math.nextafter(t, math.inf) - t
                max_pair_error_ulp = max(max_pair_error_ulp, float(abs(restored-exact))/ulp)
                with localcontext() as ctx:
                    ctx.prec = 90
                    d_vy, d_y, d_g = Decimal(vy), Decimal(y), Decimal(G)
                    root = (d_vy*d_vy + 2*d_g*d_y).sqrt()
                    oracle_tau = ((d_vy + root) / d_g if vy >= 0
                                  else 2*d_y / (root - d_vy))
                    root_error = abs(Decimal(tau) - oracle_tau)
                    max_root_error_ulp = max(max_root_error_ulp, float(root_error/Decimal(ulp)))
                if old["status"] == "subulp_reject":
                    assert hi == t and lo > 0
                    forced = math.nextafter(t, math.inf)
                    bias = float(Fraction(forced)-exact)/ulp
                    max_nextafter_bias_ulp = max(max_nextafter_bias_ulp, bias)
                    rejects.append({"magnitude": speed, "angle": angle,
                                    "offset": offset, "step": step,
                                    "lo_over_ulp": lo/ulp,
                                    "nextafter_bias_ulp": bias})
    return {"experiment": "E445", "total": sum(counts.values()),
            "baseline_counts": dict(counts),
            "positive_crossings": counts["accepted"]+counts["subulp_reject"],
            "two_component_nonmonotone": 0,
            "max_pair_roundtrip_error_ulp": max_pair_error_ulp,
            "max_root_error_ulp": max_root_error_ulp,
            "max_forced_nextafter_bias_ulp": max_nextafter_bias_ulp,
            "subulp_cases": rejects,
            "claim": "frozen synthetic binary64 arithmetic, not C integration or measured physics"}


if __name__ == "__main__":
    result = run()
    assert result["total"] == 1080
    assert result["baseline_counts"] == {"accepted": 1070,
                                           "exact_zero": 6, "subulp_reject": 4}
    assert result["max_pair_roundtrip_error_ulp"] == 0.0
    print(json.dumps(result, indent=2, sort_keys=True))
