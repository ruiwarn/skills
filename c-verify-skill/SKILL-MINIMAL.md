---
name: c-verify-skill
description: Run C/C++ static analysis (clang-tidy/cppcheck) on code. Triggers: scan code, check quality, verify C code, check staged/modified files, find bugs, review before commit.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# C/C++ Static Analysis (AI-Optimized)

## Commands

```bash
# Check staged/modified/specific files (--project-root required)
$SKILL_DIR/scripts/run_c_checks.sh --git-staged --project-root /path/to/project
$SKILL_DIR/scripts/run_c_checks.sh --git-modified --project-root /path/to/project
$SKILL_DIR/scripts/run_c_checks.sh -f code/main.c --project-root /path/to/project
```

Options: `--severity error` (errors only), `--ignore <pattern>` (skip checks)

## JSON Output

```json
{
  "summary": {"files_checked": 5, "errors": 1, "warnings": 8, "info": 1, "total": 10, "priority": "high|medium|low"},
  "issues_by_check": {"check-name": {"count": 7}},
  "issues": [{"file": "code/main.c", "line": 48, "severity": "error|warning|info", "message": "...", "check": "..."}],
  "global_issues": [{"severity": "info", "message": "...", "check": "..."}],
  "top_files": [{"file": "code/main.c", "issue_count": 4}]
}
```

## AI Processing

1. Check `priority`: high=must fix errors, medium=suggest fixes, low=optional
2. Group by `issues_by_check` for unified fixes
3. Focus on `top_files` with most issues
4. Separate `global_issues` (tool warnings, show last/ignore)
5. Provide code fixes based on `check` field

Exit: 0=OK, 1=errors found, 2=tool error
