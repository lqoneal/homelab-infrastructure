# BETA-03B Completion Report

## Result

PASS — admission contract resolution was reconciled and published without
starting ZDCL-01 implementation.

## Admit and Execute ZDCL-01

Inspect the existing submission:

```text
zeus show ZDCL-01
zeus list
```

Start qualification admission using the existing submission and capture its
actual ID:

```text
ADMISSION_JSON="$(zeus admit-mission start --mode qualification --mission ZDCL-01 --wop WOP-ZDCL-01-FOUNDATION-001 --submitter loneal --principal loneal --submission-id ZEUS-MISSION-06a7fcf8-a8b3-54bd-8469-0f05f9d41e57 --json)"
printf '%s\n' "$ADMISSION_JSON"
ADMISSION_ID="$(printf '%s' "$ADMISSION_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["admission_id"])')"
```

Inspect admission status:

```text
zeus admit-mission status --admission-id "$ADMISSION_ID"
```

Qualification admission does not grant dispatch. Operational approval must be
obtained through the published governance procedure before operational mode:

```text
OPERATIONAL_ADMISSION_JSON="$(zeus admit-mission start --mode operational --mission ZDCL-01 --wop WOP-ZDCL-01-FOUNDATION-001 --submitter loneal --principal loneal --submission-id ZEUS-MISSION-06a7fcf8-a8b3-54bd-8469-0f05f9d41e57 --json)"
printf '%s\n' "$OPERATIONAL_ADMISSION_JSON"
OPERATIONAL_ADMISSION_ID="$(printf '%s' "$OPERATIONAL_ADMISSION_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["admission_id"])')"
```

Start execution only from an accepted operational admission:

```text
EXECUTION_JSON="$(zeus execute-mission start --admission-id "$OPERATIONAL_ADMISSION_ID")"
printf '%s\n' "$EXECUTION_JSON"
EXECUTION_ID="$(printf '%s' "$EXECUTION_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["execution_id"])')"
zeus execute-mission status --execution-id "$EXECUTION_ID"
zeus execute-mission suspend --execution-id "$EXECUTION_ID" --reason OPERATOR
zeus execute-mission resume --execution-id "$EXECUTION_ID"
```

Diagnose rejection:

```text
zeus admit-mission status --admission-id "$OPERATIONAL_ADMISSION_ID"
zeus mission explain ZDCL-01
```

The shell variables are populated from the preceding verified command output;
no identifier is fabricated or manually substituted.
