#!/usr/bin/env bash
# 定位 Conan(v2) 库的源码目录
# 用法: find_lib_source.sh <库名> [版本号]
# 优先级: editable 包 -> conan 缓存(.conan2) -> 工程目录回退搜索
# 跨机器兼容: 自动识别 CONAN_HOME / ~/.conan2, 自动向上查找工程 conanfile.py 推断版本,
#             回退搜索根可通过 LIB_SEARCH_ROOTS 环境变量(冒号分隔)覆盖。
set -uo pipefail

NAME="${1:-}"
if [ -z "$NAME" ]; then
  echo "用法: $0 <库名> [版本号]"
  echo "示例: $0 freertos"
  echo "      $0 dlt698 1.0.10"
  echo "      $0 v32g410x"
  exit 1
fi
VERSION="${2:-}"

# ---- 1. 确定 Conan 缓存根目录(兼容 CONAN_HOME 环境变量) ----
CACHE=""
if [ -n "${CONAN_HOME:-}" ] && [ -d "$CONAN_HOME" ]; then CACHE="$CONAN_HOME"; fi
if [ -z "$CACHE" ] && [ -d "$HOME/.conan2" ]; then CACHE="$HOME/.conan2"; fi

# ---- 2. 向上查找工程 conanfile.py, 推断当前工程所需版本 ----
proj_ver=""; PROJ_CF=""
d="$PWD"
while [ "$d" != "/" ]; do
  if [ -f "$d/conanfile.py" ]; then
    PROJ_CF="$d/conanfile.py"
    proj_ver=$(grep -oE "self\.requires\([\"']${NAME}/[0-9][^@\"']*" "$PROJ_CF" 2>/dev/null | head -1 \
               | sed -E "s|.*${NAME}/([0-9][^@\"']*)|\1|")
    break
  fi
  d=$(dirname "$d")
done

echo "================ Conan 库源码定位 ================"
echo "库名     : $NAME"
echo "指定版本 : ${VERSION:-(未指定)}"
echo "工程所需 : ${proj_ver:-(未在 conanfile.py 找到)}${PROJ_CF:+  ($PROJ_CF)}"
echo "Conan缓存: ${CACHE:-(未找到)}"
echo "==================================================="

BEST_STAR=""; BEST_ANY=""

# ---- 3. editable 本地可编辑包检查(源码在本地路径, 不在缓存 s/) ----
if [ -n "$CACHE" ] && [ -f "$CACHE/editable_packages.json" ]; then
  ep=$(grep -oE "\"${NAME}/[^\"]+\"[^}]*\"path\": *\"[^\"]+\"" "$CACHE/editable_packages.json" 2>/dev/null | head -1)
  if [ -n "$ep" ]; then
    ed=$(printf '%s' "$ep" | sed -E 's|.*"path": *"([^"]+)".*|\1|')
    edir=$(dirname "$ed")
    echo ""
    echo "[EDITABLE 本地可编辑包] (源码不在缓存, 在本地工作目录)"
    echo "  源码目录: $edir"
    echo "  源码文件: $(find "$edir" -maxdepth 6 \( -name '*.c' -o -name '*.h' \) 2>/dev/null | wc -l) 个 (.c/.h)"
    BEST_STAR="$edir"; BEST_ANY="$edir"
  fi
fi

# ---- 4. conan 缓存查询: sqlite DB 优先, 否则扫描所有 e/conanfile.py ----
cache_hits=""
if [ -n "$CACHE" ]; then
  if [ -f "$CACHE/p/cache.sqlite3" ] && command -v sqlite3 >/dev/null 2>&1; then
    # 方法A: 直接查 recipes 表, reference -> path(hash 目录名)
    cache_hits=$(sqlite3 -separator '|' "$CACHE/p/cache.sqlite3" \
      "SELECT reference,path FROM recipes WHERE reference LIKE '${NAME}/%' ORDER BY reference;" 2>/dev/null || true)
  else
    # 方法B(回退): 遍历所有缓存的配方, 按 name 字段匹配(处理 dlt645/dlt698 前缀碰撞)
    for cf in "$CACHE"/p/*/e/conanfile.py; do
      [ -f "$cf" ] || continue
      nm=$(grep -oE '^name *= *"[^"]+"' "$cf" 2>/dev/null | head -1 | sed -E 's|.*"([^"]+)".*|\1|')
      [ "$nm" = "$NAME" ] || continue
      hp_dir=$(dirname "$(dirname "$cf")")   # cf=.../p/<hash>/e/conanfile.py -> .../p/<hash>
      hp=$(basename "$hp_dir")               # -> <hash>
      ver=$(grep -oE '^version *= *"[^"]+"' "$cf" 2>/dev/null | head -1 | sed -E 's|.*"([^"]+)".*|\1|')
      cache_hits+="${NAME}/${ver}@?|${hp}"$'\n'
    done
  fi
fi

if [ -n "$cache_hits" ]; then
  PKG_IN_CACHE=1   # 包在 conan 缓存中(无论指定版本是否匹配), 后续不再做工程目录回退搜索
  # 指定版本时仅保留精确匹配
  if [ -n "$VERSION" ]; then
    cache_hits=$(printf '%s\n' "$cache_hits" | grep -E "^${NAME}/${VERSION}@")
  fi
  if [ -n "$cache_hits" ]; then
    echo ""
    echo "[Conan 缓存命中]"
    # 进程替换, 避免管道子 shell 丢失变量
    while IFS='|' read -r ref hp; do
      [ -z "$ref" ] && continue
      src=""
      for sub in s es; do [ -d "$CACHE/p/$hp/$sub" ] && { src="$CACHE/p/$hp/$sub"; break; }; done
      if [ -z "$src" ]; then
        echo "  ${ref}  ->  ${CACHE}/p/${hp}  (无源码目录, 仅有配方 e/)"
        # 记下待 conan 兜底解析的候选 ref(优先工程所需版本), 供循环后统一调用
        if [ -n "$proj_ver" ] && echo "$ref" | grep -q "/${proj_ver}@"; then CONAN_CAND_REF="$ref"
        elif [ -z "${CONAN_CAND_REF:-}" ]; then CONAN_CAND_REF="$ref"; fi
        continue
      fi
      n=$(find "$src" -maxdepth 6 \( -name '*.c' -o -name '*.h' \) 2>/dev/null | wc -l)
      mark=" "
      if [ -n "$proj_ver" ] && echo "$ref" | grep -q "/${proj_ver}@"; then mark="★"; fi   # ★ = 工程所需版本
      echo "  ${mark} ${ref}  ->  ${src}  (${n} 个源码文件)"
      [ "$mark" = "★" ] && [ -z "$BEST_STAR" ] && BEST_STAR="$src"
      [ -z "$BEST_ANY" ] && BEST_ANY="$src"
    done < <(printf '%s\n' "$cache_hits")
    echo "  (★ = 工程当前 conanfile.py 所需版本)"
    # 快速路径(s/es)未定位到任何源码时, 用 conan 官方命令解析推荐版本的源码路径
    # (兼容未来缓存布局变更; 全程至多调用一次, 不拖慢常见情况)
    if [ -z "$BEST_STAR" ] && [ -z "$BEST_ANY" ] && [ -n "${CONAN_CAND_REF:-}" ] && command -v conan >/dev/null 2>&1; then
      csrc=$(conan cache path "$CONAN_CAND_REF" --folder source 2>/dev/null || true)
      if [ -n "$csrc" ] && [ -d "$csrc" ]; then
        echo "  (conan 解析) ${CONAN_CAND_REF}  ->  ${csrc}"
        BEST_ANY="$csrc"
      fi
    fi
  fi
fi

# ---- 5. 缓存未命中 -> 工程目录回退搜索(两阶段: 先当前工程, 再父目录) ----
# 两阶段可将常见本地包(如 mcu_driver)的搜索从 ~5s 降到 ~0.5s, 避免遍历父目录下的
# 大量 worktree 副本。包已在 conan 缓存(即使无源码)时跳过本步, 不再满盘搜索。
if [ -z "$BEST_STAR" ] && [ -z "$BEST_ANY" ] && [ -z "${PKG_IN_CACHE:-}" ]; then
  echo ""
  echo "[未在 Conan 缓存找到, 执行工程目录回退搜索]"
  # 剪枝: 跳过这些重目录以加速遍历
  PRUNE=(--exclude-dir=.git --exclude-dir=build --exclude-dir='build_*' --exclude-dir=.cache --exclude-dir=__pycache__ --exclude-dir=venv --exclude-dir=node_modules)
  # search_one <根> : 输出该根下 name="$NAME" 的 conanfile.py 路径(每行一个)
  search_one() { grep -rlE 'name *= *"'"$NAME"'"' "$1" --include=conanfile.py "${PRUNE[@]}" 2>/dev/null; }

  if [ -n "${LIB_SEARCH_ROOTS:-}" ]; then
    # 用户显式指定搜索根 -> 单阶段全搜
    ROOTS=$(echo "$LIB_SEARCH_ROOTS" | tr ':' ' ')
    echo "  搜索根: $ROOTS"
    found=$(for r in $ROOTS; do search_one "$r"; done | sort -u | head -20)
  else
    # 阶段1: 仅搜当前 git 工程根(快)
    gd="$PWD"
    while [ "$gd" != "/" ] && [ ! -d "$gd/.git" ]; do gd=$(dirname "$gd"); done
    cur_root="$gd"; parent_root=$(dirname "$gd")
    if [ "$cur_root" = "/" ]; then
      # 当前目录不在任何 git 工程内 -> 不搜索 "/"(会遍历全盘), 提示用户指定根
      echo "  当前目录不在 git 工程内, 跳过自动搜索。可用 LIB_SEARCH_ROOTS 指定搜索根。"
      found=""; ROOTS="$PWD"
    else
      echo "  搜索根(当前工程): $cur_root"
      found=$(search_one "$cur_root" | sort -u | head -20)
      # 阶段2: 当前工程未命中才扩大到父目录(含同级仓/worktree, 较慢)
      if [ -z "$found" ] && [ "$parent_root" != "$cur_root" ] && [ "$parent_root" != "/" ]; then
        echo "  当前工程未命中, 扩大到父目录: $parent_root"
        found=$(search_one "$parent_root" | sort -u | head -20)
      fi
      ROOTS="$cur_root $parent_root"
    fi
  fi

  if [ -n "$found" ]; then
    echo "  命中 conanfile.py (name=\"$NAME\"):"
    cur="$PWD"
    first_in_cur=""
    for cf in $found; do
      dn=$(dirname "$cf")
      case "$dn" in
        "$cur"*) tag="  <当前工程>"; [ -z "$first_in_cur" ] && first_in_cur="$dn" ;;
        *) tag="" ;;
      esac
      echo "    - $dn $tag"
    done
    BEST_ANY="${first_in_cur:-$(dirname "$(echo "$found" | head -1)")}"
  else
    echo "  未找到 name=\"$NAME\" 的 conanfile.py。"
    echo "  可按特征源码文件搜索, 例如:"
    echo "    find $ROOTS -name 'tasks.c'        # freertos"
    echo "    find $ROOTS -name 'dlt698_frame.*'  # dlt698"
  fi
fi

# ---- 6. 汇总推荐 ----
BEST="${BEST_STAR:-$BEST_ANY}"
echo ""
echo "==================================================="
if [ -n "$BEST" ]; then
  echo "推荐源码目录: $BEST"
  echo ""
  echo "顶层目录:"
  ls -1 "$BEST" 2>/dev/null | head -15 | sed 's/^/  /'
  echo ""
  echo "示例源码文件:"
  find "$BEST" -maxdepth 3 \( -name '*.c' -o -name '*.h' \) 2>/dev/null | head -8 | sed 's/^/  /'
  echo ""
  echo "提示: 用 Read / Grep 直接分析该目录下的文件; 跳转目录可用:"
  echo "  explorer.exe \"\$(wslpath -w \"$BEST\")\"   # WSL 下用资源管理器打开"
else
  if [ -n "${PKG_IN_CACHE:-}" ]; then
    echo "未定位到源码: $NAME 在 conan 缓存中, 但该版本无源码目录(可能从未在本机构建)。"
    echo "可换用上方带源码的版本, 或重新 conan install/download 拉取源码。"
  else
    echo "未定位到源码。请检查库名拼写, 或用 LIB_SEARCH_ROOTS 环境变量指定搜索根。"
  fi
fi
