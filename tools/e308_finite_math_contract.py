"""E308: falsify unsafe finite-math build assumptions on a classroom model.

The numerical engine rejects NaN/Inf inputs using isfinite(). Compilers
with -ffast-math/-ffinite-math-only may assume those inputs do not exist,
making the guards unsound. Check that unsupported builds fail closed.

No target, weapon, real-world firing, or physical performance claims.
"""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = "finite-input validation requires non-fast-math IEEE semantics"
HARNESS = r"""
#include <math.h>
#include "src/physics.h"
int main(void) {
    NumericalTrajectory out = {0};
    if (bl_simulate_vacuum(NAN, 45.0, 0.1, &out) != -1) return 1;
    if (bl_simulate_vacuum(INFINITY, 45.0, 0.1, &out) != -1) return 2;
    if (bl_simulate_vacuum(1.0, 45.0, NAN, &out) != -1) return 3;
    if (bl_simulate_vacuum(1.0, INFINITY, 0.1, &out) != -1) return 4;
    return 0;
}
"""
STRICT = (("-O0",), ("-O2",), ("-O3",))
UNSAFE = (("-O2", "-ffast-math"), ("-O2", "-ffinite-math-only"), ("-Ofast",))


def run() -> dict:
    compilers = tuple(c for c in ("gcc", "clang") if shutil.which(c))
    if not compilers:
        raise RuntimeError("No C compiler available; no portability conclusion")
    records = []
    with tempfile.TemporaryDirectory(prefix="e308-") as td:
        work = Path(td)
        source = work / "probe.c"
        source.write_text(HARNESS, encoding="utf-8")
        for compiler in compilers:
            version = subprocess.check_output(
                [compiler, "--version"], text=True, timeout=10
            ).splitlines()[0]
            for flags, expected in (
                *((f, "pass") for f in STRICT),
                *((f, "reject") for f in UNSAFE),
            ):
                exe = work / (compiler + "_" + "_".join(flags).replace("-", ""))
                cmd = [
                    compiler, "-std=c11", "-Wall", "-Wextra", "-pedantic",
                    *flags, "-I", str(ROOT), str(source),
                    str(ROOT / "src/physics.c"), "-lm", "-o", str(exe),
                ]
                built = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=30, check=False
                )
                guard_observed = GUARD in (built.stdout + built.stderr)
                if expected == "reject":
                    accepted = built.returncode != 0 and guard_observed
                    outcome = "rejected_with_explicit_guard" if accepted else "unexpected"
                else:
                    if built.returncode != 0:
                        accepted = False
                        outcome = "compile_failed"
                    else:
                        executed = subprocess.run(
                            [str(exe)], capture_output=True, text=True,
                            timeout=10, check=False
                        )
                        accepted = executed.returncode == 0
                        outcome = "finite_inputs_rejected" if accepted else (
                            "invalid_input_accepted_or_runtime_failed"
                        )
                records.append({
                    "compiler": compiler,
                    "version": version,
                    "flags": list(flags),
                    "expected": expected,
                    "observed": outcome,
                    "passed": accepted,
                    "compile_exit_code": built.returncode,
                    "guard_diagnostic": guard_observed,
                })
    return {
        "experiment": "E308 finite-math build-contract falsification",
        "platform": platform.platform(),
        "cases": records,
        "all_contracts_pass": all(x["passed"] for x in records),
        "claim": "Compiler-option boundary verified only on listed toolchains",
        "limitations": [
            "Compiler rejection is not a proof of numerical accuracy.",
            "No cross-CPU or non-Linux ABI evaluation.",
            "NaN/Inf are synthetic invalid inputs, not field measurements.",
            "No weapon or target application.",
        ],
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    if not result["all_contracts_pass"]:
        raise SystemExit(1)
