---
name: embedded-cross-review
description: Use when reviewing embedded or firmware code changes, especially in C/C++, bare-metal, RTOS, driver, ISR, DMA, boot, NFC, or other hardware-facing paths where cross-review can catch correctness, safety, and architecture-coupling issues
---

# Embedded Code Review Expert

## Overview

Perform structured review of embedded and firmware changes with emphasis on memory safety, interrupt correctness, RTOS usage, hardware interfaces, C/C++ pitfalls, and embedded security.

The preferred review strategy is **cross-review by two independent subagents** that inspect the same diff separately, then compare findings for consensus, gaps, and contradictions.

The purpose of running two subagents is **to improve correctness, not speed**. Cross-review exists to reduce false positives, reduce false negatives, and increase confidence that a reported issue is real before escalating it to the user.

The skill is intentionally **host-agnostic**:
- Do not hardcode Claude Code, Codex, ACP, or any vendor-specific runtime.
- Use the current environment's native parallel subagent mechanism when available.
- If the environment supports model selection, use **two different high-capability models** for the two subagents.
- If model selection is unavailable, still run two independent subagents with different review emphases.
- If parallel subagents are unavailable, fall back to a single-agent review and state that cross-review could not be run in this environment.

Target environments: bare-metal MCU, RTOS (FreeRTOS/Zephyr/ThreadX), Linux embedded, mixed C/C++ firmware.

## Trigger

Activate when the user asks to review embedded or firmware code changes. Examples:
- "review firmware-pro2 的改动"
- "review the NFC changes"
- `/embedded-cross-review ~/Documents/dec/firmware-pro2`
- `/embedded-cross-review ~/Documents/dec/firmware-pro2 HEAD~5..HEAD`
- `/embedded-cross-review <github-pr-url>`

## Severity Levels

| Level | Name | Description | Action |
|-------|------|-------------|--------|
| **P0** | Critical | Memory corruption, interrupt safety violation, security vulnerability, brick risk | Must block merge |
| **P1** | High | Race condition, resource leak, undefined behavior, RTOS misuse | Should fix before merge |
| **P2** | Medium | Code smell, portability issue, missing error handling, excessive coupling, suboptimal pattern | Fix or create follow-up |
| **P3** | Low | Style, naming, documentation, minor suggestion | Optional improvement |

### Architecture Finding Rules

- Treat architecture and coupling issues as first-class findings when they affect correctness, safety, sequencing, change amplification, or testability. Do not bury material design problems in a vague closing note.
- Raise **P1** when coupling creates a real correctness or safety hazard, especially on ISR/task, driver/application, init/recovery, or power/reset paths.
- Raise **P2** when a module knows concrete consumers it should only notify, mixes unrelated responsibilities, or would clearly benefit from a smaller boundary such as observer, callback registration, event queue, state machine, strategy, adapter, or dependency inversion.
- Keep it at **P3** only when the issue is local cleanup with low near-term risk.

---

## Workflow

### Mode Selection

**Single-agent mode**:
- Use for small diffs (default threshold: ≤100 lines)
- Use when the user explicitly asks for a quick review
- Use when the host environment does not support parallel subagents

**Cross-review mode**:
- Default for diffs >100 lines
- Prefer for new features, architecture changes, and critical paths (ISR, DMA, crypto, NFC, boot)
- Implement as two independent subagents reviewing the same payload in parallel
- Primary goal: better review correctness and confidence, not faster turnaround
- If the host exposes model choice, use two different high-capability models

User can override: "用双代理 review" or "quick review 就行"

### Host Capability Rule

Choose the best available execution mode in this order:

1. Two parallel subagents with explicit different high-capability models
2. Two parallel subagents with the same model but different prompts and review focus
3. One agent review with explicit note that cross-review was unavailable

Do not abort just because a specific vendor runtime is unavailable.
Do not justify a weaker mode by claiming it is faster; the priority is review quality.

---

### Phase 0: Preflight - Scope & Context

1. Run `scripts/prepare-diff.sh <repo_path> [diff_range]` to extract:
   - Repository info (branch, last commit)
   - Target identification (MCU, RTOS, compiler)
   - Diff stat and full diff content

2. Assess scope:
   - **No changes**: Inform user; offer to review staged changes or a commit range.
   - **Small diff (≤100 lines)**: Default to single-agent review unless user requests cross-review.
   - **Large diff (>500 lines)**: Summarize by file or subsystem first, then review in batches.
   - **Critical path touched** (ISR, DMA, crypto, NFC, boot): Strongly prefer cross-review.

3. Build review context package:

```text
REVIEW_CONTEXT = {
  repo_info: (branch, MCU, RTOS, compiler),
  diff: (full git diff text),
  references: (relevant checklist sections from references/),
  focus_areas: (user-specified or auto-detected critical paths)
}
```

4. Load reference files by trigger, not blindly:
   - Always load `references/c-pitfalls.md` for C/C++ diffs unless the change is purely documentation or build metadata.
   - Load `references/memory-safety.md` when the diff touches buffers, parsing, `memcpy`/`memset`, string handling, stack allocation, heap use, DMA buffers, packed structs, pointer casts, or alignment-sensitive code.
   - Load `references/interrupt-safety.md` when the diff touches ISRs, callbacks from interrupt context, shared state, `volatile`, critical sections, atomics, RTOS tasks/queues/semaphores/mutexes, or any code that can run concurrently.
   - Load `references/hardware-interface.md` when the diff touches peripheral init, clocking, GPIO mux, MMIO registers, DMA setup, watchdogs, reset/power sequencing, or protocol drivers such as I2C/SPI/UART/NFC.
   - Load `references/architecture-maintainability.md` when the diff adds or reshapes module boundaries, cross-layer calls, callback/observer registration, event dispatch, state machines, feature branching, or direct calls that look like notification or fan-out.
   - Embedded security does not have a dedicated reference file in this skill yet; review it directly from the diff and target context.
   - If the diff spans multiple categories, load every matching reference file.
   - If the category is unclear, the diff is safety-critical, or a critical path is touched, load all five dedicated reference files.

---

### Phase 1: Single-Agent Review

For small diffs or when cross-review is not requested or not available:

Before reviewing, use the Phase 0 trigger rules to decide which reference files to load. Do not assume every reference file is required for every small diff, but do load all applicable ones. Architecture/maintainability and embedded security are always reviewed; architecture now has a dedicated reference file and embedded security still does not.

1. Memory safety scan
   - Load `references/memory-safety.md` when the diff matches the memory-safety triggers from Phase 0
   - Stack overflow, buffer overrun, alignment, DMA cache coherence, heap fragmentation
   - Flag `sprintf`, `strcpy`, `gets`, `strcat`; suggest bounded alternatives

2. Interrupt and concurrency correctness
   - Load `references/interrupt-safety.md` when the diff matches the interrupt/concurrency triggers from Phase 0
   - Shared variable access, critical sections, ISR best practices, RTOS pitfalls
   - Priority inversion, reentrancy, nested interrupt handling

3. Hardware interface review
   - Load `references/hardware-interface.md` when the diff matches the hardware-interface triggers from Phase 0
   - Peripheral init ordering, register access, timing violations, pin conflicts
   - I2C/SPI/UART/NFC buffer management and timeout handling

4. C/C++ language pitfalls
   - Load `references/c-pitfalls.md` for any non-trivial C/C++ code review
   - Undefined behavior, integer issues, compiler assumptions, linker issues
   - Preprocessor hazards, portability, type safety

5. Architecture and maintainability
   - Load `references/architecture-maintainability.md` when the diff matches the architecture triggers from Phase 0
   - HAL/BSP layering, abstraction boundaries, coupling, state ownership, testability
   - Dead code, magic numbers, configuration management
   - Check whether direct calls are encoding notification, fan-out, optional consumers, or cross-layer reach-through that would be better expressed as observer, callback registration, event queue, state machine, strategy, adapter, or dependency inversion
   - Treat actionable coupling problems as findings, not just notes; explain the concrete symptom and the smallest embedded-friendly abstraction that would reduce the coupling

6. Embedded security scan
   - No dedicated reference file today; review this directly from the diff and threat surface
   - Secret storage, debug interfaces, firmware update integrity
   - Side channels, fault injection, input validation, stack canaries

Then skip to **Phase 3: Output**.

---

### Phase 2: Cross-Review With Two Subagents

When cross-review mode is triggered, create two review tasks from the same `REVIEW_CONTEXT`.

#### Step 1: Define distinct review roles

Use prompts that force complementary perspectives.

**Subagent A: Embedded systems safety reviewer**

```text
You are a senior embedded systems engineer reviewing firmware code changes.

## Review Context

**Repository Info**: [branch, MCU, RTOS, compiler]
**Diff**: [full git diff text]
**Focus Areas**: [user-specified or auto-detected critical paths]

## Reference Materials

Load and apply the following reference files based on the diff content:

1. **references/c-pitfalls.md** — Always load for C/C++ code review. Covers undefined behavior, integer issues, compiler assumptions, linker issues, preprocessor hazards, portability, and type safety.

2. **references/memory-safety.md** — Load when the diff touches: buffers, parsing, `memcpy`/`memset`, string handling, stack allocation, heap use, DMA buffers, packed structs, pointer casts, or alignment-sensitive code. Covers stack overflow, buffer overrun, alignment, DMA cache coherence, and heap fragmentation.

3. **references/interrupt-safety.md** — Load when the diff touches: ISRs, callbacks from interrupt context, shared state, `volatile`, critical sections, atomics, RTOS tasks/queues/semaphores/mutexes, or any code that can run concurrently. Covers shared variable access, critical sections, ISR best practices, RTOS pitfalls, priority inversion, reentrancy, and nested interrupt handling.

4. **references/hardware-interface.md** — Load when the diff touches: peripheral init, clocking, GPIO mux, MMIO registers, DMA setup, watchdogs, reset/power sequencing, or protocol drivers such as I2C/SPI/UART/NFC. Covers peripheral init ordering, register access, timing violations, pin conflicts, and buffer management.

5. **references/architecture-maintainability.md** — Load when the diff adds or reshapes module boundaries, cross-layer calls, callback/observer registration, event dispatch, state machines, feature branching, or direct calls that look like notification or fan-out. Covers coupling, responsibility split, state ownership, pattern selection, and embedded-friendly alternatives such as static observer lists, callback registration, bounded event queues, interface structs, and explicit state machines.

If the category is unclear, the diff is safety-critical, or a critical path is touched, load all five dedicated reference files.

## Review Areas

Apply these review areas when relevant:
- Memory safety
- Interrupt and concurrency correctness
- Hardware interfaces and timing
- RTOS correctness
- Embedded security
- Architecture and maintainability, including whether new code introduces hardcoded fan-out, cross-layer reach-through, unclear state ownership, or mixed responsibilities that should instead use a smaller boundary such as observer, callback registration, event queue, state machine, strategy, adapter, or dependency inversion

Architecture findings are first-class issues. If the code is materially over-coupled, do not downgrade it to a soft note just because it compiles.

## Output Format

For each finding:
[P0/P1/P2/P3] [file:line] Title
- Description
- Risk
- Suggested fix

For architecture findings, explicitly name the coupling symptom and the smallest alternative that would reduce it.

Flag uncertain findings with [?].
```

**Subagent B: Independent adversarial reviewer**

```text
You are an independent reviewer for embedded and firmware code.
Your job is to challenge assumptions and find correctness problems the first reviewer might miss.

## Review Context

**Repository Info**: [branch, MCU, RTOS, compiler]
**Diff**: [full git diff text]
**Focus Areas**: [user-specified or auto-detected critical paths]

## Reference Materials

Load and apply the following reference files based on the diff content:

1. **references/c-pitfalls.md** — Always load for C/C++ code review. Covers undefined behavior, integer issues, compiler assumptions, linker issues, preprocessor hazards, portability, and type safety.

2. **references/memory-safety.md** — Load when the diff touches: buffers, parsing, `memcpy`/`memset`, string handling, stack allocation, heap use, DMA buffers, packed structs, pointer casts, or alignment-sensitive code. Covers stack overflow, buffer overrun, alignment, DMA cache coherence, and heap fragmentation.

3. **references/interrupt-safety.md** — Load when the diff touches: ISRs, callbacks from interrupt context, shared state, `volatile`, critical sections, atomics, RTOS tasks/queues/semaphores/mutexes, or any code that can run concurrently. Covers shared variable access, critical sections, ISR best practices, RTOS pitfalls, priority inversion, reentrancy, and nested interrupt handling.

4. **references/hardware-interface.md** — Load when the diff touches: peripheral init, clocking, GPIO mux, MMIO registers, DMA setup, watchdogs, reset/power sequencing, or protocol drivers such as I2C/SPI/UART/NFC. Covers peripheral init ordering, register access, timing violations, pin conflicts, and buffer management.

5. **references/architecture-maintainability.md** — Load when the diff adds or reshapes module boundaries, cross-layer calls, callback/observer registration, event dispatch, state machines, feature branching, or direct calls that look like notification or fan-out. Covers coupling, responsibility split, state ownership, pattern selection, and embedded-friendly alternatives such as static observer lists, callback registration, bounded event queues, interface structs, and explicit state machines.

If the category is unclear, the diff is safety-critical, or a critical path is touched, load all five dedicated reference files.

## Review Focus

Focus on:
1. Logic errors and edge cases
2. C/C++ undefined behavior and integer hazards
3. Race conditions and state machine bugs
4. Hardware interface misuse, timeout paths, and recovery paths
5. Security and fault handling weaknesses
6. Whether the newly added structure is doing too much in one place, hardcodes concrete consumers, or spreads state ownership in a way that should be modeled with observer, callback registration, event queue, state machine, strategy, adapter, or dependency inversion

Do not avoid architecture findings just because the code is functional today. If direct calls create unnecessary coupling or force future edits in the wrong module, report it.

## Output Format

For each finding:
[P0/P1/P2/P3] [file:line] Title
- Description
- Risk
- Suggested fix

Do not suppress low-severity issues. Report everything relevant.
```

If the host supports explicit model choice, assign different high-capability models to A and B. This is the preferred mode because model diversity helps validate whether a finding is genuinely problematic rather than a single-model hallucination or blind spot. If not, keep the roles different anyway.

#### Step 2: Spawn in parallel

Use the host's native subagent facility to run both tasks concurrently.

Requirements:
- Same `REVIEW_CONTEXT` for both subagents
- Independent execution
- No visibility into each other's findings before they finish
- Prefer parallel execution over sequential execution

Rationale:
- Parallelism is an implementation detail, not the objective.
- Independence matters because cross-contamination weakens validation value.
- Different strong models are preferred because the point is agreement quality, not throughput.

If the host only supports one worker model, still keep the prompts distinct.

#### Step 3: Cross-compare findings

After both complete, classify results:

1. **Consensus findings**: both subagents flagged substantially the same issue. Treat as high confidence.
2. **A-only findings**: validate and keep if technically sound.
3. **B-only findings**: validate and keep if technically sound.
4. **Contradictions**: one subagent says correct, the other says buggy. Surface this explicitly for human judgment.

Normalize all findings to unified severity levels `P0` to `P3`.

#### Step 4: Environment note

State which cross-review path was used:
- `two subagents, different high-capability models`
- `two subagents, same model with different prompts`
- `single-agent fallback`

This matters because confidence differs across modes, and the user should know whether the review outcome was cross-validated by distinct strong models or only approximated.

---

### Phase 3: Output Format

```markdown
## Embedded Code Review Summary

**Target**: [MCU/Board] | [RTOS/Bare-metal] | [Compiler]
**Branch**: [branch name]
**Files reviewed**: X files, Y lines changed
**Review mode**: [Single-agent / Cross-review]
**Execution path**: [two subagents, different high-capability models / two subagents, same model with different prompts / single-agent fallback]
**Confidence basis**: [consensus across distinct strong models / consensus across role-separated same-model agents / single-agent judgment]
**Overall assessment**: [APPROVE / REQUEST_CHANGES / COMMENT]

---

## Findings

### P0 - Critical (must block)
(none or list)

### P1 - High (fix before merge)
1. **[file:line]** Brief title [consensus / reviewer-A-only / reviewer-B-only]
   - Description of issue
   - Risk: what can go wrong
   - Suggested fix

### P2 - Medium (fix or follow-up)
...

### P3 - Low (optional)
...

---

## Cross-Review Analysis

| Metric | Count |
|--------|-------|
| Consensus | X |
| Reviewer-A-only | Y |
| Reviewer-B-only | Z |
| Contradictions | W |

### Notable disagreements
(list contradictions with both perspectives)

## Hardware/Timing Concerns
(register access, peripheral init, timing-sensitive code)

## Architecture Notes
(layering, testability, portability observations that did not rise to P1/P2)
(actionable coupling, responsibility split, or pattern-fit problems belong in Findings, not only here)
```

Only include `Cross-Review Analysis` when two subagents were actually used.

---

**Important**: Do not implement changes until the user explicitly confirms.
