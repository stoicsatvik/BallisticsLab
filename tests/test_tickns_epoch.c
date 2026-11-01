#include "tickns_epoch.h"
#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void check_wire(int64_t ns, uint32_t id) {
    BlEpochTickNs a = {{ns}, id}, b = {{77}, 999};
    unsigned char bytes[BL_EPOCH_WIRE_SIZE];
    assert(bl_epoch_tickns_encode(a, bytes));
    assert(bytes[0] == 'B' && bytes[1] == 'T' && bytes[2] == 1 && bytes[3] == 1);
    assert(bl_epoch_tickns_decode(bytes, id, &b));
    assert(b.tick.nanoseconds == ns && b.epoch_id == id);
    b.tick.nanoseconds = 77;
    b.epoch_id = 999;
    assert(!bl_epoch_tickns_decode(bytes, id == 1 ? 2 : 1, &b));
    assert(b.tick.nanoseconds == 77 && b.epoch_id == 999);
    for (int pos = 0; pos < 4; ++pos) {
        unsigned char saved = bytes[pos];
        bytes[pos] ^= 1;
        assert(!bl_epoch_tickns_decode(bytes, id, &b));
        assert(b.tick.nanoseconds == 77 && b.epoch_id == 999);
        bytes[pos] = saved;
    }
    bytes[4] ^= 1;
    assert(!bl_epoch_tickns_decode(bytes, id, &b));
    assert(b.tick.nanoseconds == 77 && b.epoch_id == 999);
}

int main(void) {
    BlEpochTickNs a = {{0}, 0}, b = {{77}, 999};
    assert(!bl_epoch_tickns_init((BlTickNs){1}, 0, &b));
    assert(b.tick.nanoseconds == 77 && b.epoch_id == 999);
    assert(bl_epoch_tickns_init((BlTickNs){INT64_MIN}, 42, &a));
    assert(a.epoch_id == 42 && a.tick.nanoseconds == INT64_MIN);
    assert(!bl_epoch_tickns_add(a, -1, &b));
    assert(b.tick.nanoseconds == 77 && b.epoch_id == 999);
    assert(bl_epoch_tickns_add(a, 1, &b));
    assert(b.tick.nanoseconds == INT64_MIN + 1 && b.epoch_id == 42);
    int64_t diff = 73;
    assert(!bl_epoch_tickns_difference(a, (BlEpochTickNs){{0}, 43}, &diff) && diff == 73);
    assert(!bl_epoch_tickns_difference(a, (BlEpochTickNs){{0}, 0}, &diff) && diff == 73);
    assert(!bl_epoch_tickns_difference((BlEpochTickNs){{INT64_MAX},42}, a, &diff) && diff == 73);
    assert(bl_epoch_tickns_difference(b, a, &diff) && diff == 1);
    assert(!bl_epoch_tickns_add((BlEpochTickNs){{0},0}, 1, &b));
    assert(!bl_epoch_tickns_add(a, 1, NULL));
    assert(!bl_epoch_tickns_difference(a, a, NULL));
    unsigned char bytes[BL_EPOCH_WIRE_SIZE];
    memset(bytes, 0xAA, sizeof(bytes));
    assert(!bl_epoch_tickns_encode((BlEpochTickNs){{1},0}, bytes));
    for (int i = 0; i < BL_EPOCH_WIRE_SIZE; ++i) assert(bytes[i] == 0xAA);
    assert(!bl_epoch_tickns_decode(bytes, 0, &b));
    assert(!bl_epoch_tickns_decode(NULL, 42, &b));
    assert(!bl_epoch_tickns_decode(bytes, 42, NULL));
    check_wire(INT64_MIN, 42);
    check_wire(INT64_MAX, UINT32_MAX);
    check_wire(-1, 1);
    check_wire(0, 0x01020304U);
    check_wire(1, 1);
    puts("E474 deterministic epoch envelope: PASS");
    return 0;
}
