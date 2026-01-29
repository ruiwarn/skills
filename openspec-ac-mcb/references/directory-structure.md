## OpenSpec 目录结构（本项目）

```
openspec/
├── project.md              # 项目约定与背景
├── specs/                  # 已实现的“真相规范”
│   └── [capability]/
│       ├── spec.md         # 需求与场景
│       └── design.md       # 技术模式（可选）
├── changes/                # 变更提案（尚未落地）
│   ├── [change-id]/
│   │   ├── proposal.md     # 为什么/做什么/影响
│   │   ├── tasks.md        # 实施清单
│   │   ├── design.md       # 设计决策（可选）
│   │   └── specs/
│   │       └── [capability]/
│   │           └── spec.md # ADDED/MODIFIED/REMOVED/RENAMED
│   └── archive/            # 已完成变更归档
```

### 现有能力列表
- `control-signal`
- `error-logging`
- `switch-actuation`

### 变更与规格的关系
- **specs/**：当前系统已实现的事实
- **changes/**：计划改动，等待评审与实现

### 新能力的处理
- 若新增能力，创建 `specs/<capability>/` 与变更中的 `changes/<id>/specs/<capability>/spec.md`
- 能力命名建议：动词-名词（例如 `user-auth`）
