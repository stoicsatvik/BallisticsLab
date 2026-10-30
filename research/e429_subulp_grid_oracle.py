"""E429: offline binary64 terminal-event stress and high-precision oracle.

Educational constant-acceleration arithmetic only. No targeting, real-world
weapon inputs, or empirical physics claims. Mirrors the E409 numerical
time/vertical-state predicates; it does NOT execute the repository C code.
"""
from collections import Counter
from decimal import Decimal, localcontext
import json
import math

G = 9.80665
PI = 3.14159265358979323846
SPEEDS = (0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 50, 100)
ANGLES = (5, 10, 15, 20, 30, 45, 60, 75, 85)
OFFSETS = (1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 24, 32)


def classify(speed, angle, offset):
    """Return category and oracle data for a fixed-step generic event."""
    v0 = speed * math.sin(angle * PI / 180.0)
    flight = 2.0 * v0 / G
    dt = (flight / 2.0) * (1.0 - offset * (2.0 ** -52) / 2.0)
    t = y = 0.0
    vy = v0
    for step in range(8):
        next_t = t + dt
        next_y = y + vy * dt - 0.5 * G * dt * dt
        next_vy = vy - G * dt
        if (not all(map(math.isfinite, (next_t, next_y, next_vy)))
                or next_t <= t or (next_y == y and next_vy == vy)):
            return {"status": "other_guard", "step": step}
        if next_y == 0.0:
            return {"status": "exact_zero", "step": step}
        if next_y < 0.0:
            root = math.hypot(vy, math.sqrt(2.0 * G) * math.sqrt(y))
            tau = ((vy + root) / G if vy >= 0.0
                   else (2.0 * y) / (root - vy))
            if not math.isfinite(tau) or tau < 0.0 or tau > dt:
                return {"status": "invalid_tau", "step": step}
            with localcontext() as ctx:
                ctx.prec = 90
                radicand = Decimal(vy) ** 2 + 2 * Decimal(G) * Decimal(y)
                oracle_root = radicand.sqrt()
                oracle_tau = ((Decimal(vy) + oracle_root) / Decimal(G)
                              if vy >= 0.0 else
                              2 * Decimal(y) / (oracle_root - Decimal(vy)))
                rounded_oracle_time = float(Decimal(t) + oracle_tau)
                abs_tau_error = abs(Decimal(tau) - oracle_tau)
            status = "subulp_reject" if t + tau == t else "accepted"
            return {
                "status": status,
                "step": step,
                "oracle_unrepresentable": rounded_oracle_time == t,
                "tau_over_ulp": tau / (math.nextafter(t, math.inf) - t),
                "tau_absolute_error": float(abs_tau_error),
            }
        t, y, vy = next_t, next_y, next_vy
    return {"status": "timeout", "step": 8}


def run():
    counts = Counter()
    by_offset = {}
    rejects = []
    unrepresentable_accepted = 0
    max_tau_error = 0.0
    for offset in OFFSETS:
        group = Counter()
        for speed in SPEEDS:
            for angle in ANGLES:
                result = classify(speed, angle, offset)
                status = result["status"]
                counts[status] += 1
                group[status] += 1
                if status == "subulp_reject":
                    rejects.append({
                        "speed": speed, "angle_deg": angle,
                        "offset": offset, "step": result["step"],
                        "tau_over_ulp": result["tau_over_ulp"],
                        "oracle_unrepresentable":
                            result["oracle_unrepresentable"],
                    })
                if status == "accepted" and result["oracle_unrepresentable"]:
                    unrepresentable_accepted += 1
                max_tau_error = max(max_tau_error,
                                    result.get("tau_absolute_error", 0.0))
        by_offset[str(offset)] = dict(group)
    return {
        "experiment": "E429",
        "total": len(SPEEDS) * len(ANGLES) * len(OFFSETS),
        "counts": dict(counts),
        "by_offset": by_offset,
        "rejects": rejects,
        "oracle_unrepresentable_accepted": unrepresentable_accepted,
        "max_absolute_root_error": max_tau_error,
        "claim": "source-equivalent synthetic arithmetic; not exact C execution",
    }


if __name__ == "__main__":
    report = run()
    assert report["total"] == 1080
    assert report["counts"] == {
        "accepted": 1070, "exact_zero": 6, "subulp_reject": 4
    }, report["counts"]
    assert report["oracle_unrepresentable_accepted"] == 0
    assert all(r["oracle_unrepresentable"] for r in report["rejects"])
    print(json.dumps(report, indent=2, sort_keys=True))
