# Personal Knowledge Base

个人知识库，基于 Obsidian + Markdown + Git + Quartz + AI 构建。

- **在线 Wiki**：https://byteninjacyber.github.io/knowledge_base/
- **AI 问答**：https://kb.shuzistore.com （网页内置聊天框）

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 编辑器 | Obsidian / VS Code | 纯 Markdown，无插件依赖 |
| 静态站点 | Quartz v4.5.2 | GitHub Pages 自动部署 |
| AI 整理 | OpenRouter API | 笔记结构优化建议 |
| AI 问答 | GitHub Models (gpt-4o-mini) | Cloudflare Worker + 网页聊天框 |
| 部署 | GitHub Actions | push 后约 45 秒自动上线 |

## 知识分类

```
content/notes/
├── programming-languages/   # 编程语言（C/C++、Go、Rust、Python）
├── operating-systems/       # 操作系统（Linux 内核、进程、内存）
├── computer-network/        # 计算机网络（TCP/IP、HTTP、DNS）
├── database/                # 数据库（MySQL、Redis、存储引擎）
├── system-architecture/     # 系统架构（分布式、微服务、设计模式）
├── data-structures-and-algorithms/  # 数据结构与算法
├── devops/                  # 运维部署（Docker、K8s、CI/CD）
├── artificial-intelligence/ # 人工智能（ML、DL、大模型）
├── software-engineering/    # 软件工程（项目管理、测试、规范）
└── industry-knowledge/      # 行业知识（业务领域、行业趋势）
```

其他目录：

- `content/inbox/` — 待整理的快速笔记
- `content/projects/` — 项目相关文档
- `content/references/` — 外部资源收集

## 新电脑初始化

### 前置依赖

| 系统 | 需要安装 |
|------|------|
| **Windows** | [Git](https://git-scm.com/download/win) + [Python3](https://www.python.org/downloads/)（勾选 Add to PATH）+ [Node.js](https://nodejs.org/)（预览用） |
| **macOS** | `xcode-select --install` + `brew install python node` |
| **Linux** | `sudo apt install git python3 python3-pip nodejs npm` |

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

## 日常命令

```bash
python3 scripts/kb.py new "笔记标题"       # 新建笔记（默认到 inbox/）
python3 scripts/kb.py push                  # 提交 + 发布
python3 scripts/kb.py push "描述信息"       # 带描述提交
python3 scripts/kb.py pull                  # 拉取更新
python3 scripts/kb.py ai                    # AI 整理所有新笔记
python3 scripts/kb.py ai content/inbox/x.md # AI 整理单个文件
python3 scripts/kb.py apply                 # 应用 AI 建议
python3 scripts/kb.py preview               # 本地预览（localhost:9090）
python3 scripts/kb.py ask "问题"            # CLI 问答
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
kb ask "什么是虚函数表"
```

## 典型工作流

```bash
kb new "Docker 网络原理"                    # 1. 创建笔记
# 用 Obsidian / VS Code / 任何编辑器写内容
kb ai content/inbox/docker-网络原理.md      # 2. AI 整理（可选）
kb apply                                    # 3. 应用建议（可选）
# 将笔记移到对应分类目录，如 content/notes/devops/
kb preview                                  # 4. 本地预览
kb push "note: docker networking"           # 5. 发布上线
```

## 配置文件

| 文件 | 用途 | 入 Git? |
|------|------|---------|
| `.env` | GitHub Token（AI 问答用） | ❌ |
| `.ai/config.yaml` | AI 整理模型/Prompt 配置 | ✅ |
| `worker/wrangler.toml` | Cloudflare Worker 配置 | ✅ |

## 项目结构

```
├── content/                 # 所有笔记内容（Markdown）
├── scripts/
│   ├── kb.py                # CLI 主入口
│   ├── kb_ask.py            # AI 问答逻辑
│   └── ai_organize.py       # AI 整理逻辑
├── worker/
│   ├── index.js             # Cloudflare Worker（AI 问答后端）
│   └── wrangler.toml        # Worker 配置
├── .quartz/                 # Quartz 静态站点生成器
├── .ai/                     # AI 配置和建议缓存
└── .github/workflows/       # GitHub Actions 自动部署
```

## 换电脑清单

1. 装 Git + Python3
2. `git clone` + `python3 scripts/kb.py setup`
3. 编辑 `.env` 填 Key
4. 完成
