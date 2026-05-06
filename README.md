# Personal Knowledge Base

Obsidian + Markdown + Git + Quartz + AI (OpenRouter)

## 新电脑初始化

### 前置依赖

| 系统 | 需要安装 |
|---|---|
| **Windows** | [Git](https://git-scm.com/download/win) + [Python3](https://www.python.org/downloads/)（安装时勾选 Add to PATH） |
| **macOS** | `xcode-select --install`（自带 Git）+ `brew install python` 或去官网装 |
| **Linux** | `sudo apt install git python3 python3-pip` |

### 克隆 + 初始化

```bash
git clone git@github.com:byteninjacyber/knowledge_base.git
cd knowledge_base
python3 scripts/kb.py setup
```

Windows 下用 `python` 替代 `python3`：
```cmd
python scripts\kb.py setup
```

然后编辑 `.env` 填入 API Key。

## 日常命令（跨平台通用）

```bash
python3 scripts/kb.py new "笔记标题"       # 新建笔记
python3 scripts/kb.py push                  # 提交 + 发布
python3 scripts/kb.py push "描述信息"       # 带描述提交
python3 scripts/kb.py pull                  # 拉取更新
python3 scripts/kb.py ai                    # AI 整理所有新笔记
python3 scripts/kb.py ai content/inbox/x.md # AI 整理单个文件
python3 scripts/kb.py apply                 # 应用 AI 建议
python3 scripts/kb.py status                # 查看状态
```

### 设置快捷命令（可选）

**macOS / Linux** — 加到 `~/.bashrc` 或 `~/.zshrc`：
```bash
alias kb='python3 /你的路径/knowledge_base/scripts/kb.py'
```

**Windows** — 创建 `kb.bat` 放到 PATH 中的目录：
```bat
@python "C:\你的路径\knowledge_base\scripts\kb.py" %*
```

设置后直接用：
```bash
kb new "Docker 网络"
kb push
kb ai
```

## 典型工作流

```bash
kb new "Docker 网络原理"        # 创建
# 用 Obsidian / VS Code / 任何编辑器写笔记
kb ai content/inbox/docker-网络原理.md  # AI 整理
kb apply                         # 应用建议
kb push "note: docker networking"    # 发布
```

## 配置文件

| 文件 | 用途 | 入 Git? |
|---|---|---|
| `.env` | API Key | ❌ |
| `.ai/config.yaml` | 模型/Prompt 配置 | ✅ |

## 换电脑清单

1. 装 Git + Python3
2. `git clone` + `python3 scripts/kb.py setup`
3. 编辑 `.env` 填 Key
4. 完成
