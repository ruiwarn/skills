#!/usr/bin/env python3
"""
GitHub 代码搜索工具
用于在实现新功能前搜索 GitHub 上的参考实现
支持通过环境变量 GITHUB_TOKEN 提供认证token以提高API限额
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Any

# 从环境变量获取 GitHub Token（可选）
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')


def search_github_repos(
    keywords: str,
    language: str = "",
    sort: str = "stars",
    order: str = "desc",
    per_page: int = 10
) -> List[Dict[str, Any]]:
    """
    搜索 GitHub 仓库

    Args:
        keywords: 搜索关键词
        language: 编程语言过滤（可选）
        sort: 排序方式 (stars, forks, updated)
        order: 排序顺序 (desc, asc)
        per_page: 每页结果数量

    Returns:
        搜索结果列表
    """
    # 构建搜索查询
    query = keywords
    if language:
        query += f" language:{language}"

    # URL 编码
    encoded_query = urllib.parse.quote(query)

    # 构建 API URL
    url = f"https://api.github.com/search/repositories?q={encoded_query}&sort={sort}&order={order}&per_page={per_page}"

    try:
        # 创建请求
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('User-Agent', 'Claude-Code-GitHub-Search')

        # 如果有 token，添加认证头（提高限额：60/h → 5000/h）
        if GITHUB_TOKEN:
            req.add_header('Authorization', f'token {GITHUB_TOKEN}')

        # 发送请求
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        # 提取有用信息
        results = []
        for item in data.get('items', []):
            # 限制描述长度避免浪费token
            desc = item.get('description', '') or ''
            if len(desc) > 200:
                desc = desc[:200] + '...'

            results.append({
                'name': item['name'],
                'full_name': item['full_name'],
                'description': desc,
                'html_url': item['html_url'],
                'stars': item['stargazers_count'],
                'forks': item['forks_count'],
                'language': item.get('language', ''),
                'updated_at': item['updated_at'],
                'license': item.get('license', {}).get('name', 'Unknown') if item.get('license') else 'No license',
                'topics': item.get('topics', []),
            })

        return results

    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("\n" + "="*70, file=sys.stderr)
            print("⚠️  GitHub API 速率限制", file=sys.stderr)
            print("="*70, file=sys.stderr)
            if GITHUB_TOKEN:
                print("即使使用了 Token 仍然超限，请稍后重试。", file=sys.stderr)
            else:
                print("未认证请求限制：60次/小时", file=sys.stderr)
                print("使用 GitHub Token 可提升至：5000次/小时", file=sys.stderr)
                print("\n📝 配置 GitHub Token 步骤：", file=sys.stderr)
                print("1. 访问 https://github.com/settings/tokens", file=sys.stderr)
                print("2. 点击 'Generate new token' → 'Generate new token (classic)'", file=sys.stderr)
                print("3. 填写描述，无需勾选任何权限（public repo 搜索不需要权限）", file=sys.stderr)
                print("4. 点击 'Generate token'，复制生成的 token", file=sys.stderr)
                print("5. 设置环境变量：", file=sys.stderr)
                print("   - Linux/Mac: export GITHUB_TOKEN=ghp_xxxxxxxxxxxx", file=sys.stderr)
                print("   - Windows: set GITHUB_TOKEN=ghp_xxxxxxxxxxxx", file=sys.stderr)
                print("   - 或添加到 ~/.bashrc 或 ~/.zshrc 永久保存", file=sys.stderr)
                print("="*70, file=sys.stderr)
        else:
            print(f"HTTP 错误 {e.code}: {e.reason}", file=sys.stderr)
        return []
    except urllib.error.URLError as e:
        print(f"网络错误: {e.reason}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"搜索失败: {str(e)}", file=sys.stderr)
        return []


def search_github_code(
    keywords: str,
    language: str = "",
    per_page: int = 10
) -> List[Dict[str, Any]]:
    """
    搜索 GitHub 代码片段

    Args:
        keywords: 搜索关键词
        language: 编程语言过滤（可选）
        per_page: 每页结果数量

    Returns:
        代码搜索结果列表
    """
    # 构建搜索查询
    query = keywords
    if language:
        query += f" language:{language}"

    # URL 编码
    encoded_query = urllib.parse.quote(query)

    # 构建 API URL
    url = f"https://api.github.com/search/code?q={encoded_query}&per_page={per_page}"

    try:
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('User-Agent', 'Claude-Code-GitHub-Search')

        # 添加认证token
        if GITHUB_TOKEN:
            req.add_header('Authorization', f'token {GITHUB_TOKEN}')

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        # 提取有用信息
        results = []
        for item in data.get('items', []):
            # 限制描述长度
            desc = item['repository'].get('description', '') or ''
            if len(desc) > 150:
                desc = desc[:150] + '...'

            results.append({
                'name': item['name'],
                'path': item['path'],
                'repository': item['repository']['full_name'],
                'html_url': item['html_url'],
                'repo_url': item['repository']['html_url'],
                'repo_description': desc,
                'repo_stars': item['repository']['stargazers_count'],
                'language': item['repository'].get('language', ''),
            })

        return results

    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("\n" + "="*70, file=sys.stderr)
            print("⚠️  GitHub API 速率限制", file=sys.stderr)
            print("="*70, file=sys.stderr)
            if GITHUB_TOKEN:
                print("即使使用了 Token 仍然超限，请稍后重试。", file=sys.stderr)
            else:
                print("未认证请求限制：60次/小时", file=sys.stderr)
                print("使用 GitHub Token 可提升至：5000次/小时", file=sys.stderr)
                print("\n📝 配置 GitHub Token 步骤：", file=sys.stderr)
                print("1. 访问 https://github.com/settings/tokens", file=sys.stderr)
                print("2. 点击 'Generate new token' → 'Generate new token (classic)'", file=sys.stderr)
                print("3. 填写描述，无需勾选任何权限（public repo 搜索不需要权限）", file=sys.stderr)
                print("4. 点击 'Generate token'，复制生成的 token", file=sys.stderr)
                print("5. 设置环境变量：", file=sys.stderr)
                print("   - Linux/Mac: export GITHUB_TOKEN=ghp_xxxxxxxxxxxx", file=sys.stderr)
                print("   - Windows: set GITHUB_TOKEN=ghp_xxxxxxxxxxxx", file=sys.stderr)
                print("   - 或添加到 ~/.bashrc 或 ~/.zshrc 永久保存", file=sys.stderr)
                print("="*70, file=sys.stderr)
        else:
            print(f"HTTP 错误 {e.code}: {e.reason}", file=sys.stderr)
        return []
    except urllib.error.URLError as e:
        print(f"网络错误: {e.reason}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"搜索失败: {str(e)}", file=sys.stderr)
        return []


def search_with_fallback(keywords: str, language: str = "", search_type: str = "repo") -> List[Dict[str, Any]]:
    """
    智能降级搜索：逐步放宽搜索条件直到找到结果

    Args:
        keywords: 原始搜索关键词
        language: 语言过滤
        search_type: "repo" 或 "code"

    Returns:
        搜索结果列表
    """
    search_func = search_github_repos if search_type == "repo" else search_github_code

    # 策略1: 完整关键词 + 语言
    if language:
        print(f"尝试1: '{keywords}' + 语言:{language}", file=sys.stderr)
        results = search_func(keywords, language)
        if results:
            return results

    # 策略2: 完整关键词（不限语言）
    print(f"尝试2: '{keywords}' (不限语言)", file=sys.stderr)
    results = search_func(keywords, "")
    if results:
        return results

    # 策略3: 简化关键词（取前2-3个词）
    simplified = ' '.join(keywords.split()[:3])
    if simplified != keywords:
        print(f"尝试3: '{simplified}' (简化关键词)", file=sys.stderr)
        results = search_func(simplified, "")
        if results:
            return results

    # 策略4: 核心词（仅第1个词）
    core = keywords.split()[0]
    if core != simplified:
        print(f"尝试4: '{core}' (核心词)", file=sys.stderr)
        results = search_func(core, "")
        if results:
            return results

    return []


def format_results(results: List[Dict[str, Any]], search_type: str = "repo") -> str:
    """
    格式化搜索结果为 Markdown

    Args:
        results: 搜索结果
        search_type: 搜索类型 (repo 或 code)

    Returns:
        格式化的 Markdown 字符串
    """
    if not results:
        return "未找到相关结果"

    output = []

    if search_type == "repo":
        output.append(f"找到 {len(results)} 个仓库:\n")

        for i, repo in enumerate(results, 1):
            # 精简格式: 序号、名称、stars、语言、年份、描述
            year = repo['updated_at'][:4]
            lang = repo['language'] or '未知'
            desc = repo['description'] or '无描述'

            output.append(f"{i}. [{repo['full_name']}]({repo['html_url']})")
            output.append(f"   ⭐{repo['stars']} | {lang} | {year} | {desc}")
            output.append("")

    else:  # code
        output.append(f"找到 {len(results)} 个代码文件:\n")

        for i, code in enumerate(results, 1):
            # 精简格式: 序号、文件名、仓库、stars、语言
            lang = code['language'] or '未知'
            desc = code['repo_description'] or '无描述'

            output.append(f"{i}. [{code['path']}]({code['html_url']})")
            output.append(f"   仓库: [{code['repository']}]({code['repo_url']}) | ⭐{code['repo_stars']} | {lang}")
            if desc != '无描述':
                output.append(f"   {desc}")
            output.append("")

    return "\n".join(output)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  搜索仓库: python github_search.py repo <关键词> [语言]")
        print("  搜索代码: python github_search.py code <关键词> [语言]")
        print()
        print("示例:")
        print("  python github_search.py repo 'FFT algorithm' C")
        print("  python github_search.py code 'modbus protocol' C")
        sys.exit(1)

    search_type = sys.argv[1].lower()

    if search_type not in ['repo', 'code']:
        print("错误: 搜索类型必须是 'repo' 或 'code'", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 3:
        print("错误: 请提供搜索关键词", file=sys.stderr)
        sys.exit(1)

    keywords = sys.argv[2]
    language = sys.argv[3] if len(sys.argv) > 3 else ""

    print(f"正在搜索 GitHub {search_type}...")
    print(f"关键词: {keywords}")
    if language:
        print(f"语言: {language}")
    if GITHUB_TOKEN:
        print("已使用 GitHub Token (5000次/小时)")
    else:
        print("未使用 Token (60次/小时) - 设置 GITHUB_TOKEN 环境变量以提高限额")
    print()

    # 执行智能降级搜索
    results = search_with_fallback(keywords, language, search_type)

    # 输出结果
    if results:
        print(format_results(results, search_type))
    else:
        print("\n所有尝试均未找到结果，建议:")
        print("1. 使用更通用的关键词")
        print("2. 尝试使用 WebSearch 搜索技术文章或论文")
        print("3. 检查拼写是否正确")


if __name__ == "__main__":
    main()
