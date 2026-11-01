#include "time2.h"
#include <math.h>

/* Error-free two-sum for finite binary64, round-to-nearest, no fast-math. */
static void two_sum(double a, double b, double *s, double *e) {
    const double sum = a + b;
    const double b_virtual = sum - a;
    const double a_virtual = sum - b_virtual;
    *s = sum;
    *e = (a - a_virtual) + (b - b_virtual);
}

int bl_time2_make(double hi, double lo, BlTime2 *out) {
    if (!out || !isfinite(hi) || !isfinite(lo)) return 0;
    double s, e;
    two_sum(hi, lo, &s, &e);
    if (!isfinite(s) || !isfinite(e)) return 0;
    out->hi = s; out->lo = e;
    return 1;
}

int bl_time2_add(BlTime2 a, BlTime2 b, BlTime2 *out) {
    if (!out || !isfinite(a.hi) || !isfinite(a.lo) ||
        !isfinite(b.hi) || !isfinite(b.lo)) return 0;
    double s, e, t, f, u, v, h, l;
    two_sum(a.hi, b.hi, &s, &e);
    if (!isfinite(s)) return 0;
    two_sum(a.lo, b.lo, &t, &f);
    two_sum(e, t, &u, &v);
    two_sum(s, u, &h, &l);
    if (!isfinite(h)) return 0;
    /* This is a two-component approximation, not arbitrary exact arithmetic. */
    return bl_time2_make(h, (l + v) + f, out);
}

int bl_time2_compare(BlTime2 a, BlTime2 b) {
    if (a.hi < b.hi) return -1;
    if (a.hi > b.hi) return 1;
    if (a.lo < b.lo) return -1;
    if (a.lo > b.lo) return 1;
    return 0;
}

int bl_time2_add_strict(BlTime2 a, BlTime2 delta, BlTime2 *out) {
    BlTime2 base, step, candidate;
    const BlTime2 zero = {0.0, 0.0};
    if (!out || !bl_time2_make(a.hi, a.lo, &base) ||
        !bl_time2_make(delta.hi, delta.lo, &step)) return 0;
    const int expected = bl_time2_compare(step, zero);
    if (!bl_time2_add(base, step, &candidate)) return 0;
    if (bl_time2_compare(candidate, base) != expected) return 0;
    *out = candidate;
    return 1;
}
