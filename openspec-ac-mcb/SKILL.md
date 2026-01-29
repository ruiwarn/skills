---
name: openspec-ac-mcb
description: OpenSpec 规范驱动开发流程与变更管理技能。用于在本项目 `openspec/` 下创建/修改/验证/归档变更与规格，或当请求涉及新功能、需求变更、规格编写、变更提案、change/spec/requirements/scenario、validate/validation、archive 等场景时使用。
---

# OpenSpec（AC MCB）工作流

## 0. 先判定是否需要提案
- **直接改动**：修复已知缺陷（恢复既有行为）、拼写/格式/注释、非行为变更、非破坏性依赖更新。
- **需要提案**：新功能、破坏性变更、架构或模式调整、性能导致行为变化、安全与合规相关改动。
- **不明确**：优先走提案流程，降低风险。

## 1. 快速扫描现状
1) 读取 `openspec/project.md` 了解项目约定  
2) 查看变更与规格：
   - `openspec list`
   - `openspec list --specs`
   - 需要全文检索时用 `rg -n "Requirement:|Scenario:" openspec/specs`

## 2. 创建变更提案（changes/<change-id>）
1) 选择唯一的 `change-id`：kebab-case、动词开头（`add-`/`update-`/`remove-`/`refactor-`）  
2) 按目录结构建立提案与 delta 规格（见 `references/directory-structure.md`）  
3) 生成 `proposal.md`、`tasks.md`，必要时补 `design.md`  
4) 为每个受影响能力创建 `changes/<id>/specs/<capability>/spec.md`

## 3. 编写规范与场景
- 规范措辞使用 **SHALL/MUST**  
- 每条 Requirement 必须至少一个 `#### Scenario:`  
- `MODIFIED` 必须粘贴**完整**的旧 Requirement 再编辑  
- 场景建议使用 `GIVEN/WHEN/THEN/AND`

## 4. 校验
- 优先执行 `openspec validate <id> --strict`  
- 若 CLI 不可用，手工检查：
  - 是否存在至少一个 delta 文件
  - `## ADDED|MODIFIED|REMOVED|RENAMED Requirements` 格式正确
  - 每条 Requirement 是否包含 `#### Scenario:`

## 5. 实施门禁
- **未审批不实现**：提案未评审前，不进入代码实现阶段。

## 6. 归档
- 变更完成并发布后归档：`openspec archive <id>`  
- 仅工具链改动可用 `--skip-specs`，需要自动确认可加 `--yes`

## 7. 项目特定提示
- 现有能力（specs）：`control-signal`、`error-logging`、`switch-actuation`
- 文档以中文为主，必要时保留英文术语

## 参考资料
- 目录与用途：`references/directory-structure.md`
- CLI 命令与参数：`references/cli-commands.md`
- 变更模板：`references/change-templates.md`
