# SmartDoc RAG —— 智能文档检索增强生成系统

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.3.1-green.svg)](https://langchain.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**从文档解析到智能问答的全链路 RAG 系统**，支持 PDF/TXT 等多格式文档的 AI 驱动解析、语义向量检索、多文档隔离管理与可控幻觉抑制。

## 技术架构

```
                      ┌──────────────────────────────┐
   PDF / TXT ─────────▶  Marker AI 解析引擎            │
                      │  · 布局分析  · 表格识别        │
                      │  · OCR识别   · 图片提取        │
                      └──────────┬───────────────────┘
                                 │ Markdown 段落
                                 ▼
                      ┌──────────────────────────────┐
                      │  规则分块器 (RuleChunker)       │
                      │  · 按段落类型智能分块           │
                      │  · 表格块保持完整不切割          │
                      │  · 滑动窗口 + 上下文重叠         │
                      └──────────┬───────────────────┘
                                 │ Chunks
                                 ▼
                      ┌──────────────────────────────┐
                      │  BGE Embedding 向量化           │
                      │  · bge-large-zh-v1.5 (1024d)  │
                      │  · 本地推理，零 API 调用成本     │
                      └──────────┬───────────────────┘
                                 │ Vectors
                                 ▼
                      ┌──────────────────────────────┐
   ┌────  查询  ──────▶  ChromaDB 向量库               │
   │                  │  · 每文档独立 Collection         │
   │                  │  · MMR 多样性检索               │
   │                  │  · 元数据过滤 (block_type)      │
   │                  └──────────┬───────────────────┘
   │                             │ Top-K chunks
   │                             ▼
   │                  ┌──────────────────────────────┐
   │                  │  LLM 生成层                     │
   │                  │  · DeepSeek-V4 / 通义千问 / Kimi│
   │                  │  · 严格幻觉抑制                  │
   │                  │  · 答案溯源到原文                │
   └──  答案 + 来源  ◀─┴──────────────────────────────┘
```

## 核心特性

| 模块 | 技术选型 | 设计目标 |
|------|---------|---------|
| **文档解析** | Marker AI (surya 引擎) | 替代 PyPDFLoader，保留表格结构和图片信息 |
| **段落拆分** | 自定义规则分块器 | 按 Markdown 标题/表格边界拆分，表格块保持完整 |
| **文本向量化** | BGE-large-zh-v1.5 (1024d) | 中文语义理解最优，本地部署零带宽成本 |
| **向量存储** | ChromaDB → Milvus Lite | 每文档独立 Collection，支持增删隔离 |
| **检索策略** | MMR 多样性检索 | 解决 Top-K 结果内容重复问题 |
| **LLM 引擎** | DeepSeek-V4 / 通义千问 / Kimi | 多模型可切换，API 兼容 OpenAI 格式 |
| **幻觉抑制** | Prompt 工程 + 置信度阈值 | 无答案时不编造，显式标注不确定性 |

## 快速开始

### 环境要求

- Python 3.12+
- pip / uv 包管理器
- 至少 8GB 可用内存（首次运行需下载约 3.5GB 模型文件）

### 安装

```bash
# 克隆项目
git clone https://github.com/yourname/rag-project.git
cd rag-project

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 配置 API 密钥

在 `config/` 目录下创建 `.env` 文件：

```env
DASHSCOPE_API_KEY="your_key_here"    # 通义千问 (阿里云)
DEEPSEEK_API_KEY="your_key_here"    # DeepSeek (硅基流动)
KIMI_API_KEY="your_key_here"        # Kimi (月之暗面)
```

### 使用

```bash
# 1. 放入文档（PDF / TXT）
将文档放入 data/raw/ 目录

# 2. 配置允许加载的文档
编辑 config/settings.py 中的 ALLOW_DOC_NAMES

# 3. 解析文档并构建向量库
python core/vector_store_manager.py

# 4. 启动问答
python main.py
```

## 项目结构

```
rag-project/
├── config/                # 配置中心
│   ├── settings.py        # 全局参数（chunk_size, top_k, 模型选择）
│   └── .env               # API 密钥（不入库）
├── core/                  # 核心业务模块
│   └── vector_store_manager.py  # 多文档向量库管理器
├── utils/                 # 工具模块
│   ├── marker_parser.py   # Marker AI 文档解析器
│   └── document_loader.py # 文档预处理工具链
├── rag/                   # RAG 检索与生成
│   ├── base_rag.py        # 问答链路主逻辑
│   └── vector_store.py    # 向量库 CRUD 操作
├── data/                  # 数据目录
│   └── raw/               # 原始文档（不提交到 Git）
├── docs/                  # 学习笔记与开发日志
├── chroma_db/             # 本地向量库（自动生成）
├── main.py                # 项目入口
├── pyproject.toml         # 依赖配置
└── README.md
```

## 技术亮点

### 1. AI 驱动的文档解析

基于 **Marker** (surya 引擎) 替代传统 PyPDFLoader，解决三大痛点：

| 痛点 | PyPDFLoader | Marker |
|------|------------|--------|
| 表格结构 | 丢失为碎片文本 | 保留为 Markdown 表格 |
| 图片信息 | 完全忽略 | 自动提取并标注 |
| 中文排版 | 常出现乱序 | AI 布局分析，还原原文结构 |

### 2. 多文档向量库隔离

每份文档对应独立的 ChromaDB Collection，支持：
- 文档级别的增/删/改，不影响其他文档
- 按文档来源过滤检索范围
- 元数据驱动的分块策略（文本块 vs 表格块 vs 图片块）

### 3. 严格的幻觉抑制

```python
# 无相关文档时，LLM 强制输出固定应答
if not relevant_chunks:
    return "抱歉，当前文档中没有相关信息。请尝试换个问法。"
```

面试官会关心的：这不是简单的 Prompt 工程，而是**检索-生成链路的结构化安全约束**。

### 4. 模块化可扩展设计

- 解析器、分块器、向量库、LLM 层均为独立模块
- 通过 LangChain Document 标准对象串联各模块
- 新增文档格式只需扩展解析器，新增检索策略只需扩展向量库管理器

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.12.8 |
| RAG 框架 | LangChain | 1.3.1+ |
| 向量数据库 | ChromaDB | 0.x |
| Embedding | BGE-large-zh-v1.5 | 1.x |
| PDF 解析 | Marker (surya) | 1.10.2 |
| LLM | DeepSeek / 通义千问 / Kimi | API 兼容 |
| 包管理 | pip / uv | — |

## 开发路线

- [x] Day1-10: 基础 RAG 链路（文档加载 → 分块 → 向量化 → 检索 → 生成）
- [x] Day11-12: 项目结构重构 + 依赖规范化 + 多模型支持
- [x] Day13: Marker AI 解析器 + 多文档向量库隔离 + 规则分块器
- [ ] Day14-15: 批量导入脚本 + Chroma → Milvus Lite 迁移
- [ ] Day16-17: BGE-Reranker 重排序 + LLM-as-Scorer 语义评估
- [ ] Day18: 项目一阶段性收尾 + 完整测试

## License

MIT License — 详见 [LICENSE](LICENSE) 文件。
