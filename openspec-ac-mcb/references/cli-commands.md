## OpenSpec CLI 常用命令

### 列表与查看
```bash
openspec list                 # 列出当前变更
openspec list --specs         # 列出现有规格
openspec spec list --long     # 详细规格列表
openspec show [item]          # 查看变更或规格
openspec show [item] --json   # JSON 输出
```

### 差异与验证
```bash
openspec diff [change]              # 查看变更差异
openspec validate [item] --strict   # 严格校验
```

### 归档
```bash
openspec archive [change] [--yes|-y]   # 归档变更
openspec archive [change] --skip-specs --yes  # 仅工具链改动
```

### 初始化与更新
```bash
openspec init [path]     # 初始化 OpenSpec
openspec update [path]   # 更新指引文件
```

### 常用参数
- `--json`：机器可读输出
- `--type change|spec`：显式区分类型
- `--strict`：严格校验
- `--no-interactive`：禁用交互
- `--skip-specs`：归档时跳过规格更新
