```markdown
# 宫廷剧本RAG问答助手

一个基于LangChain 1.3.1和通义千问大模型的本地私有文档RAG问答系统，专门用于阅读和问答宫廷题材小说/剧本，支持自动识别【陛下】指代的皇帝人名，无答案时严格不编造，彻底杜绝模型幻觉。

## ✨ 功能特点
- ✅ 支持PDF和TXT格式文档批量导入
- ✅ 自动文本清洗、去重和语义分块
- ✅ 基于ChromaDB的本地向量存储，数据完全私有化
- ✅ MMR多样性检索，彻底解决检索结果重复问题
- ✅ 定制化提示词，自动识别【陛下】等身份指代
- ✅ 严格的幻觉抑制机制，无答案时固定回复
- ✅ 交互式命令行界面，自动显示参考来源
- ✅ 模块化代码结构，易于扩展和维护

## 🛠️ 环境要求
- Python 3.10+
- UV包管理器（比pip快10倍）
- 通义千问API密钥（免费额度足够个人使用）

## 🚀 快速开始
注：步骤 1-4 为首次运行需要配置，后续如果没有新增 / 修改文档，可直接执行步骤 6 的启动命令。
### 1. 克隆/下载项目
将项目下载到本地，进入项目根目录：
```bash
cd F:\rag-project
```

### 2. 创建并激活虚拟环境
```bash
# 创建虚拟环境
uv venv

# Windows 激活虚拟环境
.venv\Scripts\activate

# Mac/Linux 激活虚拟环境
source .venv/bin/activate
```

### 3. 安装所有依赖
```bash
uv sync
```

### 4. 配置 API 密钥
在`config`文件夹内新建`.env`文件，添加你的通义千问API密钥：
```env
DASHSCOPE_API_KEY="你的通义千问API密钥"
```

### 5. 导入你的文档
把需要阅读的PDF和TXT文档放入`data/raw`文件夹。

### 6. 运行项目
```bash
# 第一步：预处理文档（清洗+分块）
python utils/document_loader.py

# 第二步：创建本地向量库
python rag/vector_store.py

# 第三步：启动问答系统
python main.py
```

## 📁 项目目录结构
```
rag-project/
├── config/          # 配置文件目录
│   ├── .env         # API密钥配置（不提交到Git）
│   └── settings.py  # 全局参数配置
├── data/            # 数据目录
│   ├── raw/         # 原始文档（放入你要阅读的文件）
│   └── processed_documents.json  # 预处理后的结构化文档
├── docs/            # 学习笔记和文档目录
│   ├── learning_notes.md  # 每日学习笔记
│   └── error_log.md       # 报错记录与解决方案
├── rag/             # RAG核心代码目录
│   ├── base_rag.py  # 问答链路和交互式界面
│   └── vector_store.py  # 向量库创建、加载和检索
├── utils/           # 工具函数目录
│   └── document_loader.py  # 文档加载、清洗和分块
├── chroma_db/       # 本地向量数据库（自动生成）
├── .gitignore       # Git忽略文件配置
├── main.py          # 项目统一入口
├── pyproject.toml   # UV依赖配置文件
├── uv.lock          # 依赖版本锁定文件
└── README.md        # 项目说明文档
```

## 💡 使用技巧
1. 参数调优：回答不准确可修改`config/settings.py`，调整`CHUNK_SIZE`（500-800）和`RETRIEVER_TOP_K`（2-4）参数
2. 检索优化：检索结果重复时，将检索模式设置为`"mmr"`多样性检索
3. 更新文档：新增/替换文档后，重新执行`document_loader.py`和`vector_store.py`重建向量库
4. 提示词定制：修改`rag/base_rag.py`中的`get_prompt()`函数，自定义问答约束规则

## 📝 更新日志
v1.0（2026-05-16）：完成基础RAG链路，支持陛下身份指代识别，优化检索逻辑解决内容重复问题

## 📄 许可证
MIT License
```