/* E475 negative control: an epoch ID collision bypasses E474's identity guard.
 * Both values intentionally represent DIFFERENT caller-defined zero points.
 * Passing this test means the known limitation is reproduced, not fixed. */
#include "tickns_epoch.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

int main(void) {
    const uint32_t collided_id = UINT32_C(1781595200);
    const BlEpochTickNs epoch_a = {{100}, collided_id};
    const BlEpochTickNs epoch_b = {{5}, collided_id};
    int64_t difference = INT64_C(777);
    /* Semantically invalid across epochs, but the API only sees equal IDs. */
    assert(bl_epoch_tickns_difference(epoch_a, epoch_b, &difference));
    assert(difference == 95);

    unsigned char encoded[BL_EPOCH_WIRE_SIZE];
    assert(bl_epoch_tickns_encode(epoch_b, encoded));
    BlEpochTickNs decoded = {{777}, 999};
    assert(bl_epoch_tickns_decode(encoded, collided_id, &decoded));
    assert(decoded.tick.nanoseconds == 5 && decoded.epoch_id == collided_id);

    /* Correctly distinguish different IDs: preserve the output on failure. */
    difference = 777;
    const BlEpochTickNs distinct_id = {{5}, collided_id + 1};
    assert(!bl_epoch_tickns_difference(epoch_a, distinct_id, &difference));
    assert(difference == 777);
    puts("E475 collision negative control reproduced: semantic mismatch ACCEPTED");
    return 0;
}
