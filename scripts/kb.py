#!/usr/bin/env python3
"""
跨平台 kb 命令行工具 - 替代 kb.sh
支持 Windows / macOS / Linux
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

KB_DIR = Path(__file__).resolve().parent.parent
CONTENT_DIR = KB_DIR / "content"
ENV_FILE = KB_DIR / ".env"


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def cmd_new(args):
    title = " ".join(args) if args else "untitled"
    slug = title.lower().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    date = datetime.now().strftime("%Y-%m-%d")
    filepath = CONTENT_DIR / "inbox" / f"{slug}.md"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(
        f'---\ntitle: "{title}"\ndate: {date}\ntags: []\nsummary: ""\nai_generated: false\n---\n\n',
        encoding="utf-8",
    )
    print(f"✅ 已创建: {filepath.relative_to(KB_DIR)}")


def cmd_push(args):
    msg = " ".join(args) if args else "update notes"
    subprocess.run(["git", "add", "-A"], cwd=KB_DIR)
    result = subprocess.run(["git", "commit", "-m", msg], cwd=KB_DIR)
    if result.returncode != 0:
        print("无变更")
        return
    subprocess.run(["git", "push"], cwd=KB_DIR)
    print("✅ 已推送")


def cmd_pull(args):
    subprocess.run(["git", "pull", "--rebase"], cwd=KB_DIR)
    print("✅ 已同步")


def cmd_ai(args):
    load_env()
    script = KB_DIR / "scripts" / "ai_organize.py"
    if args:
        subprocess.run([sys.executable, str(script), "--file", args[0]], cwd=KB_DIR)
    else:
        subprocess.run([sys.executable, str(script), "--all-new"], cwd=KB_DIR)


def cmd_apply(args):
    load_env()
    script = KB_DIR / "scripts" / "ai_organize.py"
    subprocess.run([sys.executable, str(script), "--apply-all"], cwd=KB_DIR)


def cmd_status(args):
    suggestions_dir = KB_DIR / ".ai" / "suggestions"
    count = len(list(suggestions_dir.glob("*.json"))) if suggestions_dir.exists() else 0
    print(f"=== 待整理建议: {count} 条 ===")
    print()
    subprocess.run(["git", "status", "-s"], cwd=KB_DIR)


def cmd_setup(args):
    try:
        import yaml  # noqa: F401
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml", "-q"])

    if not ENV_FILE.exists():
        ENV_FILE.write_text("KB_AI_KEY=sk-or-v1-你的openrouter-key\n")
        print("已创建 .env 文件，请编辑填入你的 API Key")

    quartz_dir = KB_DIR / ".quartz"
    if not quartz_dir.exists():
        print("正在安装 Quartz（本地预览需要）...")
        subprocess.run(["git", "clone", "--depth", "1",
                        "https://github.com/jackyzha0/quartz.git", str(quartz_dir)])
        subprocess.run(["npm", "i"], cwd=quartz_dir)

    print("✅ 环境就绪")


def cmd_preview(args):
    quartz_dir = KB_DIR / ".quartz"
    if not quartz_dir.exists():
        print("Quartz 未安装，先运行: kb setup")
        sys.exit(1)

    content_dir = KB_DIR / "content"
    npx = "npx.cmd" if sys.platform == "win32" else "npx"
    print("🌐 启动本地预览: http://localhost:8080")
    print("   按 Ctrl+C 停止")
    try:
        subprocess.run([npx, "quartz", "build", "--serve", "--directory", str(content_dir)],
                       cwd=quartz_dir)
    except KeyboardInterrupt:
        print("\n已停止")


def main():
    commands = {
        "new": cmd_new,
        "push": cmd_push,
        "pull": cmd_pull,
        "ai": cmd_ai,
        "apply": cmd_apply,
        "status": cmd_status,
        "setup": cmd_setup,
        "preview": cmd_preview,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("用法: kb <命令>")
        print()
        print("  new <标题>     创建新笔记到 inbox")
        print("  push [消息]    提交并推送到 GitHub")
        print("  pull           拉取远程更新")
        print("  preview        本地预览 wiki 站点")
        print("  ai [文件]      运行 AI 整理")
        print("  apply          应用所有 AI 建议")
        print("  status         查看状态")
        print("  setup          初始化环境（含 Quartz）")
        sys.exit(0)

    cmd = sys.argv[1]
    commands[cmd](sys.argv[2:])


if __name__ == "__main__":
    main()
