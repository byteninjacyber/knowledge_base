# Personal Knowledge Base

Obsidian + Markdown + Git + Quartz + AI (OpenRouter)

## 新电脑初始化

```bash
git clone git@github.com:byteninjacyber/knowledge_base.git
cd knowledge_base
bash scripts/setup.sh
```

依赖仅：Git + Python3 + pip (pyyaml)。Obsidian 可选。

## 日常命令

在仓库目录下，用 `./scripts/kb.sh` 或设置别名后直接用 `kb`：

```bash
# 设置别名（加到 ~/.bashrc 或 ~/.zshrc）
alias kb='/path/to/knowledge_base/scripts/kb.sh'
```

| 命令 | 作用 |
|---|---|
| `kb new 笔记标题` | 创建新笔记到 inbox |
| `kb push` | 提交 + 推送（自动触发发布） |
| `kb push "描述"` | 带自定义 commit 信息 |
| `kb pull` | 拉取远程更新 |
| `kb ai` | AI 整理所有新笔记 |
| `kb ai content/inbox/xxx.md` | AI 整理单个文件 |
| `kb apply` | 应用所有 AI 建议到笔记 |
| `kb status` | 查看待处理建议和 git 状态 |

## 典型工作流

```bash
kb new "Docker 网络原理"     # 创建笔记
# ... 用 Obsidian 或任何编辑器写内容 ...
kb ai content/inbox/docker-网络原理.md  # AI 生成摘要+标签
kb apply                      # 确认并应用建议
kb push "note: docker networking"  # 发布
```

## 配置

- `.env` — API Key（不入 Git）
- `.ai/config.yaml` — 模型和 prompt 配置

## 换电脑清单

1. `git clone` 仓库
2. `bash scripts/setup.sh`
3. 编辑 `.env` 填入 API Key
4. 完成，开始写
