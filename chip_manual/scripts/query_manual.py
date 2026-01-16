#!/usr/bin/env python3
"""芯片手册查询 - Gemini 后端（零推断模式，支持多芯片、多文档类型）"""
import os
import sys
import json
import argparse
import yaml
from google import genai
from google.genai import types

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(SKILL_DIR, "config.yaml")

# 文档类型定义
DOC_TYPES = {
    "ref": {
        "key": "reference_manual",
        "name": "参考手册",
        "desc": "寄存器定义、硬件配置、外设规格等"
    },
    "api": {
        "key": "api_reference",
        "name": "API 参考",
        "desc": "驱动库函数接口、参数说明、使用示例等"
    }
}


def load_config() -> dict:
    """加载配置文件"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_api_key(config: dict) -> str:
    """获取 API Key，优先环境变量"""
    return os.environ.get("GEMINI_API_KEY") or config.get("api_key", "")


def find_chip(config: dict, chip_hint: str) -> tuple[str, dict] | None:
    """根据芯片名或别名查找芯片配置"""
    chips = config.get("chips", {})
    chip_hint_upper = chip_hint.upper()

    for chip_name, chip_config in chips.items():
        if chip_name.upper() == chip_hint_upper:
            return chip_name, chip_config
        aliases = chip_config.get("aliases", [])
        for alias in aliases:
            if alias.upper() == chip_hint_upper:
                return chip_name, chip_config

    return None


def get_available_docs(chip_config: dict) -> list[str]:
    """获取芯片可用的文档类型"""
    available = []
    for doc_type, doc_info in DOC_TYPES.items():
        if chip_config.get(doc_info["key"]):
            available.append(doc_type)
    return available


def list_chips(config: dict) -> list[dict]:
    """列出所有可用芯片"""
    result = []
    for chip_name, chip_config in config.get("chips", {}).items():
        available_docs = []
        for doc_type, doc_info in DOC_TYPES.items():
            if chip_config.get(doc_info["key"]):
                available_docs.append({
                    "type": doc_type,
                    "name": doc_info["name"],
                    "desc": doc_info["desc"]
                })
        result.append({
            "name": chip_name,
            "description": chip_config.get("description", ""),
            "aliases": chip_config.get("aliases", []),
            "available_docs": available_docs
        })
    return result


def query(chip: str, question: str, doc_type: str = "ref") -> dict:
    """查询芯片手册"""
    config = load_config()

    api_key = get_api_key(config)
    if not api_key:
        return {"error": "请设置 GEMINI_API_KEY 环境变量或在 config.yaml 中配置 api_key"}

    # 验证文档类型
    if doc_type not in DOC_TYPES:
        return {
            "error": f"无效的文档类型 '{doc_type}'",
            "valid_types": list(DOC_TYPES.keys())
        }

    chip_info = find_chip(config, chip)
    if not chip_info:
        available = list_chips(config)
        return {
            "error": f"未找到芯片 '{chip}'",
            "available_chips": available
        }

    chip_name, chip_config = chip_info
    doc_info = DOC_TYPES[doc_type]
    doc_path_key = doc_info["key"]

    # 检查是否有该类型的文档
    if not chip_config.get(doc_path_key):
        available_docs = get_available_docs(chip_config)
        return {
            "error": f"芯片 '{chip_name}' 没有 {doc_info['name']} 文档",
            "available_doc_types": available_docs
        }

    manual_path = os.path.join(SKILL_DIR, chip_config[doc_path_key])

    if not os.path.exists(manual_path):
        return {"error": f"文档文件不存在: {manual_path}"}

    client = genai.Client(api_key=api_key)
    model = config.get("model", "gemini-3-flash-preview")

    with open(manual_path, "r", encoding="utf-8") as f:
        manual = f.read()

    # 根据文档类型调整 prompt
    if doc_type == "api":
        prompt = f"""你是 {chip_name} 驱动库 API 查询助手。

【严格规则 - 必须遵守】
1. 只能基于下方 API 文档内容回答，禁止使用任何外部知识
2. 禁止推断、猜测、补充任何文档中没有的信息
3. 如果文档中找不到答案，必须回答："API 文档中未找到相关信息"
4. 引用时必须标注函数名、参数、所属模块
5. 提供代码示例时，必须来自文档中的示例

问题：{question}

===== {chip_name} API 参考文档开始 =====
{manual}
===== API 文档结束 =====

请严格基于 API 文档回答："""
    else:
        prompt = f"""你是 {chip_name} 芯片手册查询助手。

【严格规则 - 必须遵守】
1. 只能基于下方手册内容回答，禁止使用任何外部知识
2. 禁止推断、猜测、补充任何手册中没有的信息
3. 如果手册中找不到答案，必须回答："手册中未找到相关信息"
4. 引用时必须标注具体位置（章节号、寄存器地址、表格名）
5. 不要添加任何手册之外的建议或解释

问题：{question}

===== {chip_name} 手册内容开始 =====
{manual}
===== 手册内容结束 =====

请严格基于手册内容回答："""

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0)
        )
        return {
            "chip": chip_name,
            "doc_type": doc_type,
            "doc_name": doc_info["name"],
            "answer": response.text,
            "model": model,
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }


def main():
    parser = argparse.ArgumentParser(
        description="芯片手册查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
文档类型:
  ref   参考手册 - 寄存器定义、硬件配置（默认）
  api   API 参考 - 驱动库函数接口、使用示例

示例:
  %(prog)s --chip V32G410X "GPIO 寄存器地址"
  %(prog)s --chip V32G410X --type api "USART_Init 函数用法"
  %(prog)s -c V32G410 -t api "GPIO_SetBits 参数说明"
"""
    )
    parser.add_argument("--chip", "-c", help="芯片型号（如 RN7326, V32G410X）")
    parser.add_argument("--type", "-t", default="ref", choices=["ref", "api"],
                        help="文档类型: ref=参考手册, api=API参考 (默认: ref)")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用芯片及文档")
    parser.add_argument("question", nargs="?", help="查询问题")

    args = parser.parse_args()

    if args.list:
        config = load_config()
        chips = list_chips(config)
        print(json.dumps({"chips": chips}, ensure_ascii=False, indent=2))
        return

    if not args.chip:
        print(json.dumps({"error": "请使用 --chip 指定芯片型号，或用 --list 查看可用芯片"}, ensure_ascii=False))
        sys.exit(1)

    if not args.question:
        print(json.dumps({"error": "请提供查询问题"}, ensure_ascii=False))
        sys.exit(1)

    result = query(args.chip, args.question, args.type)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
