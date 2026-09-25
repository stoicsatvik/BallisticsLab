#!/usr/bin/env python3
"""Fail-closed validator for BallisticsLab provenance records.

Input is JSON so validation stays dependency-free and deterministic in CI.
This validates evidence metadata only; it does not validate the truth of claims.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

CLAIM_STATES = {"PROVEN", "SUPPORTED", "NOT_YET_PROVEN", "REJECTED", "BLOCKED"}
RECORD_TYPES = {"legal", "historical", "forensic", "engineering"}
SOURCE_CLASSES = {
    "primary_official", "primary_public_record", "academic",
    "museum_archive", "reputable_secondary",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())

def _date(value):
    return _nonempty(value) and bool(DATE_RE.fullmatch(value))

def _https(value):
    if not _nonempty(value):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)

def validate_record(record):
    errors = []
    for key in ("record_id", "record_type", "claim", "claim_state", "checked_at",
                "source", "corroboration", "uncertainty", "safety"):
        if key not in record:
            errors.append(f"missing:{key}")

    if not _nonempty(record.get("record_id")):
        errors.append("invalid:record_id")
    if record.get("record_type") not in RECORD_TYPES:
        errors.append("invalid:record_type")
    if not _nonempty(record.get("claim")):
        errors.append("invalid:claim")
    if record.get("claim_state") not in CLAIM_STATES:
        errors.append("invalid:claim_state")
    if not _date(record.get("checked_at")):
        errors.append("invalid:checked_at")
    if record.get("record_type") == "legal" and not _nonempty(record.get("jurisdiction")):
        errors.append("legal:jurisdiction_required")

    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    for key in ("title", "publisher"):
        if not _nonempty(source.get(key)):
            errors.append(f"source:{key}_required")
    if not _https(source.get("url")):
        errors.append("source:https_url_required")
    if not _date(source.get("accessed_at")):
        errors.append("source:accessed_at_required")
    if source.get("source_class") not in SOURCE_CLASSES:
        errors.append("source:invalid_source_class")
    archived = source.get("archived_url")
    if archived is not None and not _https(archived):
        errors.append("source:archived_url_must_be_https")

    safety = record.get("safety") if isinstance(record.get("safety"), dict) else {}
    if safety.get("non_operational") is not True:
        errors.append("safety:non_operational_required")

    uncertainty = record.get("uncertainty") if isinstance(record.get("uncertainty"), dict) else {}
    corroboration = record.get("corroboration") if isinstance(record.get("corroboration"), dict) else {}
    ids = corroboration.get("independent_record_ids", [])
    if not isinstance(ids, list):
        errors.append("corroboration:ids_must_be_list")
        ids = []
    unique_ids = {x for x in ids if _nonempty(x)}
    requires = corroboration.get("required") is True or uncertainty.get("disputed") is True
    if requires and len(unique_ids) < 2 and record.get("claim_state") not in {"NOT_YET_PROVEN", "BLOCKED"}:
        errors.append("corroboration:promotion_requires_two_independent_records")

    return sorted(set(errors))

def validate_document(document):
    records = document if isinstance(document, list) else [document]
    errors = {}
    seen = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors[str(index)] = ["invalid:record_must_be_object"]
            continue
        record_errors = validate_record(record)
        record_id = record.get("record_id")
        if _nonempty(record_id):
            if record_id in seen:
                record_errors.append("invalid:duplicate_record_id")
            seen.add(record_id)
        if record_errors:
            errors[str(index)] = sorted(set(record_errors))
    return errors

def main(argv):
    if len(argv) != 2:
        print("usage: validate_provenance.py RECORDS.json", file=sys.stderr)
        return 2
    try:
        document = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    errors = validate_document(document)
    if errors:
        print(json.dumps(errors, indent=2, sort_keys=True))
        return 1
    print("provenance validation: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
