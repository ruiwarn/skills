# Embedded Code Review Expert

A code review skill for embedded and firmware projects with **two-subagent cross-review** support. Two independent reviewers inspect the same diff, then findings are cross-compared to improve review correctness and catch blind spots that single-pass review misses.

## Features

### Review Capabilities
- **Memory Safety** — Stack overflow, buffer overrun, alignment, DMA cache coherence, heap fragmentation
- **Interrupt & Concurrency** — Volatile correctness, critical sections, ISR best practices, RTOS pitfalls (priority inversion, deadlock)
- **Hardware Interfaces** — Peripheral init ordering, register access patterns, I2C/SPI/UART/NFC protocol issues, clock & timing
- **C/C++ Pitfalls** — Undefined behavior, integer gotchas, compiler optimization traps, preprocessor hazards, portability
- **Architecture** — HAL/BSP layering, testability, configuration management
- **Security** — Debug interface exposure, firmware update integrity, side channels, input validation

### Two-Subagent Cross-Review
- **Reviewer A** focuses on embedded systems safety, concurrency, RTOS, timing, and hardware access
- **Reviewer B** acts as an independent adversarial reviewer for logic bugs, undefined behavior, recovery paths, and security issues
- **Cross-comparison** identifies consensus bugs (high confidence) and reviewer-specific catches
- The goal is **better correctness and confidence**, not speed
- When the host supports model choice, prefer **two different high-capability models** for the two reviewers
- Based on research: [arXiv:2602.03794](https://arxiv.org/abs/2602.03794) — heterogeneous models often outperform homogeneous multi-agent setups

### Review Modes
| Mode | When | Cost |
|------|------|------|
| **Single-model** | Small diffs (≤100 lines), quick reviews | Low |
| **Cross-review** | New features, critical paths, architecture changes | Higher review cost, higher confidence |

## Target Environments

- Bare-metal MCU (STM32, nRF, ESP32, RP2040)
- RTOS (FreeRTOS, Zephyr, ThreadX)
- Linux embedded
- Mixed C/C++ firmware

## Installation

### As Local Skill
```bash
mkdir -p ~/.agents/skills
git clone https://github.com/ylongwang2782/embedded-review.git ~/.agents/skills/embedded-cross-review
```

Adjust the destination for your host environment's skill directory if needed.

## Usage

### Basic (single-model)
```
Review my current git changes in firmware-pro2
```

### Cross-review
```
用双代理 review firmware-pro2 feat/nfc 的改动
```

### Specific commit range
```
/embedded-cross-review ~/Documents/dec/firmware-pro2 HEAD~5..HEAD
```

### GitHub PR
```
/embedded-cross-review https://github.com/user/repo/pull/42
```

## How Cross-Review Works

```
User: "review firmware-pro2"
         │
    Host environment (orchestrator)
         │
    ┌────┴────┐
    │         │
Reviewer A  Reviewer B
(embedded    (independent
 safety)      adversarial view)
    │         │
    └────┬────┘
         │
    Cross-Compare
    ├─ Consensus → HIGH CONFIDENCE (real bugs)
    ├─ Reviewer-A-only → may catch embedded-specific issues
    ├─ Reviewer-B-only → may catch independent blind spots
    └─ ⚠️ Contradictions → escalate to human
         │
    Unified Report
```

## Severity Levels

| Level | Name | Action |
|-------|------|--------|
| P0 | Critical | Must block merge — memory corruption, security, hardware damage |
| P1 | High | Fix before merge — race condition, UB, resource leak |
| P2 | Medium | Fix or follow-up — code smell, portability, missing error handling |
| P3 | Low | Optional — style, naming, documentation |

## Structure

```
embedded-cross-review/
├── SKILL.md                          # Main skill (review workflow + subagent orchestration)
├── README.md                         # This file
├── LICENSE                           # MIT
├── scripts/
│   └── prepare-diff.sh              # Extract git diff and build review context
└── references/
    ├── memory-safety.md              # Stack, buffer, alignment, DMA, heap
    ├── interrupt-safety.md           # ISR, volatile, critical sections, RTOS
    ├── hardware-interface.md         # Peripherals, registers, protocols, timing
    └── c-pitfalls.md                 # UB, integers, compiler, preprocessor, portability
```

## Requirements

- A host environment that can run the skill
- Parallel subagents are preferred for cross-review mode
- Optional: model selection support for heterogeneous cross-review
- Git (for diff extraction)
- Target repository accessible locally

## Credits

Cross-review approach informed by practical multi-agent review workflows and the research paper "Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity" (arXiv:2602.03794).

## License

MIT
