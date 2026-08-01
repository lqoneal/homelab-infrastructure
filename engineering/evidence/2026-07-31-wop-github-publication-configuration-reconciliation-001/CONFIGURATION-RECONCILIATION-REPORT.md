# GitHub Publication Configuration Reconciliation Report

## Reconciled changes

- Set `origin` in the writable clone to canonical GitHub SSH.
- Removed the secondary `github` publication remote.
- Added `authority` pointing to the `/data` checkout.
- Protected the `authority` remote from pushes with a non-routable push URL.
- Restored `main -> origin/main` tracking.
- Set GitHub CLI Git protocol to SSH at host and global levels.
- Backed up GitHub CLI and global Git configuration with owner-only permissions.
- Published the reproducible workflow in `engineering/docs/operations/GITHUB-PUBLICATION-WORKFLOW.md`.

No Operational Alpha state, capability, Mission Knowledge Model, EMM, roadmap,
runtime, lifecycle, or implementation file was changed by this configuration reconciliation.
