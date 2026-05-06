#!/bin/bash
set -e

KB_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$KB_DIR"

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

cmd="$1"
shift 2>/dev/null || true

case "$cmd" in
    new)
        title="${*:-untitled}"
        slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')
        date=$(date +%Y-%m-%d)
        file="content/inbox/${slug}.md"
        cat > "$file" <<EOF
---
title: "$title"
date: $date
tags: []
summary: ""
ai_generated: false
---

EOF
        echo "✅ 已创建: $file"
        ;;

    push)
        msg="${*:-update notes}"
        git add -A
        git commit -m "$msg" || echo "无变更"
        git push
        echo "✅ 已推送"
        ;;

    pull)
        git pull --rebase
        echo "✅ 已同步"
        ;;

    ai)
        target="$1"
        if [ -n "$target" ]; then
            python3 scripts/ai_organize.py --file "$target"
        else
            python3 scripts/ai_organize.py --all-new
        fi
        ;;

    apply)
        python3 scripts/ai_organize.py --apply-all
        ;;

    status)
        echo "=== 待整理建议 ==="
        ls .ai/suggestions/*.json 2>/dev/null | wc -l | xargs -I{} echo "{} 条"
        echo ""
        echo "=== Git 状态 ==="
        git status -s
        ;;

    *)
        echo "用法: kb <命令>"
        echo ""
        echo "  new <标题>     创建新笔记 (到 inbox)"
        echo "  push [消息]    提交并推送到 GitHub"
        echo "  pull           拉取远程更新"
        echo "  ai [文件]      运行 AI 整理"
        echo "  apply          应用所有 AI 建议"
        echo "  status         查看状态"
        ;;
esac
