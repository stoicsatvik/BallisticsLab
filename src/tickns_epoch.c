#include "tickns_epoch.h"
#include <stddef.h>

int bl_epoch_tickns_init(BlTickNs tick, uint32_t epoch_id, BlEpochTickNs *out) {
    if (!out || epoch_id == 0) return 0;
    const BlEpochTickNs candidate = {tick, epoch_id};
    *out = candidate;
    return 1;
}

int bl_epoch_tickns_add(BlEpochTickNs base, int64_t delta_ns, BlEpochTickNs *out) {
    if (!out || base.epoch_id == 0) return 0;
    BlTickNs candidate;
    if (!bl_tickns_add(base.tick, delta_ns, &candidate)) return 0;
    const BlEpochTickNs result = {candidate, base.epoch_id};
    *out = result;
    return 1;
}

int bl_epoch_tickns_difference(BlEpochTickNs later, BlEpochTickNs earlier, int64_t *out) {
    if (!out || later.epoch_id == 0 || later.epoch_id != earlier.epoch_id) return 0;
    return bl_tickns_difference(later.tick, earlier.tick, out);
}

int bl_epoch_tickns_encode(BlEpochTickNs value, unsigned char out[BL_EPOCH_WIRE_SIZE]) {
    if (!out || value.epoch_id == 0) return 0;
    unsigned char candidate[BL_EPOCH_WIRE_SIZE] = {
        'B', 'T', BL_EPOCH_WIRE_VERSION, BL_EPOCH_WIRE_NS_SCALE
    };
    const uint32_t id = value.epoch_id;
    candidate[4] = (unsigned char)(id >> 24);
    candidate[5] = (unsigned char)(id >> 16);
    candidate[6] = (unsigned char)(id >> 8);
    candidate[7] = (unsigned char)id;
    if (!bl_tickns_encode_be(value.tick, candidate + 8)) return 0;
    for (int i = 0; i < BL_EPOCH_WIRE_SIZE; ++i) out[i] = candidate[i];
    return 1;
}

int bl_epoch_tickns_decode(const unsigned char in[BL_EPOCH_WIRE_SIZE],
                           uint32_t expected_epoch_id, BlEpochTickNs *out) {
    if (!in || !out || expected_epoch_id == 0 ||
        in[0] != 'B' || in[1] != 'T' ||
        in[2] != BL_EPOCH_WIRE_VERSION || in[3] != BL_EPOCH_WIRE_NS_SCALE) return 0;
    const uint32_t id = ((uint32_t)in[4] << 24) | ((uint32_t)in[5] << 16) |
                        ((uint32_t)in[6] << 8) | (uint32_t)in[7];
    if (id != expected_epoch_id) return 0;
    BlTickNs tick;
    if (!bl_tickns_decode_be(in + 8, &tick)) return 0;
    const BlEpochTickNs candidate = {tick, id};
    *out = candidate;
    return 1;
}
