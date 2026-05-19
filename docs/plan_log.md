
# Day1 Learning Notes｜项目环境搭建 + UV虚拟环境 + Git初始化
## 前置说明
适配系统：Windows 10 / Windows 11
项目固定路径：`F:\rag-project`
遵循原则：代码可直接复制粘贴、Bug卡滞即标记、不硬磕调试

## 一、今日核心目标
1. 搭建标准化 RAG 项目目录结构
2. 基于 UV 搭建独立 Python 虚拟开发环境，安装项目全部依赖
3. 配置通义千问 API 密钥并完成连通性测试
4. 唤醒基础 Python 文件操作语法，适配后续项目开发
5. 初始化 Git 版本控制，建立规范的代码管理习惯

## 二、核心基础原理复盘
### 1. 虚拟环境作用
虚拟环境是独立的开发沙盒，将本项目的 Python 依赖单独隔离存放，不会与电脑其他项目产生版本冲突，是专业Python项目的标准配置。
本次使用 `uv` 替代传统 `pip`，安装速度更快、依赖冲突更少。

### 2. API 密钥规范
敏感密钥禁止直接写入业务代码，统一存放于 `.env` 配置文件，配合 `.gitignore` 忽略提交，防止密钥泄露造成财产损失。

### 3. Git 版本控制作用
Git 相当于代码的「时光机」，可以记录每一次代码修改，写错代码可随时回退版本，是程序员必备的基础工具。

### 4. 标准化项目目录意义
规范的文件夹分类，让项目结构清晰，后续长期维护、他人阅读都能快速定位代码，是企业级开发的基础规范。

## 三、分步实操记录
### 1. 项目前置准备
1. 在F盘新建文件夹 `rag-project`
2. 使用VSCode**打开整个项目文件夹**，而非单个文件
3. 调出VSCode内置终端（`Ctrl + \`）

### 2. UV虚拟环境搭建与依赖安装
终端逐行执行命令：
```bash
# 初始化UV项目，自动生成依赖配置文件
uv init

# 创建独立虚拟环境
uv venv

# Windows PowerShell 激活虚拟环境
.venv\Scripts\activate

# 批量安装项目全部依赖库
uv add langchain langchain-community chromadb streamlit python-dotenv pypdf dashscope
```
#### 执行成功标准
1. `uv init`：生成 `pyproject.toml` 配置文件
2. `uv venv`：生成隐藏文件夹 `.venv`
3. 激活环境：终端前缀显示 `(.venv)`
4. 依赖安装：终端提示 `Successfully installed`，无红色报错

### 3. 配置环境变量文件
1. 新建文件夹 `config`
2. 在 `config` 中新建 `.env` 配置文件，写入密钥
```env
# config/.env
# 通义千问API密钥
DASHSCOPE_API_KEY="你的通义千问API密钥"
```

### 4. 通义千问 API 连通性测试
新建 `test_api.py` 测试脚本，验证环境与密钥有效性：
```python
# test_api.py 通义千问API连通性测试
from langchain_community.chat_models import ChatTongyi
import os
from dotenv import load_dotenv

# 加载配置文件中的环境变量
load_dotenv("config/.env")

# 初始化大模型，temperature=0保证回答严谨无随机编造
llm = ChatTongyi(model="qwen-turbo", temperature=0)

if __name__ == "__main__":
    response = llm.invoke("你好")
    print("API调用成功：", response.content)
```
运行命令：
```bash
python test_api.py
```
成功标准：终端输出 `API调用成功：你好`

### 5. Python基础语法脚本练习
#### 5.1 前置准备
新建 `data` 文件夹，内部创建 `test.txt` 写入测试文本。

#### 脚本1：本地文本文件读取
文件：`script1_read_file.py`
```python
# script1_read_file.py 基础文件读取操作
def read_txt_file(file_path):
    # with语句自动管理文件开关，避免资源泄漏
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    text = read_txt_file("data/test.txt")
    print("文件内容：\n", text)
```

#### 脚本2：文件夹遍历与文件信息获取
文件：`script2_scan_folder.py`
```python
# script2_scan_folder.py 遍历文件夹获取文件名称与大小
import os

def scan_folder(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            print(f"文件名：{file_name} | 大小：{file_size} 字节")

if __name__ == "__main__":
    scan_folder("data")
```

#### 脚本3：字符串多余空格清洗
文件：`script3_clean_space.py`
```python
# script3_clean_space.py 文本空格预处理基础操作
def clean_extra_spaces(text):
    # 去除首尾及中间连续多余空白字符
    return " ".join(text.split())

if __name__ == "__main__":
    raw_text = "  我  是  多  余  空  格  "
    print("清洗前：", raw_text)
    print("清洗后：", clean_extra_spaces(raw_text))
```

### 6. 标准化项目目录搭建
完整目录结构：
```
F:\rag-project/
├── config/          # 存放配置文件、环境密钥
├── data/            # 存放项目测试数据、文档
├── utils/           # 通用工具函数存放目录
├── rag/             # RAG核心业务代码目录
├── logs/            # 程序运行日志存储
├── docs/            # 学习笔记、报错记录文档
├── .venv/           # UV虚拟环境目录
├── .gitignore       # Git忽略配置文件
└── pyproject.toml   # UV依赖管理配置文件
```

### 7. Git 版本控制配置
#### 7.1 新建 `.gitignore` 文件
```plaintext
# 虚拟环境目录
.venv/
venv/
ENV/

# Python编译缓存文件
__pycache__/
*.pyc
*.pyo
*.pyd

# 敏感配置密钥
config/.env

# 向量数据库缓存
chroma_db/

# 日志文件
logs/
*.log

# 临时文件
*.tmp
*.temp
```

#### 7.2 Git 初始化提交
```bash
# 初始化本地Git仓库
git init

# 添加所有文件至暂存区
git add .

# 提交版本快照
git commit -m "项目初始化：环境配置+基础脚本完成"
```

### 8. 复盘归档配置
在 `docs` 文件夹新建 `error_log.md`，作为专属报错错题本：
```markdown
# 报错记录与解决方法
## Day1 报错记录
### 1. 报错名称：
- 错误提示：
- 原因：
- 解决方法：

### 2. 报错名称：
- 错误提示：
- 原因：
- 解决方法：
```

## 四、常见问题与标准化解决方案
1. **PowerShell 脚本执行策略报错**
   管理员身份运行PowerShell，执行：
   ```bash
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **网络超时、依赖安装失败**
   中断命令后重启终端，切换手机热点重新安装依赖。

3. **'uv' 不是内部或外部命令**
   先手动安装uv工具：`pip install uv`，再重新执行环境搭建命令。

4. **API 密钥调用失败**
   检查 `.env` 文件密钥是否存在多余空格、换行，确认密钥权限正常。

5. **中文文件读取乱码**
   所有文件读取代码强制添加 `encoding="utf-8"` 参数。

## 五、版本管理规范
1. 开发中所有报错统一记录至 `docs/error_log.md`
2. 每日完成任务后执行 Git 提交，留存代码版本快照
3. 禁止将包含密钥的文件提交至远程代码仓库

## 六、今日学习总结
1. 掌握专业Python项目的**虚拟环境搭建规范**，理解环境隔离的意义
2. 学会敏感配置密钥的安全管理方式，规避信息泄露风险
3. 夯实文件读取、文件夹遍历、字符串清洗三大基础Python语法，适配后续RAG项目开发
4. 建立标准化项目目录思维，养成企业级开发的代码规范
5. 入门Git版本控制，学会保存代码版本，防止代码修改出错无法回退

## 七、任务链路衔接
- **前置**：无，为本项目从零开始的基础搭建阶段
- **后置**：Day2 基于本日完整环境，开展 LangChain 文档加载、文本清洗预处理开发

## 八、最终交付物清单
- [x] 完整可用的 UV 虚拟开发环境
- [x] 通义千问 API 连通测试脚本 `test_api.py`
- [x] 标准化分层项目目录结构
- [x] 三份 Python 基础语法练习脚本
- [x] `.gitignore` 忽略配置文件
- [x] 本地 Git 初始化版本仓库
- [x] `docs/error_log.md` 报错记录模板文件

---------------------------------------------------------------------------------------------------

# Day2 Learning Notes
## 前置条件
完成Day1基础环境搭建：UV虚拟环境、标准化项目目录、Git初始化、基础Python脚本可用。
项目路径：`F:\rag-project`

## 核心目标
搭建RAG项目的数据输入层，实现**PDF/TXT文档自动读取、文本清洗、结构化持久化保存**，产出干净规范的数据集，为后续文本分块、向量入库打下基础。

## 核心基础原理
1. **RAG数据流转链路**
原始文档 → 机器读取解析 → 文本清洗降噪 → JSON结构化保存 → 文本分块 → 向量存储 → 智能问答
本日完成前四个环节，是整个RAG项目的底层数据基础。

2. **LangChain核心加载器**
- `TextLoader`：用于读取TXT纯文本文件，必须指定`utf-8`编码防止中文乱码
- `PyPDFLoader`：用于读取PDF文件，自动忽略图片、水印，仅提取文字内容

3. **Document标准对象**
LangChain统一的文档封装格式，后续所有RAG操作都基于该对象：
- `page_content`：存储文档纯文本内容
- `metadata`：存储文件路径、文件类型等溯源信息

## 分步实操记录
### 一、基础加载工具测试
1. 仅学习官方指定文档，不冗余学习无关内容
2. 新建测试脚本 `test_load.py`，快速验证文档读取能力
```python
# 导入文档加载工具
from langchain_community.document_loaders import PyPDFLoader, TextLoader

# 测试读取TXT文件
txt_path = "data/test.txt"
txt_loader = TextLoader(txt_path, encoding='utf-8')
txt_doc = txt_loader.load()[0]
print("=====TXT文档内容=====")
print(txt_doc.page_content)

# 测试读取PDF文件
pdf_path = "data/test.pdf"
pdf_loader = PyPDFLoader(pdf_path)
pdf_doc = pdf_loader.load()[0]
print("\n=====PDF文档内容=====")
print(pdf_doc.page_content)

# 查看Document对象元数据
print("\n=====文档元数据信息=====")
print("TXT文件信息：", txt_doc.metadata)
print("PDF文件信息：", pdf_doc.metadata)
```

### 二、通用文档解析脚本封装
新建工具文件 `utils/document_loader.py`，实现单文件读取+批量文件夹读取，代码全注释可直接复用：
```python
# 导入系统路径处理模块
import os
# 导入LangChain官方文档加载器
from langchain_community.document_loaders import PyPDFLoader, TextLoader
# 导入标准Document对象
from langchain_core.documents import Document

def load_single_document(file_path: str) -> Document:
    """
    读取单个文档，自动识别PDF/TXT格式
    :param file_path: 文档完整路径
    :return: 标准化Document对象
    """
    # 获取文件后缀并转为小写，避免大小写格式问题
    file_extension = os.path.splitext(file_path)[1].lower()

    # 处理PDF格式文件
    if file_extension == ".pdf":
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        # 合并PDF多页内容为完整文本
        combined_content = "\n".join([page.page_content for page in pages])
        return Document(page_content=combined_content, metadata={"source": file_path, "type": "pdf"})
    
    # 处理TXT格式文件，强制utf-8编码防止乱码
    elif file_extension == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
        return loader.load()[0]
    
    # 不支持的文件格式抛出提示
    else:
        raise ValueError(f"暂不支持该文件格式：{file_extension}")

def load_documents_from_folder(folder_path: str) -> list[Document]:
    """
    批量读取指定文件夹内所有PDF/TXT文档
    :param folder_path: 原始文档存放文件夹路径
    :return: 文档对象列表
    """
    documents = []
    # 遍历文件夹内所有文件
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        # 仅处理文件，跳过子文件夹
        if os.path.isfile(file_path):
            file_extension = os.path.splitext(file_name)[1].lower()
            # 只识别PDF和TXT格式
            if file_extension in [".pdf", ".txt"]:
                try:
                    doc = load_single_document(file_path)
                    documents.append(doc)
                    print(f"成功加载文件：{file_name}")
                except Exception as e:
                    print(f"文件加载失败 {file_name}：{e}")
    return documents
```

### 三、规范化数据目录搭建
1. 在`data`目录下新建 `raw` 文件夹，专门存放**原始未处理文档**
2. 放入三类测试文档：纯文本TXT、纯文字PDF、带简单图片的PDF
3. 规范：原始文档单独存放，避免预处理操作损坏源文件

### 四、文本清洗与数据预处理
在 `utils/document_loader.py` 追加文本清洗、短文档过滤、JSON保存功能：
```python
import re
import json

def clean_text(text: str) -> str:
    """文本清洗：去除多余换行、空格，规整文本格式"""
    text = re.sub(r'\n+', '\n', text)   # 合并连续换行
    text = re.sub(r'\s+', ' ', text)    # 压缩连续空格
    text = text.strip()                 # 去除首尾空白
    return text

def filter_short_documents(documents: list[Document], min_length: int = 50) -> list[Document]:
    """过滤无意义的短文本片段，保留有效语义文档"""
    return [doc for doc in documents if len(doc.page_content) >= min_length]

def save_documents_to_json(documents: list[Document], output_path: str):
    """将处理后的文档结构化保存为JSON文件，方便后续复用"""
    docs_json = []
    for doc in documents:
        docs_json.append({
            "page_content": doc.page_content,
            "metadata": doc.metadata
        })
    # 保存文件，保证中文正常显示
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docs_json, f, ensure_ascii=False, indent=2)

# 完整预处理执行入口
if __name__ == "__main__":
    # 读取原始文档
    raw_docs = load_documents_from_folder("data/raw")
    print(f"原始文档总数：{len(raw_docs)}")

    # 批量清洗文本
    cleaned_docs = []
    for doc in raw_docs:
        doc.page_content = clean_text(doc.page_content)
        cleaned_docs.append(doc)
    
    # 过滤无效短文档
    filtered_docs = filter_short_documents(cleaned_docs)
    print(f"清洗过滤后有效文档数：{len(filtered_docs)}")

    # 保存结构化数据集
    save_documents_to_json(filtered_docs, "data/processed_documents.json")
    print("文档预处理完成，已保存至 data/processed_documents.json")
```

## 常见问题与标准化解决方案
1. **PDF文档读取乱码**
   解决方案：执行命令升级依赖 `uv add pypdf --upgrade`

2. **提示找不到文件**
   原因：文件路径书写错误、文档存放位置不规范
   解决方案：统一将原始文档放入 `data/raw`，不自定义杂乱路径

3. **中文编码报错**
   解决方案：所有文本读取代码强制添加 `encoding="utf-8"`

4. **模块导入失败**
   原因：虚拟环境未激活
   解决方案：开发前确认终端前缀为 `(.venv)`

## 版本管理与复盘规范
1. 所有报错记录归档至 `docs/error_log.md`，记录报错原因与解决方法
2. 完成开发后执行Git提交，保存版本快照
```bash
git add .
git commit -m "Day2：完成文档批量读取+文本清洗预处理"
```

## 学习总结
1. 掌握LangChain标准的文档读取范式，理解RAG项目数据输入层的核心逻辑
2. 建立工程化思维：原始数据与处理后数据分层存放，保护源文件
3. 实现文档批量自动化处理，替代手动单文件测试，提升开发效率
4. 完成文本降噪清洗，保证输入大模型的文本干净无冗余噪声
5. 产出可复用工具函数，后续同类项目可以直接套用

## 任务衔接
- **前置依赖**：Day1 项目环境与目录结构
- **后续衔接**：Day3 将基于本日产出的 `processed_documents.json` 数据集，完成文本分块、ChromaDB向量库搭建、相似度检索功能

## 最终交付物清单
- [x] `utils/document_loader.py` 通用文档读取+文本清洗工具脚本
- [x] `data/raw` 标准化原始文档存储目录
- [x] `data/processed_documents.json` 结构化干净数据集
- [x] `docs/error_log.md` 问题报错归档记录
- [x] 本地Git版本提交完成

---------------------------------------------------------------------------------------------------

# Day3 RAG项目学习笔记｜文本分块 + ChromaDB向量库搭建（复盘版）
## 前置衔接
基于Day2成果：已完成本地PDF/TXT文档批量加载、文本清洗、无效内容过滤，最终产出规整的结构化文档文件 `data/processed_documents.json`。

## 核心学习目标
承接预处理后的规整文本，完成RAG两大核心关键能力：
1. 对长文档进行**语义级文本分块**，解决大模型上下文限制、检索不精准问题；
2. 实现文本向量化转换，搭建**本地ChromaDB向量库**；
3. 完成向量库相似性检索测试，实现问题与文档片段的精准匹配。

## 一、核心基础理论（新手必复盘）
### 1. 文本分块的必要性
1. 大模型存在**上下文长度上限**，完整长文档无法直接输入模型；
2. 全文输入会导致检索模糊，无法精准定位问题对应的关键内容；
3. 分块后仅推送相关片段给大模型，**降低调用成本、提升回答精准度**。

### 2. 中文最优分块工具
固定使用：`RecursiveCharacterTextSplitter`
核心优势：**递归语义分割**，优先按段落、句子、标点拆分，最大限度保证单块文本语义完整，避免语句截断。

### 3. 两大核心分块参数
1. `chunk_size`：单个文本块最大字符数
   - 中文最优区间：500–800
   - 过小：破坏完整语义；过大：检索精度下降
2. `chunk_overlap`：相邻文本块重叠字符数
   - 通用标准：`chunk_size 的 10%`
   - 作用：避免关键信息被切割在两块边界，杜绝断章取义

## 二、完整实操流程（无时间线·标准化步骤）
### 步骤1：多组参数调试，确定最优分块配置
1. 新建测试文件 `test_chunk.py`，搭建参数对比测试代码；
2. 基于Day2清洗后的真实文档，测试三组标准参数：
   - 小组：`(500, 50)`
   - 标准组：`(800, 80)`
   - 大组：`(1000, 100)`
3. 筛选标准：**语句完整、无截断、分块粒度均匀**，记录最优参数，全局统一使用。

### 步骤2：搭建全局统一配置文件
新建 `config/settings.py`，集中管理所有项目参数（规范化项目结构）：
- 密钥配置：通义千问API密钥
- 模型配置：LLM模型、嵌入模型、生成温度
- 分块配置：写入调试后的最优`chunk_size`、`chunk_overlap`
- 向量库配置：本地存储路径、集合名称
- 检索配置：默认返回最优匹配片段数量`top_k`

### 步骤3：开发向量库核心脚本
新建 `rag/vector_store.py`，封装四大核心能力，实现模块化复用：
1. 加载模块：读取Day2输出的`processed_documents.json`结构化文档；
2. 分块模块：调用最优参数完成语义分块；
3. 建库模块：文本向量化 + 本地ChromaDB持久化存储；
4. 加载模块：支持重启项目后直接读取本地向量库，无需重复预处理。

### 步骤4：向量库初始化验证
1. 执行脚本创建本地向量库；
2. 校验标准：项目根目录生成`chroma_db`文件夹，终端正常输出文档总数、分块后片段总数，无报错。

### 步骤5：相似性检索功能开发与测试
1. 新增相似度查询函数，支持**带分数精准检索**；
2. 设计多场景测试query：通用提问、细节提问、宽泛提问；
3. 校验标准：
   - 成功返回对应文档片段；
   - 相似度分数区间0–1，**分数越低，匹配度越高**；
   - 检索结果与提问语义高度契合。

### 步骤6：向量库持久性验证
1. 关闭项目、重启VSCode、重新激活虚拟环境；
2. 直接加载本地向量库执行检索；
3. 校验标准：无需重新分块、建库，检索结果与首次一致。

## 三、项目规范化操作
1. 所有硬编码参数全部迁移至`settings.py`，统一管理、方便迭代；
2. 所有函数添加标准注释，明确入参、出参、核心作用；
3. 每日迭代完成后执行Git提交，留存版本记录。

## 四、高频Bug复盘&固定解决方案
1. **Embeddings API调用失败**
   - 原因：密钥错误、密钥含空格、账号无免费额度
   - 方案：核对`config/.env`密钥、清除首尾空格
2. **向量库加载失败/报错**
   - 原因：旧向量库参数与新参数不匹配
   - 方案：直接删除`chroma_db`文件夹，重新执行建库脚本
3. **分块语义破碎、截断严重**
   - 原因：`chunk_size`过小、分割规则不合理
   - 方案：调大单块字符数，保留中文专属分割符

## 五、今日核心学习收获
1. 掌握RAG核心逻辑：**文档预处理 → 语义分块 → 向量化存储 → 相似度检索**；
2. 理解向量库本质：将文本转化为机器可识别的数字向量，实现毫秒级语义匹配；
3. 建立项目规范化思维：全局配置统一管理、功能模块化封装、数据分层存储；
4. 区分普通大模型问答与RAG问答的核心差异：RAG可基于**私有本地文档**精准作答，无知识幻觉。

## 六、最终交付物清单（GitHub归档核对）
- `config/settings.py`：项目全局统一参数配置文件
- `rag/vector_store.py`：完整向量库创建、加载、检索模块化脚本
- `chroma_db/`：本地持久化向量数据库文件
- `docs/learning_notes.md`：分块参数对比、检索效果复盘记录
- `docs/error_log.md`：当日问题汇总与解决方案记录
- 完整Git版本提交记录
---------------------------------------------------------------------------------------------------
# Day4 RAG项目学习笔记｜LCEL标准RAG链路搭建 + 交互式问答开发（复盘版）
## 前置衔接
基于Day3成果：已完成长文档语义分块、文本向量化处理、本地ChromaDB向量库搭建，实现私有文档相似度精准检索，向量库可持久化加载复用。

## 核心学习目标
承接已建好的向量检索能力，完成RAG上层问答业务开发，落地完整问答闭环：
1. 吃透LangChain新版**LCEL管道链式语法**，搭建行业标准RAG执行流程；
2. 封装大模型调用、自定义提示词、问答执行三大核心功能模块；
3. 开发命令行交互式问答程序，实现用户提问、AI作答、原文来源溯源全套功能；
4. 修复版本兼容、代码逻辑类运行报错，保证项目无BUG稳定运行；
5. 通过提示词添加约束规则，初步限制模型自由发挥，规避无效编造回答。

## 一、核心基础理论（新手必复盘）
### 1. LCEL链式语法核心规则
1. 管道符`|`为LangChain专属流转符号，代表**上游输出作为下游输入**，串行执行流程；
2. 支持代码跨行拆分编写，仅为排版优化，不改变执行逻辑，单行写法同样合法；
3. 整体链路可直接赋值为链对象，统一通过`.invoke()`方法调用执行。

### 2. 标准RAG四步执行链路
1. 检索阶段：通过检索器从向量库召回Top-K高相似度文档片段；
2. 组装阶段：拼接文档上下文+透传用户原始问题，填充模板占位符；
3. 推理阶段：传入大模型，依据上下文与规则生成对应回答；
4. 解析阶段：剥离模型原生封装结构，输出纯净文本答案。

### 3. 两种检索调用区分
1. 独立调用`retriever.invoke(question)`：仅召回文档，用于展示参考来源；
2. 链内内置检索：跟随问答链路自动执行，专供大模型读取上下文使用；
3. 工程规范：全程共用**同一个检索器实例**，保证展示内容与模型阅读内容完全一致。

### 4. 提示词约束作用
1. 统一规定无标准答案时固定回复话术，从文本层面抑制模型幻觉；
2. 尝试添加身份指代映射规则，引导模型识别文中人物身份关系；
3. 设置回答简洁化要求，精简输出内容，剔除多余废话。

## 二、完整实操流程（无时间线·标准化步骤）
### 步骤1：项目文件创建与依赖导入
1. 在`rag`目录新建核心业务文件`base_rag.py`，作为问答系统唯一入口；
2. 批量导入LCEL所需核心组件、通义千问聊天模型、向量库加载函数；
3. 读取全局统一配置`settings.py`，统一调用模型参数、API密钥、检索数量。

### 步骤2：封装大模型初始化函数
1. 编写`get_llm()`独立函数，集中管理模型名称、温度系数、密钥传参；
2. 固定低温度参数，强化模型严谨性，减少自由创作倾向；
3. 实现解耦设计，后续更换模型仅需修改此函数，不改动问答主流程。

### 步骤3：编写自定义约束提示词模板
1. 编写`get_prompt()`函数，构建带双占位符`{context}`、`{question}`的提示文本；
2. 写入业务规则：限定陛下与皇帝身份关联、明确无答案统一回复语句；
3. 通过`PromptTemplate.from_template()`生成可自动填充的模板对象。

### 步骤4：搭建标准LCEL问答主链
1. 调用全局方法加载本地已建好的Chroma向量库；
2. 初始化检索器，读取配置文件中`RETRIEVER_TOP_K`设定召回片段数量；
3. 定义简易文档拼接函数，完成多文档内容合并整合；
4. 按照标准格式组装RAG全链路，实现检索、填模板、调模型、结果解析一体化；
5. 函数统一返回**问答链+检索器**双对象，满足答题与溯源双重需求。

### 步骤5：开发交互式问答主程序
1. 封装`interactive_qa()`循环问答逻辑；
2. 实现输入监听、退出指令识别、问答结果打印功能；
3. 遍历召回文档，格式化输出文档路径与内容片段，完成来源溯源展示；
4. 规范终端输出排版，区分答案区与参考来源区，提升交互观感。

### 步骤6：修复版本兼容致命报错
1. 排查新版Chroma库变动，删除已废弃`persist()`持久化代码，消除属性不存在报错；
2. 重构代码逻辑，废除多处重复加载向量库写法，统一全局检索实例；
3. 全流程试运行，排查模块导入、参数传参、路径读取等基础错误。

### 步骤7：多场景功能实测验证
1. 输入无关类问题，检验模型是否严格遵守规则，拒绝编造答案；
2. 输入常规文档相关问题，验证检索与作答联动是否正常；
3. 输入身份指代类问题，测试提示词引导效果，记录实际作答表现。

## 三、项目规范化操作
1. 所有模型参数、检索参数、密钥信息全部存放配置文件，杜绝硬编码；
2. 所有功能独立拆分封装函数，单一函数仅负责单一业务逻辑；
3. 代码添加功能注释，标注函数作用、调用逻辑，方便后期迭代修改；
4. 每日开发完成后提交Git版本，留存当前稳定版本代码。

## 四、高频Bug复盘&固定解决方案
1. **Chroma库提示无persist属性**
   - 原因：新版向量库取消手动持久化方法，默认自动保存本地
   - 方案：直接删除`vector_store.persist()`一行代码即可
2. **前端展示文档与模型读取内容不一致**
   - 原因：代码内创建两个独立检索器，分别用于溯源和答题
   - 方案：全局仅初始化一个检索器，全程共用同一实例
3. **导入模块路径报错**
   - 原因：未在项目根目录运行启动命令
   - 方案：固定根目录启动，使用`python -m rag.base_rag`模块化运行

## 五、今日核心学习收获
1. 完全掌握LangChain最新LCEL开发范式，理清整条RAG数据流转顺序；
2. 分清独立检索调用与链式内置检索的使用场景，解决行业常见数据错位问题；
3. 熟练完成大模型封装、提示词定制、交互式程序开发整套上层业务；
4. 具备版本适配排错能力，能够快速识别第三方库更新带来的语法变动；
5. 建立完整RAG项目分层思想：底层向量检索→中层链路组装→上层交互应用。

## 六、现存未解决问题（明日重点攻坚）
1. 身份指代识别未生效，文档明确存在陛下与对应皇帝人名，模型无法自动关联匹配；
2. 检索返回结果存在大量重复文本片段，冗余内容干扰模型提取核心信息；
3. 仅依靠文字提示词引导力度不足，语义推理类问答准确率极低；
4. 文档拼接未做去重处理，上下文内容臃肿，增加模型识别负担。

## 七、明日优化迭代方向
1. 升级文档格式化函数，新增文本去重逻辑，过滤重复检索片段；
2. 高强度优化提示词，细化人物身份判定细则，强制绑定身份对应关系；
3. 精简输入上下文内容，过滤无效语句，提升模型抓取关键信息效率；
4. 大批量身份类问句专项测试，调试至指代识别功能正常生效；
5. 优化终端交互输出格式，精简无用展示内容。

## 八、最终交付物清单（GitHub归档核对）
- `rag/base_rag.py`：完整LCEL标准RAG链路 + 交互式问答主程序
- 已优化统一检索器逻辑，修复全部运行级报错
- 完善自定义约束型Prompt模板代码
- `docs/learning_notes.md`：今日链路开发与语法学习复盘记录
- `docs/error_log.md`：Chroma版本报错、双检索器问题解决记录
- 当日稳定版本Git提交记录


