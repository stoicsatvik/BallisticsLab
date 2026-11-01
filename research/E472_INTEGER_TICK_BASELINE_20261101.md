# E472 | Fixed-scale integer ticks versus two-component binary64

Date: 2026-11-01. Generic numerical timestamps only. No physical/trajectory application, deployment, or targeting integration.

## Frozen hypothesis

Under a **100-year horizon** measured in 365-day model years and a **1 ns minimum representable step**, signed 64-bit integer nanosecond ticks can represent every timestamp and every tested signed step exactly without overflow. Two-component binary64 arithmetic is not an exact representation of arbitrary decimal nanoseconds; its accuracy depends strongly on the input construction path.

This is a deliberately bounded comparison, not a universal recommendation. The integer baseline is Python's exact integer arithmetic with an explicit signed-int64 range check, **not** a production C int64 implementation. The two-component baseline calls the repository's real `src/time2.c` `bl_time2_add_strict` via ctypes.

## Reproduction

Run `python research/e472_tick_baseline.py gcc clang` from a checkout of this branch on a machine with GCC and Clang, Python 3, and a POSIX shared-library loader. Compile flags: `-std=c11 -O2 -Wall -Wextra -Werror -pedantic -fno-fast-math -fPIC -shared`. Frozen seed **472**, **4,096** independent start/step pairs, start uniformly sampled from the interior of [0, 100 years], signed step uniformly sampled from **1 to 1,000,000,000 ns**. No chaining of outputs. Every target stays in range.

For each pair, compare the exact target rational `(start_ns + delta_ns) / 1e9` with two ways of constructing `BlTime2`:

- **Naive:** convert all nanoseconds to one binary64 seconds value, low component zero.
- **Split:** pass exact integer whole seconds as high component and a binary64 fractional-second remainder as low component.

The two-component error metric includes **input conversion plus addition error**, not addition error alone. Exactness uses `fractions.Fraction` on the actual binary64 output. Errors are absolute ns, and all values are synthetic.

## Local results

GCC and Clang gave identical results:

| Measurement | int64 ns tick oracle | Two-component naive | Two-component split |
|---|---:|---:|---:|
| Operations | 4,096 | 4,096 | 4,096 |
| Accepted | 4,096 | 4,096 | 4,096 |
| Rejected | 0 | 0 | 0 |
| Wrong-direction accepted | 0 | 0 | 0 |
| Exactly equal to target rational | 4,096 | 0 | 0 |
| Largest absolute error | 0 ns | **238.2814941467839 ns** | **0.00000010909894854194135 ns** |

The split construction is dramatically more accurate in this cohort, but it is **not exact**. The E471 direction guard admits all these steps; directional correctness alone does not ensure magnitude accuracy. This is the preserved negative result.

## Range and storage trade-off

Signed 64-bit ticks have maximum positive timestamp `2^63-1` ticks. Under 365-day model years, positive representable horizons are approximately:

| Fixed tick | Max positive horizon |
|---|---:|
| 1 ns | 292.471 years |
| 1 microsecond | 292,471 years |
| 1 millisecond | 292,471,209 years |
| 1 second | 292,471,208,678 years |

A 100-year nanosecond horizon fits; a 300-year nanosecond horizon does **not**. A 64-bit tick occupies 8 native bytes, while `BlTime2` occupies 16 native bytes on the tested platform. These are **native representation sizes**, not verified wire serialization sizes. No claim is made about cross-platform ABI, endianness, timestamp epoch, leap seconds, or signed overflow behavior in C.

## What this does and does not establish

- For bounded, known-scale timestamps, exact integer ticks are a simpler exact arithmetic baseline.
- A two-component representation can greatly reduce error when constructed with a split high/low path, but does not represent arbitrary decimal ns exactly.
- The 100-year synthetic distribution is not representative of any deployment. No speed, energy, concurrency, portability, or physical-accuracy benchmark was performed.
- Fixed ticks sacrifice horizon when finer resolution is chosen; two-component binary64 has a different dynamic range and no universal minimum tick.
- `bl_time2_add_strict` remains opt-in, unchanged; no API, production code, CI, merge, or deployment is changed by E472.

**Next falsification:** implement an optional checked C int64-tick prototype with explicit epoch and scale, test overflow/negative epochs and round-trip serialization, then compare performance and error against the two-component baseline under the same horizon. Keep this branch draft and stacked on E471 PR #26.
