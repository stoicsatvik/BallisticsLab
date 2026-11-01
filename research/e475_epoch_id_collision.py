"""E475: falsify 32-bit hashed epoch identity and test local registry invariants.

Synthetic, reproducible identity experiment. This does not exercise the C API,
model real epoch definitions, or estimate field failure frequency.
"""
import hashlib
import json
import math
import random

SEED = 475
COUNT = 200_000


def digest_id(definition: bytes, bits: int) -> int:
    return int.from_bytes(hashlib.blake2b(definition, digest_size=bits // 8).digest(), 'big')


def experiment(seed: int = SEED, count: int = COUNT) -> dict:
    rng = random.Random(seed)
    seen = {32: {}, 64: {}, 128: {}}
    collisions = {32: 0, 64: 0, 128: 0}
    first_32_collision = None
    zero_32 = 0
    for index in range(count):
        # Opaque synthetic definitions. Random bytes do NOT prove semantic uniqueness.
        definition = b'epoch-definition-v1|ns|' + rng.getrandbits(128).to_bytes(16, 'big')
        for bits in (32, 64, 128):
            identity = digest_id(definition, bits)
            previous = seen[bits].get(identity)
            if previous is not None:
                collisions[bits] += 1
                if bits == 32 and first_32_collision is None:
                    first_index, first_definition = previous
                    assert first_definition != definition
                    first_32_collision = {'id': identity, 'first_index': first_index, 'second_index': index}
            else:
                seen[bits][identity] = (index, definition) if bits == 32 else index
            if bits == 32 and identity == 0:
                zero_32 += 1

    assert first_32_collision is not None, 'Frozen synthetic cohort did not falsify 32-bit uniqueness'
    # The native C negative control checks the E474 same-ID guard separately.
    assert first_32_collision['first_index'] != first_32_collision['second_index']

    # A registry can reject inconsistent re-use when BOTH definitions are known.
    registry = {}
    registry_id = first_32_collision['id']
    definition_a, definition_b = b'epoch/A|ns', b'epoch/B|ns'
    registry[registry_id] = definition_a
    def register(epoch_id: int, definition: bytes) -> bool:
        if epoch_id == 0:
            return False
        existing = registry.get(epoch_id)
        if existing is not None and existing != definition:
            return False
        registry[epoch_id] = definition
        return True
    assert not register(registry_id, definition_b)  # reject conflicting re-registration
    assert register(registry_id, definition_a)  # allow idempotent registration
    assert not register(0, definition_a)
    assert registry[registry_id] == definition_a

    # Independent uncoordinated sequential allocators collide immediately.
    left_ids = set(range(1, 1001))
    right_ids = set(range(1, 1001))
    independent_allocator_overlap = len(left_ids & right_ids)
    assert independent_allocator_overlap == 1000

    return {
        'seed': seed,
        'synthetic_definitions': count,
        'digest_collisions': {str(k): v for k, v in collisions.items()},
        'first_32_bit_collision': first_32_collision,
        'zero_32_bit_ids': zero_32,
        'birthday_probability_at_least_one_collision': {
            str(bits): -math.expm1(-count * (count - 1) / (2 * (2 ** bits)))
            for bits in (32, 64, 128)
        },
        'uncoordinated_sequential_allocator_overlap': independent_allocator_overlap,
        'local_registry_conflict_rejected': True,
        'source_equivalent_same_id_guard_fails_to_detect_semantic_collision': True,
        'scope': 'synthetic identity experiment; not native C, not field-rate evidence',
    }


if __name__ == '__main__':
    print(json.dumps(experiment(), indent=2, sort_keys=True))
