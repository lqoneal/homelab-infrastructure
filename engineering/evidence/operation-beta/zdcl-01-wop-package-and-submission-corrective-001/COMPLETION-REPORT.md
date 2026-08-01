# ZDCL-01 WOP Package and Submission Corrective — Completion Report

## Result

The authoritative ZDCL-01 WOP package, mission contract, submission-controller
reconciliation, tests, and evidence are ready for one development publication.
No ZDCL runtime implementation is included.

## How to Submit ZDCL-01 to Zeus

1. Submit the mission:

   `zeus mission submit ZDCL-01`

2. Capture and verify the returned submission record:

   `SUBMISSION_JSON="$(zeus mission submit ZDCL-01 --json)"`

   `printf '%s\n' "$SUBMISSION_JSON"`

3. Inspect the staged queue entry:

   `zeus list`

   `zeus show ZDCL-01`

   `zeus status`

4. Inspect readiness and blockers:

   `zeus mission readiness ZDCL-01`

   `zeus mission blockers ZDCL-01`

5. Admission is separate and explicit:

   `ADMISSION_JSON="$(zeus admit-mission start --mode qualification --mission ZDCL-01 --wop WOP-ZDCL-01-FOUNDATION-001 --submitter loneal --principal loneal)"`

   `printf '%s\n' "$ADMISSION_JSON"`

   `ADMISSION_ID="$(printf '%s' "$ADMISSION_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["admission_id"])')"`

6. Start execution only after admission succeeds:

   `EXECUTION_JSON="$(zeus execute-mission start --admission-id "$ADMISSION_ID")"`

   `printf '%s\n' "$EXECUTION_JSON"`

   `EXECUTION_ID="$(printf '%s' "$EXECUTION_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["execution_id"])')"`

7. Inspect status:

   `zeus admit-mission status --admission-id "$ADMISSION_ID"`

   `zeus execute-mission status --execution-id "$EXECUTION_ID"`

8. Resume after interruption:

   `zeus execute-mission resume --execution-id "$EXECUTION_ID"`

9. Diagnose a rejected submission:

   `zeus mission explain ZDCL-01`

   Then inspect the returned rejection evidence through the Stage 1 history
   projection; rejected records are not active queue entries.

The package is development-only and does not mutate `OA-v1.0.0`. Submission
does not approve, admit, or execute protected work.
