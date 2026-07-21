#!/usr/bin/env bash

set -Eeuo pipefail

state="${1:?qualification state path required}"
governance="${2:?governance classification required}"
payload="${3:-}"
[[ -n "$payload" ]] || payload='{}'

[[ "$governance" == "governed" ]] || exit 0

turn_id="$(jq -r '."turn-id" // "unknown"' <<<"$payload" 2>/dev/null || echo unknown)"
message="$(jq -r '."last-assistant-message" // ""' <<<"$payload" 2>/dev/null || true)"
result="PASS"
reason="qualified"

if [[ "${message%%$'\n'*}" != "# Completion Report" ]]; then
    result="FAIL"
    reason="exact-heading"
else
    previous=0
    required=(
        "## Transaction Identification"
        "## Execution Summary"
        "## Repository State"
        "## Commands Executed"
        "## Artifacts Reviewed"
        "## Repository Changes"
        "## Validation Activities"
        "## Deliverables Produced"
        "## Findings"
        "## Analysis"
        "## Recommendations"
        "## Final Certification"
        "## Follow-on Work"
        "## Governance Conformance Review"
    )
    for heading in "${required[@]}"; do
        line="$(grep -n -F -m1 -x "$heading" <<<"$message" | cut -d: -f1 || true)"
        if [[ -z "$line" || "$line" -le "$previous" ]]; then
            result="FAIL"
            reason="missing-or-unordered:${heading#\#\# }"
            break
        fi
        previous="$line"
    done
fi

printf '%s\t%s\t%s\n' "$turn_id" "$result" "$reason" >> "$state"
