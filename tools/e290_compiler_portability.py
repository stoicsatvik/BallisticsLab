"""E290: independently compile the same generic physics model with GCC/Clang.

Bounded, synthetic classroom inputs only. This is a numerical portability
experiment, not weapon modeling, target prediction, or physical validation.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEEDS = (1.0, 3.0, 10.0, 30.0, 100.0)
ANGLES = (10.0, 25.0, 45.0, 65.0, 80.0)
STEPS = (0.01, 0.05, 0.2, 1.0, 5.0, 10.0)
NORMAL = len(SPEEDS) * len(ANGLES) * len(STEPS)
EDGES = 9


def parse_trace(stdout: str) -> tuple[dict[int, tuple], dict[tuple[int, int], tuple]]:
    cases: dict[int, tuple] = {}
    states: dict[tuple[int, int], tuple] = {}
    for line in stdout.splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "C" and len(fields) == 7:
            idx, status, count = map(int, fields[1:4])
            assert idx not in cases
            vals = tuple(float(x) for x in fields[4:])
            assert all(math.isfinite(x) for x in vals)
            cases[idx] = (status, count, *vals)
        elif fields[0] == "S" and len(fields) == 8:
            idx, sample = map(int, fields[1:3])
            assert (idx, sample) not in states
            vals = tuple(float(x) for x in fields[3:])
            assert all(math.isfinite(x) for x in vals)
            states[idx, sample] = vals
        else:
            raise ValueError("Unexpected trace line")
    assert set(cases) == set(range(NORMAL + EDGES))
    assert all(cases[i][0] == 0 for i in range(NORMAL))
    assert cases[NORMAL][0] == 0 and cases[NORMAL][1] == 1
    assert all(cases[i][0] == -1 for i in range(NORMAL + 1, NORMAL + EDGES))
    assert sum(row[1] for row in cases.values()) == len(states)
    for idx, row in cases.items():
        assert all((idx, i) in states for i in range(row[1]))
    return cases, states


def compare(reference: tuple, candidate: tuple) -> dict:
    a_cases, a_states = reference
    b_cases, b_states = candidate
    assert a_cases.keys() == b_cases.keys()
    status_mismatches = sum(a_cases[i][:2] != b_cases[i][:2] for i in a_cases)
    missing = len(a_states.keys() ^ b_states.keys())
    max_delta = 0.0
    different_bits = 0
    compared = 0
    worst = None
    for key in sorted(a_states.keys() & b_states.keys()):
        for col, (a, b) in enumerate(zip(a_states[key], b_states[key])):
            delta = abs(a - b) / max(1.0, abs(a))
            if delta > max_delta:
                max_delta, worst = delta, (key[0], key[1], col)
            different_bits += struct.pack("!d", a) != struct.pack("!d", b)
            compared += 1
    for idx in sorted(a_cases):
        if a_cases[idx][:2] != b_cases[idx][:2]:
            continue
        for col, (a, b) in enumerate(zip(a_cases[idx][2:], b_cases[idx][2:])):
            delta = abs(a - b) / max(1.0, abs(a))
            if delta > max_delta:
                max_delta, worst = delta, (idx, -1, col)
            different_bits += struct.pack("!d", a) != struct.pack("!d", b)
            compared += 1
    return {
        "status_or_count_mismatches": status_mismatches,
        "missing_state_keys": missing,
        "compared_floating_fields": compared,
        "different_binary64_fields": different_bits,
        "maximum_normalized_difference": max_delta,
        "worst_case_sample_field": worst,
    }


def run() -> dict:
    compilers = [c for c in ("gcc", "clang") if shutil.which(c)]
    if len(compilers) != 2:
        raise RuntimeError("Both GCC and Clang are required; do not infer portability")
    versions = {}
    traces = {}
    with tempfile.TemporaryDirectory(prefix="e290-") as td:
        for cc in compilers:
            versions[cc] = subprocess.check_output([cc, "--version"], text=True).splitlines()[0]
            for opt in ("O0", "O2", "O3"):
                label = f"{cc}-{opt}"
                executable = str(Path(td) / label)
                subprocess.run([
                    cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    f"-{opt}", "tests/e290_compiler_trace.c", "src/physics.c",
                    "-lm", "-o", executable,
                ], cwd=ROOT, check=True, timeout=30)
                output = subprocess.check_output([executable], text=True, timeout=30)
                traces[label] = parse_trace(output)
    reference = traces["gcc-O0"]
    comparisons = {label: compare(reference, trace) for label, trace in traces.items()}
    return {
        "experiment": "E290 generic numerical cross-compiler portability",
        "platform": platform.platform(),
        "toolchains": versions,
        "configurations": len(traces),
        "normal_cases_per_configuration": NORMAL,
        "edge_cases_per_configuration": EDGES,
        "reference_state_samples": len(reference[1]),
        "comparisons_against_gcc_O0": comparisons,
        "all_status_and_counts_agree": all(
            x["status_or_count_mismatches"] == 0 and x["missing_state_keys"] == 0
            for x in comparisons.values()
        ),
        "all_normalized_differences_below_1e_10": all(
            x["maximum_normalized_difference"] < 1e-10
            for x in comparisons.values()
        ),
        "claim": "BOUNDED SYNTHETIC COMPILER REPRODUCIBILITY ONLY",
        "limitations": [
            "No actual measurement, material, device, target or field data.",
            "Only GCC/Clang on the recorded Linux runner, not all CPUs/ABIs.",
            "Printing 17 significant decimal digits preserves binary64 round-trip.",
            "A passing test does not prove global numerical error bounds.",
            "The experiment does not optimize trajectories or external effects.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    data = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data + "\n")
    print(data)
    if not result["all_status_and_counts_agree"]:
        raise SystemExit("Cross-compiler status/sample divergence: inspect evidence")


if __name__ == "__main__":
    main()
