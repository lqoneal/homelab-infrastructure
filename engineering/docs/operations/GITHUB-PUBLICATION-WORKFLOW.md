# GitHub Publication Workflow

This document defines the separated roles and repeatable publication path for
the Homelab authority repository.

## Repository roles

- `/data/engineering/repositories/homelab` is the pull-only authority checkout.
  Its `origin` is `git@github.com:lqoneal/homelab-infrastructure.git` and its
  `main` branch tracks `origin/main`.
- `/home/loneal/homelab-oa15` is the writable engineering clone. Its `origin`
  is canonical GitHub and its `authority` remote fetches the `/data` checkout.
  The `authority` push URL is deliberately non-routable.
- Local `main` always tracks `origin/main`. Publication branches are pushed by
  explicit refspec and never with `-u` from `main`.

## Standard publication path

```text
git fetch origin main
git merge-base --is-ancestor origin/main HEAD
git push origin HEAD:refs/heads/agent/<publication-branch>
gh pr create --repo lqoneal/homelab-infrastructure --base main --head agent/<publication-branch> --draft
```

Git transport and API authentication are independent. SSH qualifies Git
transport with `ssh -T git@github.com` and `git ls-remote`; `gh auth status`,
`gh api user`, and `gh repo view` qualify API authentication. Tokens and
credential contents must never be printed, logged, or committed.

After merge, update the authority checkout with `git pull --ff-only`, then run
EOS synchronization and validation there.
