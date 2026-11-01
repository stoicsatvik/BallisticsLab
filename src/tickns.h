#ifndef BALLISTICSLAB_TICKNS_H
#define BALLISTICSLAB_TICKNS_H

#include <stdint.h>

/* Generic exact integer timestamp, at a fixed scale of 1 nanosecond.
 * Zero is a CALLER-DEFINED epoch, not Unix/UTC time. All operands must
 * use the same epoch. No leap-second, timezone, or clock assumptions.
 * None of these functions changes its output on failure. */
typedef struct { int64_t nanoseconds; } BlTickNs;

/* Returns 0 for signed overflow or a null output. */
int bl_tickns_add(BlTickNs base, int64_t delta_ns, BlTickNs *out);
int bl_tickns_difference(BlTickNs later, BlTickNs earlier, int64_t *out);

/* Canonical floor-seconds + [0, 1e9) nanoseconds from the caller's epoch.
 * For example (-1, 500000000) denotes -0.5 seconds. */
int bl_tickns_from_parts(int64_t seconds, uint32_t nanos, BlTickNs *out);
int bl_tickns_to_parts(BlTickNs value, int64_t *seconds, uint32_t *nanos);

/* Canonical 8-byte big-endian two's-complement bit pattern, no epoch tag.
 * Decoding uses only defined C conversions, even for INT64_MIN. */
int bl_tickns_encode_be(BlTickNs value, unsigned char out[8]);
int bl_tickns_decode_be(const unsigned char in[8], BlTickNs *out);

#endif
