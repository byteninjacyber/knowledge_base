#!/usr/bin/env python3
"""
Knowledge Base Q&A - 基于笔记内容的本地问答
用法: python scripts/kb_ask.py "你的问题"
"""

from __future__ import annotations
import os
import sys
import json
import re
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"


def load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def get_all_notes() -> List[Tuple[str, str]]:
    """返回 [(文件路径, 内容), ...]"""
    notes = []
    for md in CONTENT_DIR.rglob("*.md"):
        if md.name.startswith("."):
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        notes.append((str(md.relative_to(ROOT)), text))
    return notes


def strip_frontmatter(text: str) -> str:
    """去掉 YAML frontmatter"""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].strip()
    return text


def search_relevant(question: str, notes: List[Tuple[str, str]], top_k: int = 3) -> List[Tuple[str, str]]:
    """简单关键词匹配搜索最相关的笔记片段"""
    # 提取问题关键词（去掉常见停用词）
    stopwords = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都",
                 "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会",
                 "着", "没有", "看", "好", "自己", "这", "他", "她", "它", "们",
                 "what", "is", "the", "a", "an", "how", "why", "when", "where",
                 "do", "does", "can", "could", "would", "should", "to", "in", "of"}

    keywords = []
    for word in re.split(r'[\s,，。？?!！、]+', question.lower()):
        if word and word not in stopwords and len(word) > 1:
            keywords.append(word)

    if not keywords:
        keywords = [question.lower()]

    # 对每篇笔记打分
    scored = []
    for path, content in notes:
        body = strip_frontmatter(content).lower()
        score = 0
        for kw in keywords:
            score += body.count(kw)
        if score > 0:
            scored.append((score, path, content))

    scored.sort(reverse=True)

    # 返回 top_k 篇，每篇截取前 2000 字符
    results = []
    for _, path, content in scored[:top_k]:
        body = strip_frontmatter(content)[:2000]
        results.append((path, body))
    return results


def ask_llm(question: str, context: str) -> str:
    """调用 GitHub Models 回答问题"""
    import urllib.request

    api_key = os.environ.get("KB_AI_KEY")
    if not api_key:
        print("ERROR: 请设置 KB_AI_KEY 环境变量（在 .env 文件中）", file=sys.stderr)
        sys.exit(1)

    model = "gpt-4o-mini"
    base_url = "https://models.inference.ai.azure.com"

    system_prompt = """你是一个知识库问答助手。根据提供的笔记内容回答用户问题。
规则：
1. 只基于提供的笔记内容回答，不要编造信息
2. 如果笔记中没有相关信息，明确说"知识库中没有找到相关内容"
3. 回答要简洁、准确、有条理
4. 如果涉及代码，保持代码格式"""

    data = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"参考资料:\n{context}\n\n问题: {question}"},
        ],
        "temperature": 0.3,
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(f"{base_url}/chat/completions", data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"AI 调用失败: {e}"


def main():
    if len(sys.argv) < 2:
        print("用法: kb ask \"你的问题\"")
        print("示例: kb ask \"C++ 智能指针有哪几种？\"")
        sys.exit(0)

    question = " ".join(sys.argv[1:])
    load_env()

    print(f"🔍 搜索中...")
    notes = get_all_notes()
    relevant = search_relevant(question, notes)

    if not relevant:
        print("❌ 知识库中没有找到相关内容")
        sys.exit(0)

    print(f"📄 找到 {len(relevant)} 篇相关笔记: {', '.join(p for p, _ in relevant)}")
    print(f"🤖 正在回答...\n")

    context = "\n\n---\n\n".join(
        f"【{path}】\n{body}" for path, body in relevant
    )

    answer = ask_llm(question, context)
    print(answer)


if __name__ == "__main__":
    main()
