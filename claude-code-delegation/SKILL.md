---
name: claude-code-delegation
description: Delegate independent subtasks to `claude -p` instances. Use when you need to parallelize work across multiple files or modules that have no write conflicts.
---

# Claude Code Delegation

## Task Design

- Keep tasks narrow with **disjoint write sets** (no overlapping files)
- Prefer 10-20 minute tasks over hour-long jobs
- Main agent does review/acceptance; don't duplicate large implementation work
- Ask delegates to run verification commands and report concrete results

## Sandbox & Permissions

- `--dangerously-skip-permissions` only skips internal prompts
- It does **NOT** bypass outer sandbox restrictions or network blocks
- If `claude -p` cannot reach the API, run it outside the restrictive sandbox or escalate
- Check environment variables and API access before delegating long tasks

## Prompt Template

```
Working directory: <absolute-path>
Target files: <file1>, <file2>

Task: <clear description>

Input: <context or code snippets>

Requirements:
- Modify only the listed files
- Run verification: <command>
- Report: summary of changes + verification output
- End with: TASK_COMPLETE or TASK_FAILED: <reason>
```

## Conflict Avoidance

| Strategy | When to use |
|----------|-------------|
| File locks | Pre-declare locks before delegating |
| Phased execution | Stage 1: interfaces; Stage 2: parallel implementations |
| Isolation | Separate directories/workspaces for independent work |

## Handling Hangs

- Set timeouts: 5 min (simple edits), 15 min (complex), 20 min (build+test)
- If no output for 2+ minutes: terminate and retry with smaller scope
- If API errors occur: check sandbox/network, not just retry

## Acceptance Checklist

- [ ] All subtasks returned (TASK_COMPLETE or TASK_FAILED)
- [ ] Verification commands executed with passing results
- [ ] Only expected files modified
- [ ] No stray lock files remaining
