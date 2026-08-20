---
name: maintain-ai-dashboard
description: Use when Codex needs to access, diagnose, update, deploy, recover, or audit the internal Git AI reimbursement dashboard at 172.17.0.252, especially from a new computer or when SSH keys, Docker Compose, SQLite, projects, branches, or reimbursement statistics are involved.
---

# Maintain AI Dashboard

Maintain the internal dashboard through a verified SSH key connection. Treat the deployed service and its reimbursement evidence as production data.

## Connection gate

Locate this Skill directory and use the available Python 3 launcher (`python3`, `python`, or `py -3`). Examples below use `python3`:

```bash
python3 scripts/bootstrap_ssh.py --check
```

If it is not ready, run `python3 scripts/bootstrap_ssh.py --setup`. This may request the server password once through the SSH prompt. Do not accept a changed host fingerprint, store the password, disable host-key checking, copy a private key between computers, or continue until this succeeds:

```bash
ssh -o BatchMode=yes WRLinuxServer true
```

The server is reachable only from the company network or VPN. A routing or network failure is not an SSH credential failure.

## Route the task

- Read [references/project-background.md](references/project-background.md) for architecture, Git AI semantics, scoring, branches, worktrees, and current operating assumptions.
- Run `python3 scripts/preflight.py --alias WRLinuxServer` before any server diagnosis or mutation.
- Read [references/operations.md](references/operations.md) before changing code, configuration, projects, containers, or SQLite data.

## Operating contract

1. Diagnose read-only first and distinguish current evidence from historical assumptions.
2. Treat a user request to inspect or explain as read-only. Require an explicit change/deploy/delete request before mutating production.
3. Before an authorized mutation, require preflight success, confirm dashboard sync is not running, and create recoverable application and SQLite backups.
4. Edit and test a local copy. Upload only scoped files; never edit production source ad hoc through an SSH shell.
5. Verify API, web, containers, database integrity, project uniqueness, and synchronization after deployment. Roll back on failed acceptance.

Never print or copy `.env`, cookies, passwords, private keys, Git credentials, or credential-bearing remote URLs. Do not treat Git linked worktrees as ordinary clone directories. Do not infer current project counts or health from this Skill; use live preflight output.

## Quick reference

| Need | Action |
|---|---|
| New computer | `bootstrap_ssh.py --setup` |
| Connection proof | `bootstrap_ssh.py --check` |
| Current health | `preflight.py --alias WRLinuxServer` |
| Explain data or scoring | Read `project-background.md` |
| Deploy, repair, delete, restore | Read `operations.md` |

## Common mistakes

- Password login works but batch key proof fails: finish bootstrap; do not proceed temporarily.
- `172.17.0.252` is unreachable: check company LAN/VPN and host routing before changing SSH files.
- Sync is running: wait for it to finish before database or project changes.
- Two directories share one remote: inspect `git worktree list`; do not delete by directory name alone.
- Git AI shows zero: verify revision and `refs/notes/ai`; do not attribute historical code by inference.
