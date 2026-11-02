# E492 | A MAC checks bytes only under independently trusted keys and replay state

Date: 2026-11-02. Research-only continuation of E491, stacked on draft PR #37.

## Question and tested hypothesis

Can a bounded canonical HMAC-SHA256 envelope reject tampered snapshot bytes, wrong namespaces, attacker-chosen keys and stale generations without modifying files? Under what assumptions does the claim fail?

**SUPPORTED for 17 synthetic local stdlib unittest controls.** A domain-separated MAC covers canonical format, namespace, generation and SHA-256 digest of a caller-supplied byte string. Verification uses constant-time digest comparisons, duplicate-key rejection, exact canonical JSON, bounded envelope/snapshot sizes, a 32-byte minimum external secret, and an externally trusted minimum generation. It returns only a diagnostic status and never loads, promotes, cleans up or publishes snapshots.

## Falsifying negative controls

1. **Attacker-chosen key:** A forged MAC is rejected with the separately trusted test key, but **passes if the verifier is tricked into trusting the attacker's key**. Therefore this module cannot establish key provenance or independent issuer identity. A shared-key verifier can itself forge attestations.
2. **Replay:** A valid generation-7 attestation is rejected when a trusted floor is 8, but **passes when the caller resets the floor to 0**. A MAC alone cannot prevent rollback after restart.
3. **Hard-link provenance:** An unsigned externally created hard link fails the MAC, but **a valid signed snapshot hard-linked from outside the trusted root passes**. Cryptographic content integrity does not establish pathname origin, ownership, writer quiescence or durability.
4. The test snapshot is intentionally synthetic and **not an E477-valid registry**. A MAC-valid result does not imply E477 structural validation or scientific correctness.

## Reproduction

```bash
python -m py_compile research/e492_checkpoint_mac_gate.py tests/test_e492_checkpoint_mac_gate.py
python -m unittest discover -s tests -p 'test_e492_checkpoint_mac_gate.py' -v
```

Local Python 3.11: **17/17 tests passed**, compilation passed. Source and test Git blobs match the locally executed files: `dbd671f7ac3953df3738026b86b909e74aabaa3e` and `56f77ce6f2756963abd4ad42d5818b174aa1c4e5`. Exact-head Actions and inherited suite should be checked separately.

## Strict boundaries

- HMAC is symmetric: it does not distinguish issuer from verifier. No production key storage, key rotation, signer authorization, public-key identity or secret distribution exists.
- Trusted namespace, trusted key and a durable monotonic generation floor must be provisioned outside the data under inspection.
- The MAC authenticates the provided bytes under those assumptions only; the caller must independently run E477 pinned structural validation.
- No persistent replay state, power-loss test, concurrent writer protocol, automatic cleanup, snapshot promotion, deployment, ballistics physics or weapons application is introduced.
- This is a falsification harness, **not a security-certified checkpoint protocol**.

## Next gate

Before any recovery/promotion design, test an externally pinned asymmetric issuer public key and durable monotonic floor, with key substitution, valid signed replay, malicious hard links, concurrent noncooperating writers and process-death controls. Keep this PR draft and unmerged.
