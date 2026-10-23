# Source provenance schema v1

## Purpose

This schema defines the minimum evidence record for BallisticsLab legal and completed historical/forensic research. It is intentionally non-operational: records may support scientific, legal, historical, and engineering literacy, but must not encode attack reconstruction, targeting, security vulnerabilities, evasion, or actionable replication guidance.

## Claim states

Every claim MUST use exactly one state: `PROVEN`, `SUPPORTED`, `NOT_YET_PROVEN`, `REJECTED`, or `BLOCKED`.

`PROVEN` is reserved for claims independently derived or reproduced by repository evidence. A credible external source normally supports `SUPPORTED`, not `PROVEN`.

## Required record

Each evidence record MUST contain:

```yaml
record_id: string
record_type: legal | historical | forensic | engineering
claim: string
claim_state: PROVEN | SUPPORTED | NOT_YET_PROVEN | REJECTED | BLOCKED
jurisdiction: string | null
event_date: YYYY-MM-DD | null
checked_at: YYYY-MM-DD
source:
  title: string
  publisher: string
  url: https://...
  published_at: YYYY-MM-DD | null
  accessed_at: YYYY-MM-DD
  source_class: primary_official | primary_public_record | academic | museum_archive | reputable_secondary
  locator: string | null
  archived_url: https://... | null
corroboration:
  required: boolean
  independent_record_ids: [string]
uncertainty:
  disputed: boolean
  notes: string | null
safety:
  non_operational: true
  redactions: [string]
```

## Identity and immutability

`record_id` MUST be stable and unique. Once a record is cited by another artifact, source URL, source locator, quoted factual proposition, event date, and claim state MUST NOT be silently rewritten. Material corrections require a new record or an explicit supersession link in the consuming artifact.

URLs MUST use HTTPS. The `checked_at` and `accessed_at` dates MUST reflect actual checks; they must never be backfilled from memory.

## Source hierarchy

For Indian legal claims, prefer current primary official sources such as India Code, Ministry of Home Affairs, Gazette notifications, the Arms Act, Arms Rules, and official amendments. Secondary summaries may aid discovery but MUST NOT be the sole authority for a legal conclusion when a primary source is available.

For historical or forensic claims, prefer public primary records, official reports, academic literature, museum/archive material, and reputable secondary sources. A disputed material claim MUST set `corroboration.required: true` and reference at least two independent evidence records before promotion beyond `NOT_YET_PROVEN`.

## Fail-closed rules

A record is invalid if it lacks a source URL, publisher, access date, source class, claim state, or explicit non-operational safety marker. Legal records without a jurisdiction are invalid. Disputed records that require corroboration but have fewer than two independent record IDs remain `NOT_YET_PROVEN` or `BLOCKED`.

No record may contain construction dimensions, manufacturing recipes, conversion instructions, attack plans, firing positions, security weaknesses, evasion routes, target-selection procedures, lethality optimization, private personal data, leaked material, or restricted manuals.

## Historical case-study gate

A case study may be added only after its evidence records satisfy this schema. The study must separate verified timeline, publicly established system identity when relevant, documented evidence, disputed claims, engineering/legal lesson, and source quality. Uncertainty must remain visible rather than being collapsed into a single narrative.

## Versioning

This document is schema version `1`. Future incompatible changes require a new version and migration notes. Existing evidence records retain the schema version under which they were created.