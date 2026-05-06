# Personal Knowledge Base

Obsidian + Markdown + Git + Quartz + AI

## 快速开始

```bash
# 1. 用 Obsidian 打开此目录作为 Vault
# 2. 在 content/ 下写笔记
# 3. push 到 GitHub Private Repo
# 4. GitHub Actions 自动构建 wiki 站点 + AI 整理
```

## 结构

```
content/          # 笔记正文（Quartz 构建源）
  inbox/          # 待整理
  notes/          # 永久笔记
  projects/       # 项目文档
  references/     # 外部资源
assets/           # 附件
.ai/
  config.yaml     # AI 模型配置
  suggestions/    # AI 建议（人工确认后应用）
scripts/
  ai_organize.py  # AI 整理脚本
templates/        # 笔记模板
```

## AI 整理

```bash
# 设置 API Key
export KB_AI_KEY=sk-your-key

# 处理单个文件
python scripts/ai_organize.py -f content/notes/example.md

# 处理所有新文件
python scripts/ai_organize.py --all-new

# 预览不写入
python scripts/ai_organize.py --dry-run

# 应用 AI 建议
python scripts/ai_organize.py --apply-all
```

切换模型：编辑 `.ai/config.yaml` 中的 `provider` 字段。

## 部署

Push 到 GitHub 后，Actions 自动：
1. Quartz 构建静态 wiki 站点 → GitHub Pages
2. AI 扫描新笔记 → 生成建议到 `.ai/suggestions/`

## 迁移

所有数据为纯 Markdown + YAML frontmatter，可随时切换到任何支持 Markdown 的工具。
