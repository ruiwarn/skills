---
name: auto-postwrite-refactor
description: Automatically review and refactor code after Codex writes/edits code and before the final response, without user prompting. Use for any language to remove dead/garbage code, reduce cyclomatic complexity, merge duplicated logic, and right-size functions (not too long, not too tiny) while preserving behavior; add Chinese comments when helpful; output a change summary with reasons.
---

# Auto Postwrite Refactor

## Workflow

1) Identify just-written code
- Only inspect files changed in the current session (use git diff or the tracked edit list).
- Skip untouched files to avoid scope creep.

2) Scan for refactor targets
- Dead/unused code: unused variables, functions, branches, imports, or unreachable paths.
- Duplicated logic: similar blocks that can be merged without changing behavior.
- High cyclomatic complexity: long conditional chains, nested branching, repeated early-returns.
- Oversized functions: long functions that can be split into cohesive helpers.
- Over-fragmentation: tiny helpers that add indirection with no clarity benefit.

3) Apply safe, behavior-preserving refactors only
- Keep semantics identical; no functional changes, no signature changes unless strictly internal and behavior-neutral.
- Prefer local refactors within the same file/module.
- Do not alter public APIs, interfaces, or externally-visible behavior.

4) Maintain readability and maintainability
- Add concise Chinese comments only where the logic is non-obvious.
- Avoid over-abstracting; balance function length vs cohesion.
- Use existing style, naming, and formatting conventions.

5) Verify consistency
- Ensure refactors do not change control flow outcomes.
- Keep error handling and edge cases intact.

6) Final response requirements
- Provide a brief change summary and rationale in the assistant's final response to the user (do not add to code output).
- Do not ask the user to trigger this; run automatically after code writing.

## Heuristics (use judgment)
- Target smaller, cohesive helpers when a function mixes multiple responsibilities.
- Merge blocks when they only differ by small, parameterizable pieces.
- Avoid creating one-line wrappers unless it removes duplication.
- If comments are added, keep them short and in Chinese.
