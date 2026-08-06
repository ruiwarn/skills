---
name: conan-source-lookup
description: |
  定位 Conan(v2) 库的源码目录, 用于分析依赖库的实现。
  当用户提到 "conan 库源码"、"找库源码"、"freertos 源码"、"dlt698/dlt645 源码"、
  "v32g410x/芯片驱动源码"、"mcu_driver 源码"、".conan2 里找源码"、"库实现"、
  "第三方库怎么实现的"、"看下 xx 库的代码" 等需要阅读依赖库源码的意图时, 调用本技能。
  优先在本地 Conan 缓存(~/.conan2)中查找, 找不到再回退搜索工程目录。
---

# Conan 库源码定位

## 用途

分析依赖库实现时, 需要找到库的**源码目录**再 Read/Grep。Conan 缓存里的包目录名是
短哈希(如 `freer1302c20ea6851`), 不能靠名字猜, 必须查缓存数据库映射。本技能提供
一个脚本自动完成定位, 跨机器兼容(每台电脑源码目录可能不同)。

## 快速使用(推荐)

```bash
~/.claude/skills/conan-source-lookup/find_lib_source.sh <库名> [版本号]
```

脚本会输出**推荐源码目录**、顶层子目录、示例源码文件, 直接拿来 Read/Grep 即可。

```bash
# 常见用法
find_lib_source.sh freertos            # 自动选工程 conanfile.py 所需版本(标 ★)
find_lib_source.sh dlt698 1.0.10       # 指定版本
find_lib_source.sh v32g410x
find_lib_source.sh mcu_driver          # 不在缓存 -> 回退搜索工程目录
```

定位到目录后, 用 Grep 在该目录下搜索符号, 或 Read 具体文件。例如:
```
Grep pattern: xQueueSend   path: /home/xx/.conan2/p/freer1302c20ea6851/s
```

## 定位优先级(脚本已实现, 无需手动)

1. **editable 包**: 查 `~/.conan2/editable_packages.json`, 命中则源码在本地工作目录
   (不在缓存 `s/` 里)。例如 `micro_crv_algorithm`。
2. **Conan 缓存**: 查 `~/.conan2/p/cache.sqlite3` 的 `recipes` 表(reference -> hash 目录),
   源码在 `~/.conan2/p/<hash>/s/`(部分包用 `es/`, 脚本自动回退)。
   - 多版本共存时, **★** 标记工程当前 `conanfile.py` 所需版本。
   - 缓存布局: `e/`=配方, `s/`=源码, `es/`=导出源码, `d/`=元数据。
   - `s/`/`es/` 都不存在时, 调 `conan cache path <ref> --folder source` 兜底解析(官方命令,
     兼容未来缓存布局变更; 全程至多一次, 不拖慢常见情况)。
3. **目录扫描回退**(无 sqlite3 时): 遍历 `~/.conan2/p/*/e/conanfile.py` 按 `name=` 匹配
   (可正确区分 `dlt645`/`dlt698` 这类前缀碰撞)。
4. **工程目录回退**(缓存完全没有该包): `grep -rl 'name = "<库名>"' <搜索根> --include=conanfile.py`。
   两阶段搜索(先当前工程 ~0.5s, 未命中才扩到父目录), 并剪枝 `.git`/`build*` 加速;
   可用环境变量 `LIB_SEARCH_ROOTS`(冒号分隔)覆盖搜索根。
   > 包已在 conan 缓存(即使该版本无源码)时跳过本步, 不再满盘搜索。

## 手动定位(脚本不可用时的等价命令)

```bash
# 1. 查缓存数据库, 拿到 hash 目录名
sqlite3 ~/.conan2/p/cache.sqlite3 \
  "SELECT reference,path FROM recipes WHERE reference LIKE 'freertos/%';"
#   freertos/10.4.3.1@xian/stable|freer1302c20ea6851

# 2. 源码目录 = ~/.conan2/p/<hash>/s  (无 s/ 则用 es/)
ls ~/.conan2/p/freer1302c20ea6851/s

#    (或用 conan 官方命令直接拿源码路径, 最稳健但 ~200ms)
conan cache path "freertos/10.4.3.1@xian/stable" --folder source

# 3. 缓存没有 -> 按配方 name 字段搜索工程目录
grep -rlE 'name *= *"mcu_driver"' /mnt/f/.../gitlab --include=conanfile.py
```

跨机器注意: 缓存根优先取 `$CONAN_HOME`, 为空时才用 `~/.conan2`。

## 常见库速查(本机实测)

| 库名 | 类型 | 源码位置 | 关键子目录 |
|------|------|----------|-----------|
| `freertos` | 缓存 | `~/.conan2/p/freer1302c20ea6851/s` | `freeRTOS/`(tasks.c/queue.c/list.c) |
| `v32g410x` | 缓存 | `~/.conan2/p/v32g498a63ab2cde3f/s` | `Inc/`(lib_*.h)、`Src/`(lib_*.c) |
| `dlt698` | 缓存 | `~/.conan2/p/dlt69e753b0a1ab7e2/s` | `inc/`、`src/` |
| `dlt645` | 缓存 | `~/.conan2/p/dlt6434b8d7face969/s` | `Inc/`、`Src/` |
| `micro_crv_algorithm` | editable | `.../gitlab/lib/micro_crv_algorithm` | `Inc/`、`Src/` |
| `mcu_driver` | 本地 | `<工程>/kernel/mcu_driver_lib` | `driver/`、`include/`、`source/` |

> 速查表里的 hash 目录是本机快照, 换机器/换版本后会变; **以脚本输出为准**, 不要硬编码。

## 注意事项

- 库名用 Conan 包名(配方里的 `name = "..."`), 不是目录名。例如包名 `mcu_driver` 对应
  目录 `mcu_driver_lib`; 包名 `v32g410x` 不是 `v32g410x_lib`。
- 缓存里同一库常有多个版本, 部分旧版本可能只有配方 `e/`、没有源码 `s/`(从未在该机器
  构建过); 脚本会标注 "无 s/ 源码目录", 换带源码的版本即可。
- 若分析的是**工程本身修改过的库**(非 conan 拉取), 优先看工程内 `kernel/`、`modules/`
  或 `gitlab/lib/` 下的源码, 而不是缓存里的原始版本。
