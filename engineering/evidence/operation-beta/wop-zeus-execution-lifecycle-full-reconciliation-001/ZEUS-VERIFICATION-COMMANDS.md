# Zeus Verification Commands

Post-publication target commands:

```text
zeus mission snapshot MISSION-ZEUS-QUALIFIED-TRANSITION-BOOTSTRAP-AUTHORITY-CORRECTIVE-001 --json
zeus execute-mission status --execution-id ZEUS-DEVELOPMENT-77567054-9398-54b0-be9a-8c1dddf3ba8b
zeus execute-mission session --execution-id ZEUS-DEVELOPMENT-77567054-9398-54b0-be9a-8c1dddf3ba8b
zeus execute-mission start --admission-id EMM-DEV-ADMISSION-2b3a4a0fb355f01ad03974a8
```

Expected output must expose transaction, admission, execution, reconciliation classification, blockers, and next action. Do not resubmit the WOP.
