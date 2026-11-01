#ifndef BALLISTICSLAB_TICKNS_EPOCH_V2_H
#define BALLISTICSLAB_TICKNS_EPOCH_V2_H

#include "tickns.h"
#include <stddef.h>
#include <stdint.h>

/* Research-only v2 namespace gate. Namespace bytes are caller-provided,
 * nonzero opaque identifiers, NOT proof of registry integrity or authenticity.
 * An authoritative registry must bind (namespace, epoch_id) to an immutable
 * semantic definition; two different definitions sharing the pair are unsafe. */
#define BL_EPOCH_V2_NAMESPACE_SIZE 16
#define BL_EPOCH_V2_WIRE_SIZE 32
#define BL_EPOCH_V2_WIRE_VERSION 2
#define BL_EPOCH_V2_WIRE_NS_SCALE 1

typedef struct {
    BlTickNs tick;
    unsigned char namespace_id[BL_EPOCH_V2_NAMESPACE_SIZE];
    uint32_t epoch_id;
} BlEpochTickNsV2;

/* Return 0 on invalid input, incompatible identities or overflow.
 * On failure, caller output is unchanged. All namespaces and IDs nonzero. */
int bl_epoch_v2_init(BlTickNs tick, const unsigned char namespace_id[16],
                     uint32_t epoch_id, BlEpochTickNsV2 *out);
int bl_epoch_v2_add(BlEpochTickNsV2 base, int64_t delta_ns, BlEpochTickNsV2 *out);
int bl_epoch_v2_difference(BlEpochTickNsV2 later, BlEpochTickNsV2 earlier, int64_t *out);

/* Canonical wire: 'B','T', version=2, scale=1, namespace[16],
 * epoch_id uint32 big endian, signed tick int64 big endian.
 * Decoder requires exact length, expected namespace AND expected epoch ID;
 * v1 data is rejected, never implicitly upgraded or reinterpreted. */
int bl_epoch_v2_encode(BlEpochTickNsV2 value, unsigned char *out, size_t out_len);
int bl_epoch_v2_decode(const unsigned char *in, size_t in_len,
                       const unsigned char expected_namespace[16],
                       uint32_t expected_epoch_id, BlEpochTickNsV2 *out);

#endif
