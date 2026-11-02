"""E492 research-only snapshot MAC experiment. NOT a checkpoint authority.

The issuer and verifier share a secret. A verifier possessing that secret can
forge attestations, so this cannot establish independent issuer identity.
The trusted key, namespace and monotonic generation floor come from outside.
No file writes, snapshot promotion, cleanup or automatic recovery.
"""
from dataclasses import dataclass
import hashlib
import hmac
import json
import re

FORMAT = 'ballisticslab-checkpoint-mac-v1'
DOMAIN = b'ballisticslab-checkpoint-mac-v1\x00'
MAX_SNAPSHOT_BYTES = 1_048_576
MAX_ATTESTATION_BYTES = 1024
MAX_GENERATION = (1 << 63) - 1
FIELDS = frozenset(('format', 'namespace', 'generation', 'sha256', 'mac'))
HEX64 = re.compile(r'[0-9a-f]{64}\Z')


@dataclass(frozen=True)
class AttestationResult:
    status: str  # mac_valid, rejected, inspection_error
    detail: str
    generation: int | None = None
    snapshot_sha256: str | None = None


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def _unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate key')
        obj[key] = value
    return obj


def _validate_context(snapshot, namespace, key, generation):
    if type(snapshot) is not bytes or len(snapshot) > MAX_SNAPSHOT_BYTES:
        raise ValueError('invalid snapshot bytes')
    if type(namespace) is not bytes or len(namespace) != 16 or not any(namespace):
        raise ValueError('invalid namespace')
    if type(key) is not bytes or len(key) < 32:
        raise ValueError('invalid externally supplied secret')
    if type(generation) is not int or not 0 <= generation <= MAX_GENERATION:
        raise ValueError('invalid generation')


def issue_test_mac(snapshot: bytes, namespace: bytes, generation: int, secret: bytes) -> bytes:
    """Construct a synthetic MAC; not production issuance or key management."""
    _validate_context(snapshot, namespace, secret, generation)
    fields = {'format': FORMAT, 'namespace': namespace.hex(), 'generation': generation,
              'sha256': hashlib.sha256(snapshot).hexdigest()}
    mac = hmac.new(secret, DOMAIN + _canonical(fields), hashlib.sha256).hexdigest()
    envelope = _canonical({**fields, 'mac': mac})
    if len(envelope) > MAX_ATTESTATION_BYTES:
        raise ValueError('oversized envelope')
    return envelope


def verify_test_mac(snapshot: bytes, envelope: bytes, expected_namespace: bytes,
                    trusted_secret: bytes, minimum_generation: int) -> AttestationResult:
    """Read-only MAC gate; caller MUST separately validate E477 snapshot structure.

    A trusted monotonic generation floor must be maintained independently;
    accepting floor=0 after every restart does NOT prevent rollback.
    """
    try:
        _validate_context(snapshot, expected_namespace, trusted_secret, minimum_generation)
        if type(envelope) is not bytes or not 0 < len(envelope) <= MAX_ATTESTATION_BYTES:
            raise ValueError('invalid envelope length/type')
        obj = json.loads(envelope.decode('ascii'), object_pairs_hook=_unique_pairs)
        if not isinstance(obj, dict) or set(obj) != FIELDS or _canonical(obj) != envelope:
            return AttestationResult('rejected', 'noncanonical or unexpected envelope fields')
        gen = obj['generation']
        if (obj['format'] != FORMAT or obj['namespace'] != expected_namespace.hex()
                or type(gen) is not int or not 0 <= gen <= MAX_GENERATION
                or type(obj['sha256']) is not str or not HEX64.fullmatch(obj['sha256'])
                or type(obj['mac']) is not str or not HEX64.fullmatch(obj['mac'])):
            return AttestationResult('rejected', 'invalid attestation fields')
        fields = {key: obj[key] for key in ('format', 'namespace', 'generation', 'sha256')}
        expected_mac = hmac.new(trusted_secret, DOMAIN + _canonical(fields), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_mac, obj['mac']):
            return AttestationResult('rejected', 'MAC mismatch')
        digest = hashlib.sha256(snapshot).hexdigest()
        if not hmac.compare_digest(digest, obj['sha256']):
            return AttestationResult('rejected', 'snapshot digest mismatch')
        if gen < minimum_generation:
            return AttestationResult('rejected', 'generation below trusted floor')
        return AttestationResult('mac_valid', 'MAC only; issuer, durability and path provenance unverified', gen, digest)
    except (ValueError, UnicodeError, TypeError, OverflowError):
        return AttestationResult('inspection_error', 'invalid input or envelope encoding')
