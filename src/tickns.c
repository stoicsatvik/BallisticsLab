#include "tickns.h"
#include <limits.h>
#include <stddef.h>

#define BL_NS_PER_SEC INT64_C(1000000000)

int bl_tickns_add(BlTickNs base, int64_t delta_ns, BlTickNs *out) {
    if (!out || (delta_ns > 0 && base.nanoseconds > INT64_MAX - delta_ns) ||
        (delta_ns < 0 && base.nanoseconds < INT64_MIN - delta_ns)) return 0;
    BlTickNs candidate = {base.nanoseconds + delta_ns};
    *out = candidate;
    return 1;
}

int bl_tickns_difference(BlTickNs later, BlTickNs earlier, int64_t *out) {
    const int64_t a = later.nanoseconds, b = earlier.nanoseconds;
    if (!out || (b < 0 && a > INT64_MAX + b) ||
        (b > 0 && a < INT64_MIN + b)) return 0;
    *out = a - b;
    return 1;
}

int bl_tickns_from_parts(int64_t seconds, uint32_t nanos, BlTickNs *out) {
    const int64_t whole_max = INT64_MAX / BL_NS_PER_SEC;
    const int64_t whole_min = INT64_MIN / BL_NS_PER_SEC;
    if (!out || nanos >= (uint32_t)BL_NS_PER_SEC ||
        seconds > whole_max || seconds < whole_min - 1) return 0;
    int64_t candidate;
    if (seconds == whole_min - 1) {
        /* The one negative whole-second value whose product overflows.
         * Adding a large enough positive fractional remainder restores
         * representability, including the exact INT64_MIN endpoint. */
        const int64_t min_nanos = BL_NS_PER_SEC + (INT64_MIN % BL_NS_PER_SEC);
        if ((int64_t)nanos < min_nanos) return 0;
        candidate = INT64_MIN + ((int64_t)nanos - min_nanos);
    } else {
        const int64_t base = seconds * BL_NS_PER_SEC;
        if (base >= 0 && (int64_t)nanos > INT64_MAX - base) return 0;
        candidate = base + (int64_t)nanos;
    }
    out->nanoseconds = candidate;
    return 1;
}

int bl_tickns_to_parts(BlTickNs value, int64_t *seconds, uint32_t *nanos) {
    if (!seconds || !nanos) return 0;
    int64_t s = value.nanoseconds / BL_NS_PER_SEC;
    int64_t n = value.nanoseconds % BL_NS_PER_SEC;
    if (n < 0) { --s; n += BL_NS_PER_SEC; }
    *seconds = s;
    *nanos = (uint32_t)n;
    return 1;
}

int bl_tickns_encode_be(BlTickNs value, unsigned char out[8]) {
    if (!out) return 0;
    uint64_t bits = (uint64_t)value.nanoseconds;
    for (int i = 7; i >= 0; --i) {
        out[i] = (unsigned char)(bits & UINT64_C(255));
        bits >>= 8;
    }
    return 1;
}

int bl_tickns_decode_be(const unsigned char in[8], BlTickNs *out) {
    if (!in || !out) return 0;
    uint64_t bits = 0;
    for (int i = 0; i < 8; ++i) bits = (bits << 8) | (uint64_t)in[i];
    int64_t decoded;
    if (bits <= (uint64_t)INT64_MAX) {
        decoded = (int64_t)bits;
    } else {
        decoded = -(int64_t)(UINT64_MAX - bits) - INT64_C(1);
    }
    out->nanoseconds = decoded;
    return 1;
}
