/* E476: namespace isolation and explicit version migration rejection.
 * Passing this test does not establish semantic uniqueness or authenticity. */
#include "tickns_epoch_v2.h"
#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static const unsigned char NS_A[16] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
static const unsigned char NS_B[16] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17};
static const unsigned char NS_ZERO[16] = {0};
static const uint32_t COLLIDED_ID = UINT32_C(1781595200);

static void test_identity(void) {
    BlEpochTickNsV2 a, b, c;
    assert(bl_epoch_v2_init((BlTickNs){100}, NS_A, COLLIDED_ID, &a));
    assert(bl_epoch_v2_init((BlTickNs){5}, NS_B, COLLIDED_ID, &b));
    assert(bl_epoch_v2_init((BlTickNs){5}, NS_A, COLLIDED_ID, &c));
    int64_t difference = 777;
    assert(!bl_epoch_v2_difference(a, b, &difference) && difference == 777);
    assert(bl_epoch_v2_difference(a, c, &difference) && difference == 95);
    /* NEGATIVE CONTROL: identical namespace+ID still admits different semantics
     * if a registry incorrectly reuses the pair. This remains unsolved here. */
    assert(bl_epoch_v2_difference(a, c, &difference) && difference == 95);
    BlEpochTickNsV2 sentinel = b;
    assert(!bl_epoch_v2_init((BlTickNs){0}, NS_ZERO, 1, &sentinel));
    assert(memcmp(&sentinel, &b, sizeof(b)) == 0);
    assert(!bl_epoch_v2_init((BlTickNs){0}, NS_A, 0, &sentinel));
    assert(memcmp(&sentinel, &b, sizeof(b)) == 0);
    assert(!bl_epoch_v2_init((BlTickNs){0}, NS_A, 1, NULL));
    assert(!bl_epoch_v2_init((BlTickNs){0}, NULL, 1, &sentinel));
    assert(!bl_epoch_v2_difference(a, b, NULL));
    assert(!bl_epoch_v2_difference(a, (BlEpochTickNsV2){0}, &difference));
    assert(difference == 95);
    assert(!bl_epoch_v2_add((BlEpochTickNsV2){0}, 1, &sentinel));
    assert(memcmp(&sentinel, &b, sizeof(b)) == 0);
    assert(bl_epoch_v2_add(a, 1, &sentinel));
    assert(sentinel.tick.nanoseconds == 101 && sentinel.epoch_id == COLLIDED_ID);
    assert(memcmp(sentinel.namespace_id, NS_A, 16) == 0);
    sentinel = b;
    assert(!bl_epoch_v2_add((BlEpochTickNsV2){.tick={INT64_MAX}, .namespace_id={1}, .epoch_id=1}, 1, &sentinel));
    assert(memcmp(&sentinel, &b, sizeof(b)) == 0);
    assert(!bl_epoch_v2_difference((BlEpochTickNsV2){.tick={INT64_MAX}, .namespace_id={1}, .epoch_id=1},
                                   (BlEpochTickNsV2){.tick={INT64_MIN}, .namespace_id={1}, .epoch_id=1}, &difference));
    assert(difference == 95);
}

static void test_wire(void) {
    BlEpochTickNsV2 value, decoded, sentinel;
    assert(bl_epoch_v2_init((BlTickNs){INT64_MIN}, NS_A, COLLIDED_ID, &value));
    assert(bl_epoch_v2_init((BlTickNs){777}, NS_B, 999, &sentinel));
    unsigned char bytes[BL_EPOCH_V2_WIRE_SIZE], scratch[BL_EPOCH_V2_WIRE_SIZE];
    memset(bytes, 0xA5, sizeof(bytes));
    assert(!bl_epoch_v2_encode(value, bytes, 31));
    for (size_t i = 0; i < sizeof(bytes); ++i) assert(bytes[i] == 0xA5);
    assert(bl_epoch_v2_encode(value, bytes, sizeof(bytes)));
    assert(bytes[0] == 'B' && bytes[1] == 'T' && bytes[2] == 2 && bytes[3] == 1);
    assert(memcmp(bytes + 4, NS_A, 16) == 0);
    decoded = sentinel;
    assert(bl_epoch_v2_decode(bytes, sizeof(bytes), NS_A, COLLIDED_ID, &decoded));
    assert(decoded.tick.nanoseconds == INT64_MIN && decoded.epoch_id == COLLIDED_ID);
    assert(memcmp(decoded.namespace_id, NS_A, 16) == 0);
    decoded = sentinel;
    assert(!bl_epoch_v2_decode(bytes, sizeof(bytes), NS_B, COLLIDED_ID, &decoded));
    assert(memcmp(&decoded, &sentinel, sizeof(decoded)) == 0);
    assert(!bl_epoch_v2_decode(bytes, sizeof(bytes), NS_A, COLLIDED_ID + 1, &decoded));
    assert(memcmp(&decoded, &sentinel, sizeof(decoded)) == 0);
    assert(!bl_epoch_v2_decode(bytes, 16, NS_A, COLLIDED_ID, &decoded));
    assert(memcmp(&decoded, &sentinel, sizeof(decoded)) == 0);
    assert(!bl_epoch_v2_decode(bytes, sizeof(bytes), NS_ZERO, COLLIDED_ID, &decoded));
    assert(!bl_epoch_v2_decode(bytes, sizeof(bytes), NS_A, 0, &decoded));
    assert(!bl_epoch_v2_decode(NULL, sizeof(bytes), NS_A, COLLIDED_ID, &decoded));
    assert(!bl_epoch_v2_decode(bytes, sizeof(bytes), NULL, COLLIDED_ID, &decoded));
    assert(!bl_epoch_v2_decode(bytes, sizeof(bytes), NS_A, COLLIDED_ID, NULL));
    for (size_t i = 0; i < 24; ++i) {
        memcpy(scratch, bytes, sizeof(bytes));
        scratch[i] ^= 1;
        assert(!bl_epoch_v2_decode(scratch, sizeof(scratch), NS_A, COLLIDED_ID, &decoded));
        assert(memcmp(&decoded, &sentinel, sizeof(decoded)) == 0);
    }
    /* Migration must be explicit: a v1-like header is not silently accepted. */
    memcpy(scratch, bytes, sizeof(bytes)); scratch[2] = 1;
    assert(!bl_epoch_v2_decode(scratch, sizeof(scratch), NS_A, COLLIDED_ID, &decoded));
    assert(memcmp(&decoded, &sentinel, sizeof(decoded)) == 0);
    /* NEGATIVE CONTROL: payload corruption is NOT detected by v2. */
    memcpy(scratch, bytes, sizeof(bytes)); scratch[31] ^= 1;
    assert(bl_epoch_v2_decode(scratch, sizeof(scratch), NS_A, COLLIDED_ID, &decoded));
    assert(decoded.tick.nanoseconds == INT64_MIN + 1);
    puts("E476 v2 namespace/identity/version gates: PASS; payload corruption still accepted");
}

static void test_seeded_roundtrips(void) {
    uint64_t state = UINT64_C(476);
    BlEpochTickNsV2 value, decoded;
    unsigned char bytes[BL_EPOCH_V2_WIRE_SIZE];
    for (int i = 0; i < 4096; ++i) {
        /* Frozen xorshift64* input, no implementation-defined signed casts. */
        state ^= state >> 12;
        state ^= state << 25;
        state ^= state >> 27;
        const uint64_t bits = state * UINT64_C(2685821657736338717);
        const int64_t magnitude = (int64_t)(bits >> 1);
        const int64_t tick = (bits & 1U) ? -magnitude : magnitude;
        const uint32_t id = (uint32_t)(i + 1);
        assert(bl_epoch_v2_init((BlTickNs){tick}, NS_A, id, &value));
        assert(bl_epoch_v2_encode(value, bytes, sizeof(bytes)));
        assert(bl_epoch_v2_decode(bytes, sizeof(bytes), NS_A, id, &decoded));
        assert(decoded.tick.nanoseconds == tick && decoded.epoch_id == id);
        assert(memcmp(decoded.namespace_id, NS_A, 16) == 0);
        decoded = value;
        assert(!bl_epoch_v2_decode(bytes, sizeof(bytes), NS_B, id, &decoded));
        assert(decoded.tick.nanoseconds == tick && decoded.epoch_id == id);
    }
    puts("E476 seeded exact wire round trips: 4096/4096; cross-namespace rejects: 4096/4096");
}

int main(void) { test_identity(); test_wire(); test_seeded_roundtrips(); return 0; }
