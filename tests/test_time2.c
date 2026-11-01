#include <assert.h>
#include <float.h>
#include <math.h>
#include <stdio.h>
#include "../src/time2.h"

int main(void) {
    BlTime2 base, one, plus, twice, zero, negative;
    assert(bl_time2_make(0x1p53, 0.0, &base));
    assert(bl_time2_make(1.0, 0.0, &one));
    assert(bl_time2_add(base, one, &plus));
    assert(plus.hi == 0x1p53 && plus.lo == 1.0);
    assert(bl_time2_compare(plus, base) > 0);
    assert(base.hi + one.hi == base.hi);
    assert(bl_time2_add(plus, one, &twice));
    assert(twice.hi == 0x1.0000000000001p53 && twice.lo == 0.0);
    assert(bl_time2_compare(twice, plus) > 0);
    assert(bl_time2_make(0, 0, &zero));
    assert(bl_time2_make(-1, 0, &negative));
    assert(bl_time2_compare(negative, zero) < 0);
    assert(bl_time2_make(1e-300, 1e-320, &plus));
    assert(plus.hi == 1e-300 && plus.lo == 1e-320);
    assert(!bl_time2_make(NAN, 0, &plus));
    assert(!bl_time2_make(INFINITY, 0, &plus));
    assert(!bl_time2_make(DBL_MAX, DBL_MAX, &plus));
    assert(!bl_time2_make(1, 0, NULL));
    assert(!bl_time2_add(base, one, NULL));
    assert(bl_time2_make(0x1p53, 1, &plus));
    char encoded[160];
    assert(snprintf(encoded, sizeof(encoded), "%a %a", plus.hi, plus.lo) > 0);
    BlTime2 decoded;
    assert(sscanf(encoded, "%la %la", &decoded.hi, &decoded.lo) == 2);
    assert(bl_time2_compare(plus, decoded) == 0);
    puts("time2 generic numerical tests passed");
    return 0;
}
