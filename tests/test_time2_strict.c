/* E471: generic signed-step representability, not a physical timing claim. */
#include <assert.h>
#include <float.h>
#include <math.h>
#include <stdio.h>
#include "../src/time2.h"

static BlTime2 make(double hi, double lo) {
    BlTime2 value;
    assert(bl_time2_make(hi, lo, &value));
    return value;
}

int main(void) {
    const BlTime2 base = make(0x1p53, 1.0);
    const BlTime2 tiny_pos = make(0x1p-54, 0);
    const BlTime2 tiny_neg = make(-0x1p-54, 0);
    BlTime2 result = make(17, 0);
    const BlTime2 sentinel = result;
    assert(!bl_time2_add_strict(base, tiny_pos, &result));
    assert(bl_time2_compare(result, sentinel) == 0);
    assert(!bl_time2_add_strict(base, tiny_neg, &result));
    assert(bl_time2_compare(result, sentinel) == 0);

    /* The preexisting unchecked API still silently stalls. */
    assert(bl_time2_add(base, tiny_pos, &result));
    assert(bl_time2_compare(result, base) == 0);

    assert(bl_time2_add_strict(base, make(1, 0), &result));
    assert(bl_time2_compare(result, base) > 0);
    assert(bl_time2_add_strict(base, make(-1, 0), &result));
    assert(bl_time2_compare(result, base) < 0);
    assert(bl_time2_add_strict(base, make(0, 0), &result));
    assert(bl_time2_compare(result, base) == 0);

    /* Unnormalized caller input is canonicalized, not lexicographically
       compared against an invalid two-component representation. */
    const BlTime2 raw_base = {0x1p53, 1.0};
    const BlTime2 raw_zero = {0x1p53, -0x1p53};
    assert(bl_time2_add_strict(raw_base, raw_zero, &result));
    assert(bl_time2_compare(result, base) == 0);

    result = sentinel;
    assert(!bl_time2_add_strict(make(DBL_MAX, 0), make(DBL_MAX, 0), &result));
    assert(bl_time2_compare(result, sentinel) == 0);
    assert(!bl_time2_add_strict(base, make(1, 0), NULL));
    assert(!bl_time2_add_strict((BlTime2){NAN, 0}, tiny_pos, &result));
    assert(bl_time2_compare(result, sentinel) == 0);
    puts("E471 strict signed-step admission passed");
    return 0;
}
