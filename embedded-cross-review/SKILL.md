---
name: embedded-cross-review
description: Use when reviewing embedded or firmware code changes, especially in C/C++, bare-metal, RTOS, driver, ISR, DMA, boot, NFC, or other hardware-facing paths where cross-review can catch correctness, safety, and architecture-coupling issues
---

# Embedded Code Review Expert

## Overview

Perform structured review of embedded and firmware changes with emphasis on memory safety, interrupt correctness, RTOS usage, hardware interfaces, C/C++ pitfalls, and embedded security.

The preferred review strategy is **cross-review by two independent subagents** that inspect the same diff separately, then compare findings for consensus, gaps, and contradictions.

- **Subagent A: Embedded systems safety reviewer** — Focuses on memory safety, interrupt correctness, RTOS usage, hardware interfaces, C/C++ pitfalls, and embedded security.
- **Subagent B: Test Terminator** — Operates under the `test-terminator` skill protocol. Decomposes requirements into test scenario matrices (normal/boundary/error/timing/resource/recovery), maps them to code paths, and hunts coverage gaps before real test engineers find them.

The purpose of running two subagents is **to improve correctness from two orthogonal dimensions**: A ensures the code is safe and correct from an engineering standpoint; B ensures no test scenario is left uncovered from a test engineering standpoint. Cross-review exists to reduce false positives, reduce false negatives, and increase confidence that a reported issue is real before escalating it to the user.

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
   - **Large diff (>500 lines)**: Do **not** stuff the whole diff + all references into one request — that is what overflows a subagent's context. Apply the token budget below and review in batches by file/subsystem.
   - **Critical path touched** (ISR, DMA, crypto, NFC, boot): Strongly prefer cross-review.

   **Token budget & chunking (mandatory for both subagents)**: estimate the size of `diff + selected references + prompt` against the worker model's context window and keep it within budget (target ≤60% of the window, leaving room for the subagent's own reasoning/output). If it exceeds budget, split by file/subsystem and review chunk-by-chunk — reuse test-terminator's `[TT-SPLIT]` protocol (each chunk runs independently, then a cross-chunk consistency pass for shared state and interfaces). Never silently truncate the diff to fit.

3. Build review context package. Pass references **by reference (load on demand), not by stuffing full files into the prompt** — give each subagent the matched filenames + the trigger rules in step 4 and let it open only the sections it needs:

```text
REVIEW_CONTEXT = {
  repo_info: (branch, MCU, RTOS, compiler),
  diff: (full git diff text, or the current chunk if [TT-SPLIT] is active),
  references: (filenames of matched reference files — loaded on demand, not inlined wholesale),
  focus_areas: (user-specified or auto-detected critical paths),
  budget: (worker-model context window and per-request budget)
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
   - If the category is unclear, the diff is safety-critical, or a critical path is touched, consult all five dedicated reference files — but load them **on demand** (open the relevant sections as each review area is worked), not by pre-inlining all five into one prompt. "Consult all five" is about coverage, not about stuffing the context window; respect the token budget above.

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

**Subagent B: Test Terminator（测试终结者）**

Subagent B 由 `test-terminator` skill 提供，职责与 A 正交：A 从**嵌入式工程安全**找问题，B 从**测试工程师视角**反向推演——从需求拆解测试场景矩阵（正常/边界/异常/时序/资源/恢复），映射到代码路径，猎杀“代码没覆盖但测试会测”的缺口。

**主路径（优先，DRY）**：把 `test-terminator` skill 作为 Subagent B 加载并运行，传入同一个 `REVIEW_CONTEXT`，默认角色 🔴 测试刽子手。让 test-terminator 自带的协议（场景矩阵、路径映射、缺口猎杀、判定顺序铁律、`[TT-SPLIT]` 分块与失败降级）在子代理内生效；**不在此处复制其全文**，以免两份漂移。改 B 的行为请改 `test-terminator/SKILL.md`。

**回退路径**：若当前 host 无法在子代理内加载 test-terminator（运行时不支持嵌套技能加载，或加载后 token 超限），改为在 Subagent B 的 prompt 末尾注入下面这份精简协议（它是 test-terminator 的浓缩版，以 test-terminator 为准）：

```text
你当前执行测试终结者（Test Terminator）评审。规则：
1. 从需求出发拆解测试场景矩阵（正常/边界/异常/时序/资源/恢复）；需求不明确时先做隐含需求推导并标注置信度，确认后再拆解
2. 每个场景必须映射到具体代码路径；找不到路径 = ❌缺口
3. 主动猎杀隐藏缺口：防御性编程缺口、静默失败、状态不一致、资源泄漏、时序脆弱性、魔术数字
4. 每个缺口标注等级 P0/P1/P2/P3 并推动闭环（修复 / 标注风险）
5. 判定顺序铁律：先按客观证据定级与定闸门（[TT-PASS]/[TT-FAIL]/[TT-PARTIAL]），再算战报/KPI；KPI 绝不反向下调缺口等级或翻转闸门
6. 代码体量超限或子任务失败：标“未评审”、相关场景计缺口、覆盖率不计未跑部分、禁止 [TT-PASS]，降级 [TT-PARTIAL]
7. 禁止“我觉得没问题”——必须拿出路径映射证据
8. 输出：场景矩阵覆盖率 X/Y、缺口清单（含 file:line / 触发条件 / 预期行为 / 代码路径 / 建议修复）；存在漏测项时附「⚔️ 战报结算」(守住 / 失守 / 攻防比 / KPI S~F，P0 失守一票否决)。禁用「击杀 / 阵亡」杀戮词
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

#### Step 2.5: Orchestrator role & subagent-failure handling

The orchestrator (this skill — the agent that spawned A and B) is an **aggregator and adjudicator, not a third reviewer**. Its job is to deduplicate, normalize severity, surface contradictions, and audit coverage. It must **not** generate its own substantive findings and silently merge them in as if from an independent reviewer. Any orchestrator observation must be labeled `[orchestrator-note]`, and it is never counted toward consensus nor used to stand in for a failed reviewer. (Letting the orchestrator self-review is exactly what lets a failed reviewer be papered over — don't.)

**Completion invariant**: a run counts as a completed cross-review **only if both A and B returned structured findings**. If either subagent fails — token-limit overflow, timeout, crash, or empty/unparseable output:

1. **Recover first**: re-run only the failed side with a reduced payload — apply the Phase 0 token budget, split the diff by file/subsystem (reuse test-terminator's `[TT-SPLIT]`), and/or load fewer reference files.
2. **If still failing, degrade honestly**: drop to single-agent fallback using whichever subagent succeeded. Set `Execution path = single-agent fallback (reviewer X failed: <reason>)` and `Confidence basis = degraded — NOT cross-validated`.
3. **Never report a degraded run as a completed cross-review.** Do not claim "cross-review complete / full coverage / no supplement needed" when one reviewer did not return. The orchestrator's own analysis may **supplement** the surviving reviewer but may not **substitute** for the failed one.
4. State the failure and its confidence impact **prominently** in the final report — not buried in a closing note.

#### Step 3: Cross-compare findings

Only when both A and B returned (see the Step 2.5 invariant; otherwise take the degrade path). Classify results:

1. **Consensus findings**: both subagents flagged substantially the same issue. Treat as high confidence.
2. **A-only findings**: validate and keep if technically sound.
3. **B-only findings**: validate and keep if technically sound.
4. **Contradictions**: one subagent says correct, the other says buggy. Surface this explicitly for human judgment.

Normalize all findings to unified severity levels `P0` to `P3`.

#### Step 4: Environment note

State which cross-review path was used:
- `two subagents, different high-capability models`
- `two subagents, same model with different prompts`
- `single-agent fallback (cross-review unavailable in this host)`
- `single-agent fallback (a reviewer failed mid-run — results NOT cross-validated)` ← use this, not a "complete" label, whenever A or B failed after starting

This matters because confidence differs across modes, and the user should know whether the review outcome was cross-validated by distinct strong models, only approximated, or **degraded by a reviewer failure**. A degraded run must say so here; it must never be labeled a completed cross-review.

---

### Phase 3: Output Format

```markdown
## Embedded Code Review Summary

**Target**: [MCU/Board] | [RTOS/Bare-metal] | [Compiler]
**Branch**: [branch name]
**Files reviewed**: X files, Y lines changed
**Review mode**: [Single-agent / Cross-review]
**Execution path**: [two subagents, different high-capability models / two subagents, same model with different prompts / single-agent fallback (cross-review unavailable) / single-agent fallback (reviewer X failed mid-run)]
**Confidence basis**: [consensus across distinct strong models / consensus across role-separated same-model agents / single-agent judgment / degraded — NOT cross-validated, reviewer X failed]
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

## Test Terminator Coverage Report (reviewer-B only)

**场景矩阵覆盖率**: X/Y
**缺口统计**: P0=A, P1=B, P2=C, P3=D

### ⚔️ 战报结算（存在漏测项时必出）

**守住的防线**（你打败的测试）: N 个场景已封死 ✅
**失守的缺口**（测试打败你的）: M 个残留 ❌
**攻防比**: N 守 / M 失
**终结者 KPI 评级**: [S/A/B/C/D/F] · 称号 · 一句评语（从严打分，P0 失守一票否决直接判 F）
**测试人员待领赏**: K 个高概率缺口（发现概率 > 80%，P0×a / P1×b）→ 对方 KPI 预计 +Z；你今天失守的，就是测试人员明天的 KPI

**测试人员发现概率最高的缺口**:
1. [场景] — [file:line] — 触发条件
2. [场景] — [file:line] — 触发条件
3. [场景] — [file:line] — 触发条件

**TT 结论**: [TT-PASS] / [TT-FAIL] / [TT-PARTIAL]
- 如为 [TT-FAIL]，说明存在测试人员会发现的 P0/P1 缺口，建议阻塞交付
- 如为 [TT-PARTIAL]，说明存在未评审块或子 agent 失败，覆盖不完整，禁止当作通过，需列出未覆盖范围
- 如为 [TT-PASS]，说明当前可获得证据下所有可运行验收均通过，已知高风险缺口已修复或已明示

---

## Cross-Review Analysis

### Embedded Safety Findings (Reviewer-A: Embedded Systems Safety)

| Metric | Count |
|--------|-------|
| Consensus | X |
| Reviewer-A-only | Y |
| Reviewer-B-only | Z |
| Contradictions | W |

### Test Coverage Findings (Reviewer-B: Test Terminator)

| Metric | Count |
|--------|-------|
| 场景矩阵覆盖率 | X/Y |
| P0 测试缺口 | A |
| P1 测试缺口 | B |
| P2 测试缺口 | C |
| P3 测试缺口 | D |
| 测试人员发现概率 > 80% 的缺口 | E |
| 攻防比（守 / 失） | N 守 / M 失 |
| 终结者 KPI 评级 | [S/A/B/C/D/F] · 称号 |

### Cross-domain overlaps
List findings where Reviewer-A 的安全问题与 Reviewer-B 的测试缺口指向同一处代码（如：缓冲区溢出既是安全问题也是边界测试缺口）。这类重叠发现置信度最高。

### Notable disagreements
(list contradictions with both perspectives)

## Hardware/Timing Concerns
(register access, peripheral init, timing-sensitive code)

## Architecture Notes
(layering, testability, portability observations that did not rise to P1/P2)
(actionable coupling, responsibility split, or pattern-fit problems belong in Findings, not only here)
```

Only include `Cross-Review Analysis` when two subagents were actually used **and both returned structured findings**. A run where A or B failed is a degraded single-agent fallback, not a cross-review — report it as such (see Step 2.5), never as completed cross-review.

---

**Important**: Do not implement changes until the user explicitly confirms.

---

## 版本历史

- v1.2.0 — 交叉评审健壮性重构：Subagent B 改为**调用 `test-terminator` skill**（DRY，不再 inline 复制全文；host 无法嵌套加载时回退到精简注入协议）；新增 Step 2.5「编排者角色 + 子代理失败处置」——编排者降为纯聚合/裁决（自身观察只标 `[orchestrator-note]`，不计 consensus、不顶替失败 reviewer），并加**完成不变量**（A 与 B 都返回结构化结果才算完整交叉评审）与失败分支（先缩负载/分块重试 → 否则降级单代理 fallback 并显式标注 degraded 置信度，禁止把降级跑报成完整交叉评审）；Phase 0 reference 改按需加载 + token 预算 + 复用 `[TT-SPLIT]` 分块，杜绝“全 diff + 五个 reference 一次性灌爆上下文”；Phase 3 增加 degraded/[TT-PARTIAL] 口径
- v1.1.0 — Subagent B（测试终结者）同步加入「战报结算 + KPI 评级」紧迫感输出：内联 KPI 评级规则（S~F，P0 失守一票否决）+ 测试人员待领赏反向施压（保证子代理独立可执行）；Subagent B Output Format 增加 [⚔️ 战报结算] 块；Phase 3「Test Terminator Coverage Report」与 Cross-Review 统计表补充「守住/失守/攻防比/终结者 KPI 评级」字段；Subagent B 宣言补「攻防战 = 失守 = KPI 掉级 = 淘汰」。口径与 `test-terminator` 一致，禁用「击杀/阵亡」杀戮词
- v1.0.0 — 初始版本，双 subagent 交叉评审（A 嵌入式安全 + B 测试终结者） 