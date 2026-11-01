#include "tickns_epoch_v2.h"
#include <string.h>

static int namespace_valid(const unsigned char *ns) {
    if (!ns) return 0;
    unsigned char any = 0;
    for (size_t i = 0; i < BL_EPOCH_V2_NAMESPACE_SIZE; ++i) any |= ns[i];
    return any != 0;
}

int bl_epoch_v2_init(BlTickNs tick, const unsigned char namespace_id[16],
                     uint32_t epoch_id, BlEpochTickNsV2 *out) {
    if (!out || !namespace_valid(namespace_id) || epoch_id == 0) return 0;
    BlEpochTickNsV2 candidate = {0};
    candidate.tick = tick;
    candidate.epoch_id = epoch_id;
    memcpy(candidate.namespace_id, namespace_id, BL_EPOCH_V2_NAMESPACE_SIZE);
    *out = candidate;
    return 1;
}

int bl_epoch_v2_add(BlEpochTickNsV2 base, int64_t delta_ns, BlEpochTickNsV2 *out) {
    if (!out || !namespace_valid(base.namespace_id) || base.epoch_id == 0) return 0;
    BlTickNs tick;
    if (!bl_tickns_add(base.tick, delta_ns, &tick)) return 0;
    base.tick = tick;
    *out = base;
    return 1;
}

int bl_epoch_v2_difference(BlEpochTickNsV2 later, BlEpochTickNsV2 earlier, int64_t *out) {
    if (!out || !namespace_valid(later.namespace_id) || later.epoch_id == 0 ||
        later.epoch_id != earlier.epoch_id ||
        memcmp(later.namespace_id, earlier.namespace_id, BL_EPOCH_V2_NAMESPACE_SIZE) != 0) return 0;
    return bl_tickns_difference(later.tick, earlier.tick, out);
}

int bl_epoch_v2_encode(BlEpochTickNsV2 value, unsigned char *out, size_t out_len) {
    if (!out || out_len != BL_EPOCH_V2_WIRE_SIZE ||
        !namespace_valid(value.namespace_id) || value.epoch_id == 0) return 0;
    unsigned char candidate[BL_EPOCH_V2_WIRE_SIZE] = {
        'B', 'T', BL_EPOCH_V2_WIRE_VERSION, BL_EPOCH_V2_WIRE_NS_SCALE
    };
    memcpy(candidate + 4, value.namespace_id, BL_EPOCH_V2_NAMESPACE_SIZE);
    const uint32_t id = value.epoch_id;
    candidate[20] = (unsigned char)(id >> 24);
    candidate[21] = (unsigned char)(id >> 16);
    candidate[22] = (unsigned char)(id >> 8);
    candidate[23] = (unsigned char)id;
    if (!bl_tickns_encode_be(value.tick, candidate + 24)) return 0;
    memcpy(out, candidate, BL_EPOCH_V2_WIRE_SIZE);
    return 1;
}

int bl_epoch_v2_decode(const unsigned char *in, size_t in_len,
                       const unsigned char expected_namespace[16],
                       uint32_t expected_epoch_id, BlEpochTickNsV2 *out) {
    if (!in || !out || in_len != BL_EPOCH_V2_WIRE_SIZE ||
        !namespace_valid(expected_namespace) || expected_epoch_id == 0 ||
        in[0] != 'B' || in[1] != 'T' ||
        in[2] != BL_EPOCH_V2_WIRE_VERSION || in[3] != BL_EPOCH_V2_WIRE_NS_SCALE ||
        memcmp(in + 4, expected_namespace, BL_EPOCH_V2_NAMESPACE_SIZE) != 0) return 0;
    const uint32_t id = ((uint32_t)in[20] << 24) | ((uint32_t)in[21] << 16) |
                        ((uint32_t)in[22] << 8) | (uint32_t)in[23];
    if (id != expected_epoch_id) return 0;
    BlTickNs tick;
    if (!bl_tickns_decode_be(in + 24, &tick)) return 0;
    return bl_epoch_v2_init(tick, expected_namespace, id, out);
}
