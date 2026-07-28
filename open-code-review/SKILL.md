---
name: ocr
description: >
  Performs AI code review via the `ocr` CLI (alibaba/open-code-review,
  pre-installed & configured on this machine). Use when the user asks to
  review code, review a commit/PR, review staged/unstaged changes, compare
  branches, or says 评审/审查/复查代码. Produces line-level comments; then
  interpret findings, apply fixes, and re-review in the same session.
---

# Open Code Review (`ocr`)

`ocr` 是阿里巴巴开源的 AI 代码评审 CLI（`alibaba/open-code-review`）。它读取 Git diff，由 LLM Agent 生成**行级精确**的评审评论。本机已预装预配置，可直接调用。

## 环境现状

本机已完成配置，无需再装再配：

- `ocr` 已全局安装（`npm install -g @alibaba-group/open-code-review`）
- LLM 已在全局配置文件 `~/.opencodereview/config.json` 写死（脱离环境变量），中文输出已开启
- git ≥ 2.41 要求已满足

评审异常时，先验证连通性：

```bash
ocr llm test      # 应显示 "✓ Connection test successful"
```

若失败，多为 LLM 配置问题，引导用户检查 `~/.opencodereview/config.json` 的 `llm` 段（url / auth_token / model / protocol），不要自行编造密钥。

## 常用命令

```bash
# 评审工作区所有改动（staged + unstaged + untracked）
ocr review

# 评审单个 commit
ocr review -c HEAD
ocr review -c <commit-sha>

# 分支对比评审（适合发 MR/PR 前整体过一遍）
ocr review --from <base> --to <branch>

# 预览评审范围，不调用 LLM、不耗 token
ocr review -c HEAD -p
ocr review --preview

# 全文件扫描（无需 git diff，扫描整个目录/仓库）
ocr scan
ocr scan --path src/

# 输出 JSON（便于程序解析）
ocr review --format json

# 查看某文件命中的评审规则
ocr rules check <file-path>
```

### 关键 flag

| flag                         | 作用                      |
| ---------------------------- | ----------------------- |
| `-c, --commit <sha>`         | 评审指定 commit             |
| `--from <a> --to <b>`        | 分支/引用对比                 |
| `-p, --preview`              | 仅预览将评审哪些文件，不调 LLM       |
| `--audience agent`           | 摘要式输出（无进度行），适合 agent 消费 |
| `-f, --format json`          | JSON 输出                 |
| `-b, --background "<上下文>"`   | 附带业务/需求上下文，提升评审质量       |
| `-B, --background-file <md>` | 从 Markdown 文件读上下文       |
| `--path <dir>`               | scan 专用，限定扫描目录          |

## 评审规则系统

ocr 用**四层优先级链**为每个文件匹配评审规则（第一个匹配的模式生效）：

1. `--rule` 参数（CLI 覆盖，最高）
2. 项目配置 `<repo>/.opencodereview/rule.json`（可提交 git，团队共享）
3. 全局配置 `~/.opencodereview/rule.json`（用户偏好）
4. 系统内置规则（随二进制发布，覆盖常见语言：C/C++/Java/Python/Go/Rust/JS/TS…）

### 自定义规则文件格式（`.opencodereview/rule.json`）

```json
{
  "include": ["src/**/*.{ts,tsx}"],
  "exclude": ["**/*.test.ts", "vendor/**", "build/**"],
  "rules": [
    {
      "path": "**/*.{c,h}",
      "rule": "这里写评审关注点（内联文本，不支持引用外部 md 文件）",
      "merge_system_rule": true
    }
  ]
}
```

- `exclude`：不评审的文件 glob，过滤优先级最高（厂商库、构建产物、测试固定件等建议排除以省 token）
- `include`：绕过默认排除模式（如强制评审测试文件）
- `rules`：`{path, rule}` 数组，按声明顺序匹配；`merge_system_rule: true` 表示叠加在内置规则上而非替换
- glob 语法：`*` 不跨 `/`，`**` 跨目录，`{a,b}` 花括号展开；匹配不区分大小写
- 规则文本须**内联**在 `rule` 字段，不支持引用外部 .md 文件

用 `ocr rules check <file>` 确认某文件命中的规则及来源层级；用 `ocr review --preview` 确认 include/exclude 生效。

## 配置体系

### LLM 配置（`~/.opencodereview/config.json`）

优先级（源码 `internal/llm/resolver.go`）：① OCR config 文件 ② `OCR_LLM_*` 环境变量 ③ `ANTHROPIC_*` 环境变量 ④ shell rc 文件。**config 文件优先级最高，写死即脱离环境变量。**

两种写法：

```bash
# 命令行（token 不回显，推荐）
ocr config set llm.url <完整endpoint>
ocr config set llm.auth_token <token>
ocr config set llm.model <model>
ocr config set llm.protocol anthropic   # 或 openai

# 或直接编辑 ~/.opencodereview/config.json 的 llm 段
```

注意：`llm` 段的 `url` 须写**完整路径**（如 `.../v1/messages`），不会自动补后缀；`protocol` 取 `anthropic` | `openai`，优先于 `use_anthropic`。

其他配置项：

```bash
ocr config set language Chinese          # 输出语言
ocr config provider                      # 交互式选 provider（会写入 provider 段）
ocr config model                         # 交互式选 model
```

⚠️ 若 config 里同时存在 `provider` 段和 `llm` 段，`provider` 优先（走 provider 模式，忽略 `llm` 段）。要用 `llm` 段须先清掉 `provider`/`providers`/`model` 字段。

## 推荐工作流

1. **预览范围**（省 token，先看要评审哪些文件）：
  ```bash
   ocr review -c HEAD -p
  ```
2. **评审**（带业务上下文效果更好）：
  ```bash
   ocr review -c HEAD --audience agent --background "本次改动目的：xxx"
  ```
3. **解读**：把 ocr 输出的行级评论转述给用户，按严重度排序（critical > high > medium > low）。
4. **修复**：在同一会话里直接改代码。
5. **复审**：改完再跑一次 `ocr review` 确认问题消除。

## 注意事项

- `ocr review`（不带 `-c`）评审工作区全部改动，**包含 untracked 文件**。
- 评审耗时随改动规模增长，单 commit 通常 30s–3min；长分支对比可能更久。
- 大仓库建议用 `exclude` 排除厂商库/构建产物，既省 token 又降噪。
- 评审评论为 0 时输出 "Looks good to me"，属正常（未发现问题）。
- 规则可随项目演进持续扩充：每踩一个坑，往 `.opencodereview/rule.json` 加一条对应检查。
