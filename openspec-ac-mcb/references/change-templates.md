## 变更模板（示例）

### proposal.md
```markdown
## Why
（1-2 句说明问题/机会）

## What Changes
- 变更点 1
- 变更点 2
- **BREAKING**（如有破坏性变更）

## Impact
- 影响的规格：control-signal / error-logging / switch-actuation / 新能力
- 影响的代码模块：简述模块或路径
```

### tasks.md
```markdown
## 1. Implementation
- [ ] 1.1 任务 1
- [ ] 1.2 任务 2
- [ ] 1.3 任务 3
```

### design.md（可选）
```markdown
## Context
（背景与约束）

## Goals / Non-Goals
- Goals: ...
- Non-Goals: ...

## Decisions
- Decision: ...
- Alternatives considered: ...

## Risks / Trade-offs
- 风险 → 缓解

## Migration Plan
（迁移/回滚步骤）

## Open Questions
- ...
```

### specs/<capability>/spec.md（delta）
```markdown
## ADDED Requirements
### Requirement: 新增功能
系统 MUST ...

#### Scenario: 成功路径
- **GIVEN** ...
- **WHEN** ...
- **THEN** ...

## MODIFIED Requirements
### Requirement: 已有功能
（粘贴完整旧内容后再修改）

#### Scenario: 变更后的场景
- **GIVEN** ...
- **WHEN** ...
- **THEN** ...

## REMOVED Requirements
### Requirement: 旧功能
**Reason**: ...
**Migration**: ...

## RENAMED Requirements
- FROM: `### Requirement: Old Name`
- TO: `### Requirement: New Name`
```

### change-id 命名规则
- kebab-case
- 动词开头：`add-` / `update-` / `remove-` / `refactor-`
- 确保唯一，冲突可加 `-2`、`-3`
