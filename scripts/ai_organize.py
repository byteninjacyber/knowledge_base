#!/usr/bin/env python3
"""
Knowledge Base AI Assistant
支持 DeepSeek / OpenAI / Claude，统一接口自动整理笔记。
用法: python scripts/ai_organize.py [--file path] [--all-new] [--dry-run]
"""

from __future__ import annotations
import os
import sys
import yaml
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Tuple, List

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / ".ai" / "config.yaml"
SUGGESTIONS_DIR = ROOT / ".ai" / "suggestions"
CONTENT_DIR = ROOT / "content"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_api_key():
    key = os.environ.get("KB_AI_KEY")
    if not key:
        print("ERROR: 请设置环境变量 KB_AI_KEY", file=sys.stderr)
        sys.exit(1)
    return key


def get_base_url(provider: str) -> str:
    urls = {
        "deepseek": "https://api.deepseek.com/v1",
        "openai": "https://api.openai.com/v1",
        "claude": "https://api.anthropic.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta",
    }
    custom = os.environ.get("KB_AI_BASE_URL")
    return custom or urls.get(provider, urls["openai"])


def call_llm(provider: str, model: str, prompt: str, content: str, api_key: str) -> str:
    """统一调用接口 - 所有支持 OpenAI 兼容格式的模型"""
    import urllib.request
    import urllib.error

    base_url = get_base_url(provider)

    if provider == "gemini":
        url = f"{base_url}/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = json.dumps({
            "contents": [{"parts": [{"text": f"{prompt}\n\n{content}"}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024},
        }).encode()
    elif provider == "claude":
        url = f"{base_url}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        data = json.dumps({
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": f"{prompt}\n\n{content}"}],
        }).encode()
    else:
        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        data = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个知识管理助手。"},
                {"role": "user", "content": f"{prompt}\n\n{content}"},
            ],
            "temperature": 0.3,
        }).encode()

    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if provider == "gemini":
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()
            elif provider == "claude":
                return result["content"][0]["text"].strip()
            else:
                return result["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        print(f"API Error: {e.code} {e.read().decode()}", file=sys.stderr)
        return ""


def parse_frontmatter(text: str) -> Tuple[dict, str]:
    """解析 markdown frontmatter"""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()
    return meta, body


def write_frontmatter(meta: dict, body: str) -> str:
    """重新组装 markdown"""
    fm = yaml.dump(meta, allow_unicode=True, default_flow_style=False).strip()
    return f"---\n{fm}\n---\n\n{body}\n"


def get_new_files() -> List[Path]:
    """获取最近 git 变更的 markdown 文件"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "--", "content/"],
            capture_output=True, text=True, cwd=ROOT
        )
        files = [ROOT / f for f in result.stdout.strip().split("\n") if f.endswith(".md")]
        return [f for f in files if f.exists()]
    except Exception:
        return []


def process_file(filepath: Path, config: dict, api_key: str, dry_run: bool = False):
    """处理单个文件：生成摘要和标签建议"""
    text = filepath.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    if not body.strip():
        return

    provider = config["provider"]
    models = config["models"]
    prompts = config["prompts"]

    suggestions = {}

    # 生成摘要
    if not meta.get("summary"):
        summary = call_llm(provider, models["summarize"], prompts["summarize"], body, api_key)
        if summary:
            suggestions["summary"] = summary

    # 生成标签
    if not meta.get("tags") or meta["tags"] == []:
        tags_raw = call_llm(provider, models["tag"], prompts["tag"], body, api_key)
        if tags_raw:
            suggestions["tags"] = [t.strip() for t in tags_raw.split(",")]

    # 链接建议
    links = call_llm(provider, models["link_suggest"], prompts["link_suggest"], body, api_key)
    if links:
        suggestions["link_suggestions"] = links.strip().split("\n")

    if not suggestions:
        print(f"  跳过 (无需更新): {filepath.relative_to(ROOT)}")
        return

    if dry_run:
        print(f"  [DRY RUN] {filepath.relative_to(ROOT)}: {json.dumps(suggestions, ensure_ascii=False)}")
        return

    # 写入 suggestions 目录，等待人工确认
    suggestion_file = SUGGESTIONS_DIR / f"{filepath.stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    suggestion_file.write_text(json.dumps({
        "file": str(filepath.relative_to(ROOT)),
        "suggestions": suggestions,
        "timestamp": datetime.now().isoformat(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  建议已保存: {suggestion_file.relative_to(ROOT)}")


def apply_suggestions(suggestion_file: Path):
    """应用 AI 建议到原始文件"""
    data = json.loads(suggestion_file.read_text(encoding="utf-8"))
    filepath = ROOT / data["file"]
    suggestions = data["suggestions"]

    text = filepath.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    if "summary" in suggestions:
        meta["summary"] = suggestions["summary"]
    if "tags" in suggestions:
        meta["tags"] = suggestions["tags"]

    filepath.write_text(write_frontmatter(meta, body), encoding="utf-8")
    suggestion_file.unlink()
    print(f"  已应用: {filepath.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="AI 知识库整理工具")
    parser.add_argument("--file", "-f", help="处理单个文件")
    parser.add_argument("--all-new", action="store_true", help="处理所有新变更文件")
    parser.add_argument("--dry-run", action="store_true", help="只预览不写入")
    parser.add_argument("--apply", "-a", help="应用指定建议文件")
    parser.add_argument("--apply-all", action="store_true", help="应用所有建议")
    args = parser.parse_args()

    config = load_config()
    api_key = get_api_key()

    if args.apply:
        apply_suggestions(Path(args.apply))
        return

    if args.apply_all:
        for f in SUGGESTIONS_DIR.glob("*.json"):
            apply_suggestions(f)
        return

    files = []
    if args.file:
        files = [Path(args.file).resolve()]
    elif args.all_new:
        files = get_new_files()
    else:
        # 默认处理 content/ 下所有 md
        files = list(CONTENT_DIR.rglob("*.md"))

    print(f"处理 {len(files)} 个文件 (provider: {config['provider']})")
    for f in files:
        print(f"  处理: {f.relative_to(ROOT)}")
        process_file(f, config, api_key, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
