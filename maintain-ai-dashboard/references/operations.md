# Operations runbook

Use this reference only for server maintenance. Commands assume `bootstrap_ssh.py --check` and `preflight.py` have succeeded.

## Authorization and evidence

Classify the request before acting:

- Inspect, explain, review, or diagnose: read-only checks only.
- Change, fix, deploy, add, or delete: perform only the requested mutation and its normal backup/test/verification steps.
- A request to wait or monitor does not authorize a restart, deployment, or data change.

Never expose `.env`, private keys, cookies, database secrets, Git credential files, or credential-bearing remote URLs in commands or output.

## Obtain a working copy

Prefer an existing trusted local project copy. If none exists, make a new local task directory and download `/home/wr/ai-dashboard/app` while excluding `.env`, build output, caches and dependencies. Use `rsync` when available; otherwise copy explicit source files with `scp`. Treat the server deployment as a temporary baseline, not a replacement for a long-term Git source repository.

Before editing, record the live Compose state and download only what is needed. Use `apply_patch` for local edits. Preserve unrelated local and server changes.

## Read-only diagnosis

1. Run `scripts/preflight.py` and retain its sanitized report.
2. Inspect container status and only the relevant bounded log tail.
3. Query SQLite with URI `mode=ro` and `PRAGMA query_only=ON`.
4. For Git AI issues, inspect the configured branch HEAD, commit or range and `refs/notes/ai`; separate worktree status, landed attribution and usage/token data.
5. Explain the evidence and proof boundary before proposing a mutation.

Do not restart services merely to diagnose. Do not run synchronization repeatedly while a previous run is active.

## Pre-deployment gate

Proceed only when the user requested the change, tests are defined, preflight reports sync stopped, and exact files are known.

Create a timestamped backup directory below `/home/wr/ai-dashboard/backups`. Copy the current application directory into it. Back up SQLite with Python's `sqlite3.Connection.backup()` API, then run `PRAGMA quick_check` against the backup. A direct filesystem copy of a live SQLite database is not an acceptable backup.

Keep the backup until the user accepts the deployment. Report its exact path without including secrets.

## Test and deploy

Run checks proportional to the change:

```bash
cd server && python3 -m py_compile app.py test_app.py
cd server && python3 -m unittest test_app.py
npm test
npm run build
```

Upload only changed, verified files into `/home/wr/ai-dashboard/app`. Do not upload `.env`, local credentials, `node_modules`, caches, generated output or an entire unrelated workspace.

Rebuild through the existing Compose file and project directory. Do not invent a parallel `nohup`, systemd, or container launch path. A full rebuild is authorized only as the normal deployment step for the requested code change.

## Acceptance and rollback

After deployment:

1. Require both Compose services to be `running`.
2. Require `/api/health` and the web page to respond successfully.
3. Re-run `preflight.py`; confirm SQLite `quick_check`, backup readiness and zero duplicate canonical remotes.
4. Check bounded new logs for startup exceptions.
5. Exercise the exact changed behavior. For statistics, compare project, branch, commit SHA and month boundaries rather than only the final score.

If acceptance fails, stop additional changes. Restore the scoped application files from the timestamped backup and rebuild the original services. Restore SQLite only if the failed change mutated database state or schema; stop writers first and preserve the failed database for diagnosis.

## Project and repository changes

Adding a project clones it to `/home/wr/git/<repository-name>` using the server's Git credentials. Reject an existing target directory or canonical remote. Configure one or more actual remote branch names; a commit reachable from several selected branches must count once by SHA.

Before deleting:

1. Require sync stopped and create a fresh SQLite backup.
2. Resolve the exact project ID, canonical remote, target path and repository type.
3. Check `git status`, untracked files, unpushed commits and `git worktree list --porcelain`.
4. For an ordinary clean clone, use the dashboard deletion action so it moves the directory to `/home/wr/git/.ai-dashboard-trash` and deletes configuration transactionally.
5. For a linked worktree, stop and obtain explicit direction. Use Git worktree operations from its common repository; never use recursive filesystem deletion.

If only a duplicate database configuration exists for the same remote, preserve every repository/worktree directory and remove only the confirmed duplicate configuration in a transaction after backup. Verify a subsequent source scan does not recreate it.

## Stopping conditions

Stop and report instead of improvising when the host fingerprint changes, batch-mode SSH fails, sync remains active, the database backup or integrity check fails, a repository is dirty, the remote/path identity differs, an unexpected migration is required, or acceptance cannot be restored with the prepared backup.
