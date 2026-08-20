# Project background

## Purpose and topology

The AI 编程报销看板 turns Git AI line attribution into auditable monthly reimbursement evidence. Employees use the web page to view or capture their own result; administrators configure repositories, branches, filters, identities, scoring, and synchronization.

| Item | Current location |
|---|---|
| SSH | `WRLinuxServer` → `wr@172.17.0.252:22` |
| Web | `http://172.17.0.252:18088` |
| API | `http://172.17.0.252:18089` |
| Deployed source | `/home/wr/ai-dashboard/app` |
| SQLite data | `/home/wr/ai-dashboard/data/dashboard.sqlite3` |
| Backups | `/home/wr/ai-dashboard/backups` and `/home/wr/ai-dashboard/data/backups` |
| Git repositories | `/home/wr/git` |
| Git AI | `/home/wr/.git-ai/bin/git-ai` |
| Containers | `ai-reimbursement-web`, `ai-reimbursement-api` |

The web service is a TypeScript/Vinext application. The API is FastAPI/Python. Docker Compose mounts the SQLite data, repository root, Git AI installation, Git configuration and credentials into the API container. Credentials belong to the server and must never be copied into the Skill or maintenance reports.

## Git AI evidence semantics

Git AI 1.6.22 records explicit line attribution in Git Notes under `refs/notes/ai`. It does not infer who or what created historical code before attribution was recorded. `git ai stats` is revision-scoped: without a revision it describes the current `HEAD`; ranges and individual commits must be named explicitly.

The dashboard synchronization process fetches every configured remote branch plus `refs/notes/ai`, enumerates non-merge commits since the project start time, and stores attributed additions with commit, author, file, tool/model and branch evidence. Token or tool activity is supporting context, not proof that code landed. Shipped line attribution and usage data must remain separate concepts.

Unknown additions remain in the penetration denominator. A missing Note, an uninstrumented AI tool, or code created before Git AI was installed can therefore reduce the rate; the dashboard must not relabel those lines as AI by assumption.

## Natural-month scoring

The selected calendar month is the formal reimbursement period. The current rule version is `V0.3`.

| Dimension | Bands | Score |
|---|---|---|
| Effective AI lines `L` | `<50`, `50–199`, `200–499`, `500–999`, `1000–1999`, `≥2000` | `0, 10, 20, 30, 40, 45` |
| Effective work items `M` | `0`, `1`, `2`, `3`, `≥4` | `0, 5, 12, 18, 25` |
| Active output days `D` | `0`, `1–2`, `3–4`, `5–8`, `≥9` | `0, 3, 7, 11, 15` |
| AI penetration `R` | `<20%`, `20–39%`, `40–59%`, `60–79%`, `≥80%` | `0, 5, 9, 12, 15` |

`R = AI-attributed additions / Git-added lines`. An effective work item is one project-date pair containing attributed AI or human additions; several commits to the same project on one day remain one item. Four items is the maximum scoring band because the dimension measures breadth of delivered work, not commit fragmentation.

Eligibility requires all three gates: `R ≥ 50%`, `D ≥ 3`, and total score `S ≥ 62`. A score from 62 through 99 is normal use with a 100 yuan cap. Score 100 is high-intensity use with a 300 yuan cap; reaching 100 requires every dimension at its highest band. Actual reimbursement is the lower of actual eligible expense and the cap. Low-line, high-value architecture, research, documentation, or exceptional Agent/API work requires separate project review rather than manipulating this model.

## Projects, branches, and worktrees

One dashboard project can include multiple branches. Synchronization stores branch evidence, while aggregation counts a commit only once per `(project_id, commit_sha)` even if it is reachable from several selected branches. The evidence view combines all matching branch names.

Remote URLs are canonicalized without credentials, scheme noise, a trailing slash, or `.git`; a second project for the same remote must be rejected. Do not rely only on directory names.

`/home/wr/git/lc_breaker_project_new_gw25` is a linked worktree of `/home/wr/git/lc_breaker_project_new`, used for `feature/guowang25`; it is not a second GitLab repository. The dashboard keeps one project configuration for that remote. A linked worktree has a `.git` file pointing at the common repository; never move or recursively delete it as though it were an ordinary clone.

As of 2026-08-20, live preflight showed 13 enabled, healthy project configurations and `HPLC_HRF` using three selected branches. Counts and branch choices are operational state and may change; always refresh them live.

## Data model and refresh

SQLite contains `settings`, `projects`, `employees`, `employee_aliases`, `commit_stats`, `sync_snapshots`, and `audit_log`. Project deletion cascades its statistics and snapshots. Application-level audit entries record administrative changes without credentials.

Manual refresh and the scheduler pull current configured branches and Git Notes before analysis. A current-month result is therefore a month-to-date snapshot as of the most recent successful sync; a closed historical month can still change if Notes, identity mappings, filters, branches, or scoring rules are changed and data is recalculated.
