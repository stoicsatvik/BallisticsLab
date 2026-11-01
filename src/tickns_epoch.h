#ifndef BALLISTICSLAB_TICKNS_EPOCH_H
#define BALLISTICSLAB_TICKNS_EPOCH_H

#include "tickns.h"
#include <stdint.h>

/* Generic caller-managed epoch identity. An ID identifies a *semantic* epoch;
 * callers must maintain a collision-free registry. ID 0 is invalid.
 * The wire format is not authenticated and has no corruption checksum. */
typedef struct {
    BlTickNs tick;
    uint32_t epoch_id;
} BlEpochTickNs;

#define BL_EPOCH_WIRE_SIZE 16
#define BL_EPOCH_WIRE_VERSION 1
#define BL_EPOCH_WIRE_NS_SCALE 1

/* All functions return 0 on invalid input and leave outputs untouched. */
int bl_epoch_tickns_init(BlTickNs tick, uint32_t epoch_id, BlEpochTickNs *out);
int bl_epoch_tickns_add(BlEpochTickNs base, int64_t delta_ns, BlEpochTickNs *out);
int bl_epoch_tickns_difference(BlEpochTickNs later, BlEpochTickNs earlier, int64_t *out);

/* v1 wire layout (byte offsets): 0..1='B','T'; 2=version 1;
 * 3=nanosecond scale 1; 4..7=nonzero epoch ID, big endian;
 * 8..15=signed int64 ticks, big endian two's complement.
 * Decoder requires the expected epoch ID; no automatic epoch conversion. */
int bl_epoch_tickns_encode(BlEpochTickNs value, unsigned char out[BL_EPOCH_WIRE_SIZE]);
int bl_epoch_tickns_decode(const unsigned char in[BL_EPOCH_WIRE_SIZE],
                           uint32_t expected_epoch_id, BlEpochTickNs *out);

#endif
