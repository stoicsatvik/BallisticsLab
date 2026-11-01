#include "tickns.h"
#include <assert.h>
#include <stdint.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

static void check_roundtrip(int64_t ns) {
    BlTickNs a = {ns}, b = {0};
    int64_t sec = 123;
    uint32_t sub = 123;
    unsigned char bytes[8] = {0};
    assert(bl_tickns_to_parts(a, &sec, &sub));
    assert(sub < UINT32_C(1000000000));
    assert(bl_tickns_from_parts(sec, sub, &b) && b.nanoseconds == ns);
    assert(bl_tickns_encode_be(a, bytes));
    b.nanoseconds = 0;
    assert(bl_tickns_decode_be(bytes, &b) && b.nanoseconds == ns);
}

int main(void) {
    BlTickNs out = {42};
    assert(bl_tickns_add((BlTickNs){INT64_MAX}, 1, &out) == 0 && out.nanoseconds == 42);
    assert(bl_tickns_add((BlTickNs){INT64_MIN}, -1, &out) == 0 && out.nanoseconds == 42);
    assert(bl_tickns_add((BlTickNs){INT64_MAX}, -1, &out) && out.nanoseconds == INT64_MAX - 1);
    assert(bl_tickns_add((BlTickNs){INT64_MIN}, 1, &out) && out.nanoseconds == INT64_MIN + 1);
    out.nanoseconds = 42;
    assert(!bl_tickns_difference((BlTickNs){INT64_MAX}, (BlTickNs){-1}, &out.nanoseconds) && out.nanoseconds == 42);
    assert(!bl_tickns_difference((BlTickNs){INT64_MIN}, (BlTickNs){1}, &out.nanoseconds) && out.nanoseconds == 42);
    assert(bl_tickns_difference((BlTickNs){-1}, (BlTickNs){INT64_MIN}, &out.nanoseconds) && out.nanoseconds == INT64_MAX);
    assert(bl_tickns_from_parts(-1, 500000000U, &out) && out.nanoseconds == -500000000);
    assert(bl_tickns_from_parts(0, 999999999U, &out) && out.nanoseconds == 999999999);
    out.nanoseconds = 42;
    assert(!bl_tickns_from_parts(0, 1000000000U, &out) && out.nanoseconds == 42);
    assert(!bl_tickns_from_parts(INT64_MAX, 0, &out) && out.nanoseconds == 42);
    assert(!bl_tickns_from_parts(INT64_MIN, 0, &out) && out.nanoseconds == 42);
    assert(!bl_tickns_from_parts(-9223372037LL, 145224191U, &out) && out.nanoseconds == 42);
    assert(bl_tickns_from_parts(-9223372037LL, 145224192U, &out) && out.nanoseconds == INT64_MIN);
    assert(bl_tickns_from_parts(9223372036LL, 854775807U, &out) && out.nanoseconds == INT64_MAX);
    out.nanoseconds = 42;
    assert(!bl_tickns_from_parts(9223372036LL, 854775808U, &out) && out.nanoseconds == 42);
    const int64_t edges[] = {INT64_MIN, INT64_MIN+1, -1000000001LL, -1000000000LL, -999999999LL, -1, 0, 1, 999999999LL, 1000000000LL, 1000000001LL, INT64_MAX-1, INT64_MAX};
    for (size_t i=0; i<sizeof(edges)/sizeof(edges[0]); ++i) check_roundtrip(edges[i]);
    unsigned char negative_one[8];
    assert(bl_tickns_encode_be((BlTickNs){-1}, negative_one));
    for (int i=0; i<8; ++i) assert(negative_one[i] == 255);
    unsigned char positive_one[8];
    assert(bl_tickns_encode_be((BlTickNs){1}, positive_one));
    for (int i=0; i<7; ++i) assert(positive_one[i] == 0);
    assert(positive_one[7] == 1);
    assert(!bl_tickns_add((BlTickNs){0}, 0, NULL));
    assert(!bl_tickns_to_parts((BlTickNs){0}, NULL, (uint32_t *)&out));
    assert(!bl_tickns_encode_be((BlTickNs){0}, NULL));
    assert(!bl_tickns_decode_be(NULL, &out));
    assert(!bl_tickns_decode_be(positive_one, NULL));
    puts("E473 deterministic C contracts: PASS");
    return 0;
}
