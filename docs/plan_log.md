
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

#批量安装项目全部依赖库
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

# Day5 RAG项目学习笔记｜RAG检索策略优化+项目工程化重构+全项目规整复盘版
## 前置衔接
基于Day4成果：已搭建LCEL标准RAG问答全链路，实现交互式命令行问答、答案生成、参考来源溯源全套功能，修复库版本兼容、重复加载向量库等运行级报错，基础问答业务流程完全跑通。

## 核心学习目标
在成熟可用RAG系统基础上，完成项目优化与工程化规整，夯实第一周收尾工作：
1. 掌握**MMR多样性检索**原理与实操配置，对比相似度检索优劣，选定最优检索策略；
2. 完成项目代码全局模块化重构，实现配置、工具、核心业务彻底解耦；
3. 搭建项目统一全局入口，简化项目启动方式，降低使用门槛；
4. 清理项目冗余文件与废弃测试代码，统一代码注释规范，提升项目可读性；
5. 编写完整项目使用文档，完善项目部署、运行、使用全流程说明；
6. 批量实测多类型问答场景，优化基础作答效果，汇总场景化使用问题；
7. 完成第一周代码阶段性归档，规范Git版本管理，稳定封存可用版本。

## 一、核心基础理论（优化复盘）
### 1. 两种主流检索策略核心区别
1. 相似度检索：仅依据语义分值排序，优先召回和问句最贴近的文本片段，易出现内容高度重复，信息覆盖面窄；
2. MMR最大边际相关性检索：兼顾**语义相似度+内容多样性**，在保证匹配度前提下，筛选差异化文本，有效减少重复片段，丰富回答信息维度；
3. 参数核心作用：`lambda_mult`控制相似度权重，越趋近1越偏向精准匹配，越趋近0越侧重内容多样。

### 2. 检索名额抢占核心逻辑
1. 设定固定Top-K返回数量时，向量库内所有文档平等参与召回；
2. 无关文档会优先占据检索名额，导致核心剧情文档片段无法正常召回，直接降低问答准确率；
3. 事后文档过滤仅能剔除展示与上下文内容，无法改变前期名额分配问题，属于治标不治本。

### 3. 项目工程化分层设计思想
1. 配置层：集中存放所有模型、向量库、检索、路径全局参数，杜绝代码内硬编码；
2. 工具层：封装文档加载、文本清洗、文件操作通用工具，实现功能复用；
3. 核心业务层：独立存放向量库管理、RAG问答链路核心逻辑；
4. 应用入口层：统一启动入口，屏蔽底层代码细节，使用者一键启动即可运行。

### 4. 交互式问答输出规范
1. 区分答案正文与参考来源展示区域，统一终端输出排版格式；
2. 过滤无效参考文档展示内容，精简溯源信息，提升交互体验；
3. 统一无答案场景固定回复话术，严格遵循提示词约束，杜绝模型自由编造。

## 二、完整实操流程（标准化优化步骤）
### 步骤1：检索策略切换与参数调优
1. 修改检索器配置，将默认相似度检索替换为MMR检索模式，保留原有检索架构不变；
2. 调试`fetch_k`候选召回数量与`lambda_mult`权重参数，适配中文宫廷剧本文本场景；
3. 固定最优Top-K召回数量，写入全局配置文件，统一全项目检索参数。

### 步骤2：全局配置统一收拢管控
1. 核对项目内所有散落参数，全部迁移至`config/settings.py`统一管理；
2. 拆分API配置、模型配置、分块配置、向量库配置、检索配置五大模块，分类清晰；
3. 优化环境变量读取逻辑，统一密钥调用方式，提升项目安全性。

### 步骤3：全项目代码模块化重构
1. 拆分冗余耦合代码，严格遵循单一职责原则拆分函数；
2. 统一全局向量库、检索器实例创建逻辑，全程共用同一实例，杜绝溯源与答题内容错位；
3. 优化文档拼接格式化函数，完善短文本过滤、基础内容清洗逻辑。

### 步骤4：新增项目全局统一入口
1. 在项目根目录创建`main.py`主启动文件，整合交互式问答启动逻辑；
2. 简化启动命令，仅需执行根目录启动脚本即可运行整套问答系统；
3. 美化启动页文字提示，完善程序使用说明，优化用户使用体验。

### 步骤5：项目冗余内容清理规整
1. 删除前期测试用临时脚本、无用调试代码、废弃临时数据文件；
2. 梳理项目文件夹层级，严格遵循既定目录结构，保证目录整洁统一；
3. 全项目批量补全标准函数注释、业务逻辑注释，标注核心代码作用与使用场景。

### 步骤6：编写项目完整README说明文档
1. 梳理项目整体介绍、核心功能特点，清晰说明项目应用场景；
2. 分步撰写环境搭建、依赖安装、密钥配置、数据导入、项目启动全流程教程；
3. 完善项目目录结构说明、项目许可证标注，满足开源项目基础规范。

### 步骤7：多场景批量实测与效果记录
1. 批量测试基础问答、无答案问答、人物身份问答、逻辑推理问答四大场景；
2. 记录不同问句下MMR检索的作答表现，对比原检索模式的优劣差异；
3. 汇总问答出错场景、作答偏差问题，分类整理留存优化依据。

### 步骤8：第一周代码版本归档封存
1. 核对本周所有开发成果，确认基础功能无运行级BUG；
2. 规范提交Git本地仓库，填写清晰版本提交备注，封存第一周稳定可用版本；
3. 整理本周报错日志、学习笔记，统一归档至docs文档目录。

## 三、项目规范化升级要点
1. 全项目禁止明文密钥、固定路径、固定参数硬编码，所有可变内容统一配置化；
2. 通用工具函数全部封装复用，减少重复代码编写，提升后期迭代效率；
3. 严格区分开发调试代码与线上正式运行代码，正式版本剔除所有调试打印语句；
4. 建立项目迭代规范，优化功能优先整合进正式代码，临时调试逻辑单独存放。

## 四、今日新增高频Bug复盘&固定解决方案
1. **无关文档抢占检索名额，核心内容召回不足**
   - 现象：Top-K结果大量混入测试文档，剧情关键片段无法被检索到
   - 临时方案：在文档格式化阶段过滤非目标文档，剔除无效上下文内容
   - 根治方案：延后至下周实现检索源头元数据精准过滤

2. **同含义不同问句，回答结果不一致**
   - 现象：直白身份提问可正常作答，衍生句式提问出现答案错乱、识别失败
   - 原因：仅依靠提示词语义引导力度不足，缺少实体关系强制绑定
   - 临时方案：固定标准提问句式保证正确率，下周升级实体映射逻辑

3. **MMR检索出现少量有效信息缺失**
   - 现象：过度偏向多样性后，丢失部分精准匹配核心语句
   - 解决方案：调高`lambda_mult`相似度权重，平衡精准度与多样性

4. **终端参考来源展示杂乱冗余**
   - 现象：溯源内容过长、无关文档同步展示，观感较差
   - 解决方案：截取内容片段精简展示，前端展示层过滤无关文档来源

## 五、今日核心学习收获
1. 熟练掌握LangChain双检索策略使用场景与参数调优技巧，可根据业务场景灵活切换；
2. 建立完整Python后端项目工程化思维，掌握中小型AI项目分层架构搭建方法；
3. 学会项目标准化文档编写、版本管理、代码规整整套开源项目基础流程；
4. 深刻理解检索层名额分配、后置过滤的利弊，明确RAG优化优先级顺序；
5. 完成第一周全流程技术闭环，从环境搭建→数据预处理→向量入库→问答链路→项目规整全流程完整落地；
6. 能够独立排查检索策略引发的问答偏差问题，具备基础RAG效果调优能力。

## 六、现存未解决遗留问题（顺延第二周攻坚）
1. 人物身份指代联动识别不稳定，陛下、皇帝、本名、帝号无法全自动互通推理；
2. 检索源头无法彻底屏蔽无关测试文档，仅能依靠后置过滤，占用检索资源；
3. 检索结果重复文本片段未彻底清理，冗余上下文加重模型识别负担；
4. 复杂语义推理类问题作答准确率偏低，仅靠基础RAG架构无法满足深度问答需求；
5. 暂无自动化测试脚本，问答正确率仅依靠人工逐条测试，效率较低。

## 七、下周开篇优先迭代优化方向
1. 完善文档去重逻辑，优化上下文拼接格式，精简送入大模型的文本内容；
2. 强化提示词人物实体强制绑定规则，打通所有称谓双向识别逻辑；
3. 研究向量库元数据过滤语法，实现检索源头直接筛选目标文档；
4. 入门学习查询重写进阶优化方案，解决口语化问句识别偏差问题；
5. 搭建简易问答自动化测试用例，批量统计问答正确率，量化优化效果。

## 八、今日最终交付物清单（GitHub归档核对）
- 优化后`rag/base_rag.py`：切换MMR检索+优化问答交互逻辑完整代码
- `main.py`：项目全局统一启动入口文件
- 完整规整版`README.md`：项目部署使用全套说明文档
- 全项目清理完毕冗余代码，统一标准函数注释
- `docs/learning_notes.md`：本周RAG全流程学习汇总笔记
- `docs/error_log.md`：本周所有运行报错、检索优化问题解决方案汇总
- 第一周最终稳定版Git本地提交记录
- 全局统一化`config/settings.py`项目配置文件

# Day6 Learning Notes
## 前置条件
完成Day1-Day5核心功能开发：纯本地RAG链路跑通、MMR多样性检索实现、文档去重逻辑生效、交互式问答界面可用。
项目路径：`F:\rag-project`
GitHub仓库：https://github.com/ADONIS686/rag-project.git

## 核心目标
解决第一周遗留的基础环境与数据纯净度问题，实现文档白名单过滤与全自动向量库更新机制，优化人物指代消解准确率，预习查询重写核心概念，完成第一周收尾，为Day7查询重写功能落地打下坚实基础。

## 核心基础原理
1. **文档白名单过滤原理**
通过配置文件统一管理允许访问的文档列表，在检索后对返回的文档片段进行元数据校验，只保留白名单内的文档内容，彻底杜绝无关文档干扰问答结果。

2. **全自动向量库更新机制**
将文档预处理、清洗、分块、旧库删除、新库创建全流程自动化，运行`create_vector_store()`即可一键完成所有步骤，无需手动执行多个脚本，避免人为操作失误导致的数据不一致。

3. **动态指代消解原理**
无需硬编码人物绑定关系，通过上下文同场出现的称谓与人名自动建立指代映射，是RAG系统通用的身份识别方案，适用于任意文本内容。

4. **检索参数对效果的影响**
- `k`：最终返回给大模型的文档片段数量，数量过少会导致上下文不完整，无法支撑逻辑推导
- `lambda_mult`：MMR检索的相似度权重，值越高越偏向精准匹配，越低越偏向内容多样性

5. **any()与all()函数区别**
- `any()`：满足任意一个条件即返回True，适用于白名单放行逻辑
- `all()`：必须满足所有条件才返回True，不适用于文档白名单筛选

6. **查询重写基础概念**
将用户口语化、模糊化、指代不明的问句，改写成清晰、精准、适合向量检索的标准问句，是提升RAG检索准确率的低成本高收益手段。

## 分步实操记录
### 一、基础环境问题收尾
1. 修复GitHub远程地址配置错误，解决同步失败问题
2. 清理`data/raw`文件夹内所有测试文档，仅保留核心文档`wenben1.pdf`
3. 删除旧向量库文件夹`chroma_db`，为重建纯净向量库做准备
4. 完善`.gitignore`配置，屏蔽API密钥、原始文档、向量库、临时文件等隐私与自动生成内容

### 二、文档白名单功能实现
1. 在`config/settings.py`中新增全局白名单配置：
```python
# 文档白名单：只允许这些文件参与问答
ALLOW_DOC_NAMES = ["wenben1.pdf"]
```
2. 在`rag/base_rag.py`的`format_docs()`函数中添加白名单过滤逻辑：
```python
valid_docs = [
    doc
    for doc in docs 
    # 过滤条件：长度>20 + 仅目标文档
    if len(doc.page_content.strip()) > 20 
    and any(allow_name in doc.metadata["source"] for allow_name in ALLOW_DOC_NAMES)
]
```
3. 在交互式问答的参考来源展示处同步添加白名单过滤，确保前端展示与大模型输入一致

### 三、全自动向量库更新机制升级
1. 修改`rag/vector_store.py`的`create_vector_store()`函数，改为无参调用
2. 新增全套自动预处理逻辑：自动加载文档、清洗文本、过滤短文本、生成结构化JSON
3. 新增自动删旧库逻辑：创建新库前自动删除旧的`chroma_db`文件夹，避免旧数据残留
4. 实现一键更新：运行`python rag/vector_store.py`即可完成从原始文档到向量库的全流程更新

### 四、人物指代消解优化
1. 定位问题根源：初始检索`k=3`召回上下文不足，原始提示词仅识别直白定义句
2. 优化提示词指代规则，放宽判定逻辑：允许通过上下文同场出现关系绑定称谓与人名
3. 调整检索参数，将`k`值从3改为5，提升上下文召回量
4. 保留动态指代特性，不硬编码任何人物绑定关系，保证系统通用性

### 五、专项功能测试
1. 设计10个覆盖不同宫廷称谓的测试用例
2. 逐个测试问答效果，记录每个问题的回答结果与参考来源
3. 验证白名单过滤效果：确认所有参考来源仅显示`wenben1.pdf`
4. 验证自动更新功能：修改原始文档后重新建库，问答结果同步更新
5. 验证无答案场景的表现：原文未记载内容严格如实回复，不编造信息

### 六、日志归档与版本提交
1. 将今日核心报错与解决方法归档至`docs/error_log.md`
2. 记录测试结果与优化过程至`docs/plan_log.md`
3. 提交所有修改并推送到GitHub远程仓库

## 常见问题与标准化解决方案
1. **宫廷称谓指代消解失败**
   - 错误提示：询问陛下、当朝皇帝、启明帝身份时，回复「文档中没有明确说明」
   - 原因：检索召回数量不足，提示词指代规则过于严格
   - 解决方案：将检索`k`值调整为5，优化提示词规则，支持上下文同场出现判定

2. **ChromaDB检索端filter过滤失效**
   - 错误提示：使用`"filter": {"source": {"$contains": "wenben1.pdf"}}`查询结果为空
   - 原因：本地ChromaDB版本不支持`$contains`元数据运算符
   - 解决方案：彻底放弃检索层filter，全程使用Python后置代码过滤文档

3. **无关文档干扰问答结果**
   - 错误提示：参考来源列表出现已删除的test.pdf文档
   - 原因：旧向量库残留数据，未实现白名单过滤
   - 解决方案：删除旧向量库重建，添加全局文档白名单过滤逻辑

## 版本管理与复盘规范
1. 所有测试数据与问答结果归档至`docs/record_notes.md`
2. 所有报错与解决方法统一记录在`docs/error_log.md`
3. 完成当日开发后执行Git提交，保存版本快照
```bash
git add .
git commit -m "Day6：解决GitHub同步+实现文档白名单+全自动向量库更新+优化人物指代+查询重写预习"
git push
```

## 学习总结
1. 掌握了文档白名单过滤的实现方法，彻底解决了无关文档干扰问题
2. 实现了全自动向量库更新机制，大幅提升了开发效率和数据一致性
3. 理解了动态指代消解的核心逻辑，掌握了不硬编码的通用身份识别方案
4. 学会了通过调整检索参数优化RAG问答效果，明确了`k`值与`lambda_mult`的作用
5. 掌握了查询重写的基础概念与应用场景，为明日功能落地做好准备
6. 理清了Python后置过滤与Chroma检索层filter的区别，避免了常见的兼容性坑
7. 区分了`any()`与`all()`函数的用法，掌握了白名单过滤的正确写法
8. 建立了"先解决基础问题，再优化上层功能"的开发思路，保证系统稳定性

## 任务衔接
- **前置依赖**：Day5 完成MMR检索、文档去重与基础RAG链路
- **后续衔接**：Day7 将基于今日优化后的基础RAG系统，实现查询重写功能，进一步提升模糊问句的回答准确率

## 最终交付物清单
- [x] 纯净的`wenben1.pdf`专属向量库
- [x] 完善后的`.gitignore`配置文件
- [x] 全局文档白名单功能实现
- [x] 全自动向量库更新机制
- [x] 优化后的人物指代消解提示词
- [x] 10个指代问题的专项测试记录
- [x] 更新后的`docs/error_log.md`与`docs/plan_log.md`
- [x] 本地Git提交与GitHub远程同步完成


# GitHub 开发日志：Day7 - RAG查询重写功能落地集成
## 核心目标：将查询重写模块集成至RAG问答链路，自动优化模糊问句，解决指代不明问题，提升问答准确率

---

### 一、今日实际完成工作（100%遵循开发计划执行）
1. **查询重写 Prompt 模板设计**
   - 编写宫廷剧本专属 `QUERY_REWRITE_PROMPT`，定义标准化改写规则、指代替换逻辑、固定称谓转换
   - 配置改写示例，实现口语化问句转书面检索问句的基础能力
2. **查询重写函数开发与测试**
   - 完成 `rewrite_query` 核心函数编写，搭建提示词→大模型→字符串输出的改写链路
   - 完成单元测试，验证基础问句改写功能正常运行
3. **RAG 主链路集成改造**
   - 重构 `get_rag_chain()` 函数，通过 `RunnablePassthrough.assign` 将查询重写接入主流程
   - 实现完整自动化流程：用户问句 → 查询重写 → MMR向量检索 → 大模型答案生成
   - 配置检索器参数，优化文本召回效果
   - 清理测试代码，恢复程序主入口，完成全流程联调
4. **批量测试与问题归档**
   - 完成 20 道问答测试用例全量执行，记录测试结果
   - 编写 `error_log.md` 文档，归档代码报错、业务问题、根因分析
5. **开发文档归档**
   - 更新开发日志、测试报告，完成代码规范化整理

---

### 二、今日学习收获
1. 掌握 **RAG 查询重写** 核心原理与应用价值，理解模糊问句优化的必要性
2. 熟练使用 LangChain LCEL 表达式构建链式调用，掌握 `RunnablePassthrough.assign` 用法
3. 学会排查 LangChain 链路拼接、Python 类型错误等常见报错
4. 理解 MMR 向量检索参数配置逻辑，提升文档召回效果
5. 掌握大模型提示词工程基础，通过规则+示例约束模型输出格式
---

### 三、遇到的问题及已解决方案
1. **管道符类型错误（已修复）**
   - 报错：`TypeError: unsupported operand type(s) for |: 'list' and 'function'`
   - 原因：在 lambda 中调用 `invoke` 返回文档列表，错误使用 LCEL 管道符连接函数
   - 解决：改为标准 Python 函数调用，规范链路写法
2. **查询重写函数传参异常（已修复）**
   - 原因：函数定义接收字符串，实际传入完整字典数据
   - 解决：重构函数入参，从字典中正确提取原始问题字段
3. **模型无约束违规改写（已优化）**
   - 解决：在 Prompt 中新增禁止规则，约束模型不私自增删问题内容

---

### 四、现存待优化问题（明日继续处理）
1. 查询重写稳定性不足：模型仍会私自添加限定词、替换问题主体
2. 20 题测试准确率 70%，未达到 ≥85% 的验收目标
3. 部分问答信息不完整，向量检索存在时序内容断层
4. 模型幻觉、皇后/妃嫔身份分类错误问题待修复

---

### 五、提交文件清单
- `rag/base_rag.py`：查询重写功能、RAG 链路重构、函数优化
- `docs/error_log.md`：当日报错与问题记录
- `docs/record_notes.md`：20 道测试用例结果报告
- `docs/plan_log.md`：开发计划与复盘记录

---

### 六、Git 提交信息
```bash
git add .
git commit -m "Day7：完成RAG查询重写功能集成，实现问句自动优化与全流程调试，完成批量测试与问题归档"
git push
```
# Day8 开发日志 | RAG问答系统优化 
**核心目标**：深度优化查询重写，落地自我纠正功能，将整体准确率提升至85%以上

---

## 一、今日完成事项
1. **完成查询重写Prompt终极优化**，采用"正向强制规则+精准错误反例"的形式，彻底解决历史违规改写问题
2. **落地自我纠正双链路架构**，新增答案生成子链与自我校验子链，构建"生成-验证"双层质检体系
3. **完成20道历史测试题全量回归测试**，验证优化效果，统计当前系统准确率
4. **定位并记录两个隐蔽的链路设计缺陷**，完成根因分析与初步修复方案设计
5. **更新error_log.md**，按统一格式归档今日所有问题与解决方案

---

## 二、今日学习收获
1. **大模型提示词工程核心技巧**
   - 理解了"正向规则优于否定规则，具体反例优于笼统描述"的原则
   - 掌握了通过错误示例约束大模型行为的方法，大幅提升查询重写的准确率
2. **RAG多阶段生成架构**
   - 学习了"生成-验证"范式的核心逻辑：先用一个模型生成答案，再用另一个模型校验修正
   - 理解了自我纠正功能如何有效降低大模型幻觉率，提升答案可靠性
3. **LangChain LCEL链路设计**
   - 掌握了RunnablePassthrough.assign的用法，实现链路中间结果的透传与追加
   - 学会了将复杂RAG流程拆分为多个独立子链，便于调试和维护
4. **检索一致性问题**
   - 认识到MMR多样性检索的随机性：相同query多次调用会返回不同结果
   - 理解了"检索结果复用"的重要性，不仅提升性能，更保证调试信息的一致性

---

## 三、今日遇到的问题
1. **查询重写违规篡改问题**
   - 现象：模型私自添加限定词、替换问题主体，如"母后→生母"、"皇后整顿宫规→燕光逸整顿宫规"
   - 影响：检索匹配失败，大量问题回答"文档中没有找到相关信息"
2. **自我纠正链路集成问题**
   - 现象：初期集成时出现管道符类型错误、参数传递不匹配等语法问题
   - 影响：程序无法正常运行，链路执行中断
3. **检索器重复执行问题**
   - 现象：单次问答流程中，interactive_qa函数打印的参考来源,retriever被调用4次，造成不必要的性能开销
   - 影响：响应速度变慢，向量库访问压力增大
4. **参考来源与实际文档不匹配问题**
   - 现象：interactive_qa函数打印的参考来源，与qa_chain内部实际生成答案所用的文档不一致
   - 影响：调试信息失真，无法通过打印的参考来源定位答案错误原因

---

## 四、今日已解决问题
| 问题名称 | 根因分析 | 解决方案 | 优化状态 |
|---------|---------|---------|---------|
| 查询重写违规篡改 | 早期重写规则约束缺失，仅用否定性话术，大模型约束力弱 | 新增强制正向规则+精准错误反例，明确禁止行为与正确示例 | ✅ 已完全修复 |
| 自我纠正链路集成 | 对LCEL语法不熟悉，参数传递方式错误 | 按照标准LCEL写法重构子链，使用RunnableLambda包装自定义函数 | ✅ 已完全修复 |
| 基础问答准确率低 | 查询重写错误导致检索失效，答案生成缺乏校验 | 优化查询重写+新增自我纠正双链路 | ✅ 已显著提升 |

---

## 五、今日未解决问题
1. **检索器重复4次执行问题**
   - 状态：已定位根因，完成修复方案设计，暂未修改代码
   - 根因：generate_answer_chain内部调用1次，self_correction_chain内部调用1次，interactive_qa函数手动调用2次，共4次检索
   - 影响：响应速度变慢，向量库访问压力增大
   - 修复方案：暂时停止打印参考来源，并未完全解决问题，根本修复方案看问题2

2. **参考来源与实际文档不匹配问题**
   - 状态：已定位根因，完成修复方案设计，暂未修改代码
   - 根因：函数内手动调用retriever仅用于打印，而生成答案和自我纠正使用内部独立检索，MMR随机性导致结果不一致
   - 影响：调试信息失真，无法通过打印的参考来源定位答案错误原因
   - 修复方案：改造答案生成链与自我纠正链，取消内部自动检索，改为接收外部传入的上下文文档
   -今日测试结果没有脱离预期，暂时不需要定位参考来源来大幅度修改参数，所以问题2未执行实际修复

---

## 七、今日总结
今日成功完成查询重写终极优化与自我纠正功能落地，系统综合准确率从70%提升至88%，突破85%达标线。查询重写的历史致命错误已彻底解决，自我纠正功能有效降低了幻觉率，提升了答案的完整性和准确性。

当前系统核心功能正常，仅存在两个非致命的链路设计缺陷和少量业务逻辑瑕疵。明日执行自动测试脚本时，如测试结果未达预期，将启动参考来源定位方案，修复问题2.

# Day9 完成：
1. 固定MMR随机种子+调参，解决检索波动问题
2. 目前固定为temperature=0.1 + 文本清洗，实现问答结果100%稳定 测试 0  0.01  0.05效果不好
3. 优化.gitignore，清理Git缓存，规范工程文件
4. 全量测试通过，功能正常，准确率达标

# Day10: RAG 自动化测试脚本（Day10）
## 日志类型：开发 + 学习 + 问题复盘
### 任务：
1. 搭建自动化测试脚本，支持批量测试和 CSV 报告生成
2. 完成 Day7 20 道题首次自动化测试
3. 统一全局拒答话术

### 一、今日完成工作
迭代优化 test_rag.py 批量测试脚本，完善 异常捕获、中间数据留存、CSV 报告导出 全流程逻辑。
梳理 RAG 三条子链调用逻辑：问题重写、原始答案生成、答案修正，修正历史错误调用代码。
对脚本核心代码逐行拆解学习，固化 Python 基础语法、标准库使用规范。
运行多组测试用例生成 CSV 测试报告，验证脚本稳定性与输出格式规范性。
### 二、今日学习知识点
1. 异常处理相关
try...except Exception as e 通用异常捕获机制：捕获代码运行时异常，避免单条用例报错导致整体程序中断。
异常对象 e：存储错误描述、异常类型等信息，str(e) 可获取可读报错文本。
调试进阶：使用 traceback 模块打印完整异常堆栈，快速定位报错文件、行号与代码。
2. 局部变量判断 & 三元表达式
locals()：内置函数，返回当前函数内所有局部变量字典，可判断变量是否已定义。
语法 var if 'var' in locals() else ""：三元表达式结合 locals()，异常场景下保留已成功赋值的变量，未执行的变量兜底为空字符串，同时规避 NameError。
3. CSV 标准库（csv）
csv.DictReader / csv.DictWriter：专门实现字典与 CSV 文件互读写。
fieldnames：定义 CSV 表头，需与字典 key 一一对应；writeheader() 写入表头，writerows() 批量写入多行数据。
跨平台换行核心：open() 中 newline='' 参数作用。
4. 文件读写 & 换行符体系
不同操作系统原生换行符：Windows \r\n、Linux/macOS \n。
csv 库固定特性：每写完一行会自动追加 \n。
平台表现差异：无 newline='' 时，Windows 会出现明显空行；Linux/macOS 因文本工具、CSV 解析器兼容，视觉无空行，但底层仍是双换行 \n\n。
5. 时间格式化
datetime.now().strftime("%Y-%m-%d %H:%M:%S")：将时间对象转为 年-月-日 时:分:秒 格式字符串，掌握 %Y/%m/%d/%H/%M/%S 格式符含义。
6. RAG 子链分工规范
rewrite_query：实现问题重写；
generate_answer_chain：生成原始答案 raw_answer；
self_correction_chain：基于原始答案做修正，生成最终答案 final_answer。

# Day11: RAG 自动化测试脚本（Day11）
优化rag链路节约token,优化prompt 部分回答依旧有问题，自我纠正部分待优化

# Day12: RAG 自动化测试脚本升级前置准备工作
⭕目前：
✅ 测试完成！
📊 整体准确率：86.00%
📈 各类型准确率：
  - 人物身份：75.00% (10.5/14)
  - 场所归属：75.00% (6.0/8)
  - 礼制规矩：83.33% (5.0/6)
  - 事件缘由：100.00% (7.0/7)
  - 事件结果：100.00% (1.0/1)
  - 事件细节：100.00% (2.0/2)
  - 统计类：50.00% (0.5/1)
  - 人物关系：100.00% (4.0/4)
  - 场所功能：100.00% (2.0/2)
  - 无答案：100.00% (5.0/5)
   day11未完全收尾，后续可能要更换模型，希望能提升到90%
✅ Python 3.14 → 3.12.8 版本回退，解决兼容问题
✅ Day11 测试准确率 86%，已归档
# Day12: 缓冲日 — 环境收尾 + 多模型接入 + 配置规整
## 完成事项
✅ Milvus Lite 测试通过：连接/建集合/插入/查询 四步全绿
✅ 多模型 LLM 客户端就绪：DeepSeek V4 + Kimi 2.6 + 通义千问，一行参数切换
✅ Ollama + Llama3:8b 已安装验证，本地模型兜底可用
✅ BGE 模型下载脚本就绪
✅ DeepSeek / Kimi 账号已注册，API Key 已生成
✅ 配置文件归整：所有配置统一放 `config/`，删除根目录冗余 `.env` 和 `config.yaml`
✅ `.gitignore` 补充排除规则

## 跳过项（非阻塞）
- Claude Code / CC Switch：Anthropic 封中国区，OAuth 和 API Key 均不可用
  → DeepSeek + Kimi + Qwen 三模型足够覆盖全部开发，无需 Claude

## 项目约定更新
- 所有配置文件一律放 `config/` 文件夹

## 项目一重点难点标记
1. 文档解析：用Marker替换PyPDF，解决PDF表格和图片解析问题
2. 混合检索：BM25+向量检索+重排序，提升检索准确率
3. 多模型切换：支持云端/本地模型自由切换，降低成本

---
# Day13✅ 完成

## 完成内容
1. 创建 `core/vector_store_manager.py`，实现多文档向量库独立管理（每份文档独立 collection，支持按文档名过滤检索）
2. `from langchain_community.embeddings import DashScopeEmbeddings` 警告处理：忽略 sunset 警告，后续 Day15 迁移 Milvus 时一并替换
3. 修复 Windows 下 Chroma 文件锁未释放导致 `PermissionError` 的问题（`delete_collection` 方法增加 `gc.collect()` + 重试机制）
4. 创建 `utils/marker_parser.py`，Marker 文档解析器骨架就绪（Marker v1.10.2 安装验证通过）
5. `utils/marker_parser.py` 测试脚本就绪（待实际 PDF 解析验证）

## 新增文件
- `core/vector_store_manager.py` — 多文档向量库管理器
- `utils/marker_parser.py` — Marker 文档解析器（骨架）

## 具体执行情况
- `vector_store_manager.py` 测试通过：导入/检索/删除全流程 ✅
- Marker 安装验证：`pip show marker-pdf` → v1.10.2 ✅
- 3份测试文档已放入 `data/raw/`：wenben1.txt、wenben2.pdf、wenben3.pdf ✅
- `delete_collection` Windows 文件锁 bug 已修复（gc + 重试3次）

## 未完成事项（顺延 Day14）
- `utils/marker_parser.py` 尚未用实际 PDF 验证解析效果
- `utils/chunker.py` 规则分块器尚未创建
- `scripts/import_docs.py` 多文档批量导入脚本尚未创建
- 3份文档分块隔离效果尚未测试验证

## 明日（Day14）待办
1. 验证 `marker_parser.py` 实际解析效果（用 wenben2.pdf / wenben3.pdf）
2. 创建 `utils/chunker.py` 规则分块器
3. 创建 `scripts/import_docs.py` 多文档批量导入脚本
4. 完成3份文档导入 + 隔离检索验证
5. 如 Day14 计划有空余时间，提前启动缓存机制开发

## 今日遇到的问题
1. **`ModuleNotFoundError: No module named 'langchain_chroma'`**
   - 解决：`pip install langchain-chroma`
2. **`ModuleNotFoundError: No module named 'langchain_community'`**
   - 解决：`pip install langchain-community`
3. **`ModuleNotFoundError: No module named 'config'`**
   - 原因：`core/` 子目录运行，Python 找不到项目根目录的 `config` 模块
   - 解决：文件头部加 `sys.path.insert(0, str(Path(__file__).parent.parent))`
4. **Windows `PermissionError: 另一个程序正在使用此文件`**
   - 原因：Chroma 删除 collection 时文件句柄未释放
   - 解决：`delete_collection` 中先 `store.delete_collection()` → `del` → `gc.collect()` → 重试3次删目录

## Git 提交（待执行）
```bash
git add .
git commit -m "Day13：多文档向量库隔离架构 + Marker解析器骨架 + Windows文件锁bug修复"
git push
```

---

# Day16— Token统计 + 规则分块 + 全链路日志

## 完成内容
1. **Token统计**：新建 `core/cost_tracker.py`，按模型不同自动计费，内存统计 + JSONL持久化
2. **llm_client.py 集成**：`tracker.record()` 挂在 `_openai_compatible_chat()` 和 `_ollama_chat()` 内部
3. **规则分块器**：新建 `utils/chunker.py`，接收 marker 的 `List[Document]`，表格/图片透传，文本段落拼接至 chunk_size
4. **全链路日志**：新建 `core/request_logger.py`，JSONL 格式，每天一个文件，记录 request_id/query/token/cost
5. **plan_v2.md 重构**：对照 plan1 查漏，补回 8 个遗漏任务

## 新增文件
- `core/cost_tracker.py`
- `core/request_logger.py`
- `utils/chunker.py`

## 修改文件
- `core/llm_client.py`（tracker + logger 集成）

## 验证结果
- Token统计：DeepSeek 1次调用 → 10/440 token → ¥0.000125 ✅
- 规则分块：wenben2.pdf → 67块解析 → 22块分块（text×12 + image×9 + table×1）✅
- 全链路日志：`logs/requests_2026-06-06.jsonl` 写入验证 ✅

## Git 提交
```bash
git add .
git commit -m "Day16：Token统计(cost_tracker) + 规则分块器(chunker) + 全链路日志(request_logger)"
git push
```

---

# Day17— Guardrails 全天

## 完成内容
1. **新建 `core/guardrails.py`**：三层输入护栏
   - 敏感词过滤（`contains_sensitive_words`，黑名单匹配）
   - 明显无关话术拦截（`is_off_topic`，正则快速匹配）
   - 文档查询意图检测（`is_likely_doc_query`，通用不限主题）
   - 三层短路逻辑：任意命中即拒答，不调 LLM，零 Token 消耗
2. **集成护栏到 `rag/base_rag.py`**：
   - `apply_input_guard()` 3行集成到 `interactive_qa()`（第473行）
3. **引用标注统一管理**（方案 B）：
   - `CITATION_INSTRUCTION` 在 `guardrails.py` 中定义
   - `base_rag.py` 通过 `from core.guardrails import CITATION_INSTRUCTION` 引用
   - `get_prompt()` 硬编码替换为 `{CITATION_INSTRUCTION}` 变量
   - 以后改规则只改一处
4. **修复引用标注格式**：
   - 示例中"宫廷剧本全集.txt"替换为通用"检索文档"
   - 解决 LLM 模仿示例编造来源的问题
5. **向量库重建**：
   - 发现 ChromaDB 为空（0 chunk），LLM 在凭空编造答案
   - 运行 `create_vector_store()` 重建向量库

## 遇到的关键问题
1. **LLM 幻觉发现**：ChromaDB 0条数据时，LLM 仍生成看似合理的宫廷剧本内容并标注 `[chunk_N]`
   → 是因为 `get_prompt()` 里的引用规则示例让 LLM 学会了模仿格式
   → 修复后仍需加"检索为空则拒答"的逻辑（暂未实现）
2. **SSL 连接错误**：dashscope API 连不上 → 关闭代理后解决
3. **Python 3.14 路径警告**：错误栈中出现 3.14 路径，但 `.venv` 实际为 3.12

## 新增文件
- `core/guardrails.py`

## 修改文件
- `rag/base_rag.py`（3处：导入 CITATION_INSTRUCTION + 导入 apply_input_guard + 集成护栏）
- `F:\AIStudy\ProjectPlan\plan_v2.md`（FastAPI 层 + 分层记忆 + 学习清单）

## 今日产出评估
- Guardrails 三层拦截：11/11 单元测试通过 ✅
- 引用标注统一：单一来源，不再散落 ✅
- 输入护栏集成：敏感词/闲聊 100% 拦截 ✅

## Git 提交（待执行）
```bash
git add .
git commit -m "Day17：Guardrails三层护栏 + 引用标注统一管理 + 向量库重建"
git push
```


---

# Day18.5 补充（6.13）— 护栏精简 + 面试文件重组

## 背景
项目从"宫廷剧本专用"升级为"通用文档检索"，用户指出原有的 `OFF_TOPIC_PATTERNS`（正则话题过滤）和超短词拦截（`len <= 3`）在通用场景下会误拦正当问题。例如：
- 如果文档是 AI 论文，"什么是人工智能"是合理问题，但被 `r"什么是人工智能"` 正则拦下
- 用户回复"好""嗯"（回应 RAG 追问），被 ≤3 字规则拦下

## 改动

### `core/guardrails.py` — 从三层精简到两层
- ❌ 删除 `DOC_QUERY_INTENT_KEYWORDS` 列表（含"好的""可以""嗯""行"等对话词，错放位置）
- ❌ 删除 `OFF_TOPIC_PATTERNS` 正则列表
- ❌ 删除 `is_off_topic()` 函数
- ❌ 删除 `is_likely_doc_query()` 函数
- ❌ 删除 `import re`（不再需要）
- ✅ 保留 `contains_sensitive_words()` + 空输入检查
- ✅ `check_query()` 从 20 行缩到 8 行
- ✅ `REJECT_EMPTY = "请输入您的问题。"`（替代旧的 `REJECT_OFF_TOPIC`）
- ✅ 单元测试更新：13/13 通过

### `F:\AIStudy\study\interview_notes_rag.md` — 按功能模块重组
- 从按时间（一~十二）改为按功能模块（八大模块）
- 同一代码文件的内容放一起：RAG核心链路 → 文档解析 → 向量数据库 → 可观测性 → 评测 → 技巧 → 踩坑
- 🆕 新增 Q14：护栏设计演进（从三层到一层，从过度防御到信任系统）

## 设计理念
> "在通用文档检索场景下，检索器本身就是最好的相关性过滤器。输入护栏只负责安全底线，不替检索器做内容判断。"

## Git 提交（待执行）
```bash
git add .
git commit -m "Day18.5：护栏精简(三层→两层) + 面试文件按模块重组"
git push
```


---

### Prompt 通用化（6.13 晚间）

**`QUERY_REWRITE_PROMPT`**：
- ❌ 删除 "专门处理宫廷剧本问答"
- ❌ 删除 "陛下、皇帝、圣上 → 燕光逸" 硬编码映射
- ❌ 删除宫廷剧本专属错误示例
- ✅ 改为通用代词消解：他/她/它/这个/这件事/这里 → 文中提到的...
- ✅ 新增通用示例：函数怎么用、第三章讲了什么、他为什么做这个决定
- ✅ 规则 3 明确：不修改任何专有名词、术语、人名、地名、产品名

**`get_prompt()` 模板**：
- ❌ 删除规则 5：陛下/皇上/新帝 → 燕光逸 硬编码
- ❌ 删除规则 7：仅依据宫殿名称判断居所
- ✅ 规则 5 改为：使用文档原文术语，不做同义替换
- ✅ 规则 8 新增：技术文档中的步骤、参数、配置原样引用
- ✅ 规则 3 改为：人物/实体以文档正式名称为准
- ✅ 第一行加：适用于各类文档（小说、技术文档、论文、剧本、新闻等）


---

# Day18.5 完整日志（周六）— 代码梳理 + 全线精简 + 计划重整

## 一、完成事项

### 1. Guardrails 精简（上午）
- `core/guardrails.py`：三层输入护栏 → 两层（敏感词 + 空输入）
- 砍掉：`OFF_TOPIC_PATTERNS`、`DOC_QUERY_INTENT_KEYWORDS`、`is_off_topic()`、`is_likely_doc_query()`、`import re`
- 单元测试 13/13 通过

### 2. Prompt 通用化
- `QUERY_REWRITE_PROMPT`：去掉宫廷剧本专用规则，改为通用代词消解
- `get_prompt()` 模板：去掉燕光逸/宫殿硬编码，支持小说/技术文档/论文

### 3. cost_tracker.summary() 接入
- 两个 `interactive_qa()` 退出时打印会话统计（调用次数/Token/费用/分模型）

### 4. 面试文件按功能模块重组
- `F:\AIStudy\study\interview_notes_rag.md` 完全重写，八大模块
- 新增 Q14：护栏设计演进（从三层到一层）

### 5. 全项目代码梳理（晚间）
逐模块排查连接关系，发现重大断层：

| 已写好的组件 | 是否接入 RAG 链 |
|-------------|:--:|
| `marker_parser.py` | ❌ |
| `chunker.py` | ❌ |
| `vector_store_manager.py` | ❌ |
| `llm_client.py` | ❌ |
| `cost_tracker.py` | ✅ 但 `summary()` 未接 |
| `cache.py` | ❌ 382行代码完整但零连接 |
| `guardrails.py` | ✅ |
| `document_loader.py` | ✅ 用的是旧 PyPDFLoader |
| `vector_store.py` | ✅ 用的是旧 RecursiveCharacterTextSplitter |

**当前 RAG 实际跑的是 Day1-3 旧管线**：
`PyPDFLoader → RecursiveCharacterTextSplitter → ChromaDB → ChatTongyi 硬编码`

### 6. 计划重整
- `plan_v2.md` 插入 **Day20 梳理接线日（6.14）**，暂停所有新功能
- Day18 欠账（缓存+Ollama）和 Day19 内容（BM25+语义分块）全部保留
- 所有后续计划 +2 天，第一波投递 6.17→6.19

## 二、今日核心认知

> "项目不是没写完，是写了两套系统——旧管线在跑，新管线在仓库里闲着。明天不写一行新代码，把火车站已经造好的轨道连上就让列车跑起来。"

## 三、修改文件清单
- `core/guardrails.py`：精简
- `rag/base_rag.py`：Prompt通用化 + cost_tracker接入
- `docs/plan_log.md`：本条目
- `F:\AIStudy\ProjectPlan\plan_v2.md`：插入Day20 + 全盘日期偏移
- `F:\AIStudy\study\interview_notes_rag.md`：按模块重组 + 新增Q14

## Git 提交（待执行）
```bash
git add .
git commit -m "Day18.5：全项目梳理 + 护栏精简 + Prompt通用化 + 计划重整 + 接线日安排"
git push
```


---


# Day20 启动— 接线日前半段

## 完成内容

1. **架构梳理**：明确 `vector_store.py`（适配层）和 `vector_store_manager.py`（引擎层）分工，两文件都保留，Day24 再合并。

2. **day20_plan.md 修正**：伪代码三处函数名错误已修复。

3. **文档管线首次跑通**：`create_vector_store()` 新管线（marker_parser → chunker → vector_store_manager）首次执行。

4. **Chunker 超长段 bug 修复**：
   - 现象：DashScope embedding `Range of input length should be [1, 2048]`
   - 根因：`rule_chunk()` 对超长单段落原样放行
   - 修复：`utils/chunker.py` 超长段强制按 chunk_size 切多块，段内 overlap，段间不重叠

## 修改文件
- `utils/chunker.py`：超长段强制拆分
- `F:\AIStudy\study\day20_plan.md`：修正函数名

## 明日继续
Day20 接线②（LLM 切换）+ 接线③（缓存）+ 全链路验证

---

# Day20 接线日②｜2026-06-20

## 完成内容

### 1. 模型配置统一
- `llm_client.py:52`：qwen model_name → `qwen-plus-2025-12-01`（免费额度到期后用带日期后缀的版本）
- `llm_factory.py`：删除重复的 MODEL_CONFIG 字典，改为 `LLMClient.MODEL_CONFIG[_TYPE_MAP[model_type]]` — 以后换模型只改 `llm_client.py` 一处
- `base_rag.py:15`：删除失效的 `MODEL_CONFIG` import

### 2. CITATION_INSTRUCTION 修复
- 根因：`get_prompt()` 里 `{CITATION_INSTRUCTION}` 被 `PromptTemplate.from_template()` 当做变量占位符，每次 invoke 要求传入
- 修复：`template.replace("{CITATION_INSTRUCTION}", CITATION_INSTRUCTION)` 写死为 Python 常量，用 `.replace()` 而非 `.format()` 避免 `{context}` `{question}` 被误匹配

### 3. 多文档检索器管道桥接
- `rag/vector_store.py`：新增 `MultiDocRetriever(BaseRetriever)` 类，实现 `_get_relevant_documents()` 桥接到 `VectorStoreManager.search()`
- `load_vector_store()` 重写：不再返回 Chroma 实例，改为 `VectorStoreManager()` → `MultiDocRetriever(manager)`
- `base_rag.py`：`get_rag_chain()` 里 7 行 `as_retriever(MMR)` 简化为 1 行 `load_vector_store(top_k=...)`

### 4. VectorStoreManager 自动加载磁盘集合
- 问题：每次 `VectorStoreManager()` 新建实例，`self._stores` 是空字典，即使磁盘上 `chroma_db/wenben1/` 已有数据也搜不到
- 修复：新增 `_auto_load_collections()` 方法 + `__init__` 末尾调用，扫描 `persist_root` 目录自动调用 `create_collection(entry.name)` 加载
- 额外修复：`search()` 里 `store = self._stores.get(doc_name)` → `or self._stores.get(self._sanitize_name(doc_name))`，兼容 `doc_filter=["wenben1.txt"]` 查 key 为 `"wenben1"` 的情况

### 5. vector_store.py __main__ 重写
- 修复 `search()` 返回值类型错误（dict 列表 → 用 `result['score']` 而非 `(doc, score)` 解包）
- 加 `SEARCH_DOC = None` 开关，方便切全部/单文档检索

### 6. 面试笔记更新
- 新增 Q17：LangChain 管道中 MultiDocRetriever 运行原理（模板方法模式、管道数据流）

### 7. main.py 全链路跑通 ✅
- 启动 → 自动加载向量库 → 查询重写 → 检索（20条结果）→ 生成答案 → 显示来源

## 修改文件
- `core/llm_client.py`
- `core/llm_factory.py`
- `rag/base_rag.py`
- `rag/vector_store.py`
- `core/vector_store_manager.py`

## 剩余
- cache.py 集成（4行插入 interactive_qa()）✅ 已完成（2026-06-22）

## Git 提交（待执行）
```bash
git add .
git commit -m "Day20 接线日：模型配置统一 + 检索器管道桥接 + 向量库自动加载 + 全链路跑通"
git push
```

---

# Day20 收尾：缓存集成完成｜2026-06-22

## 完成内容

### 1. cache.py 集成到 interactive_qa() ✅
- 4行插入：查缓存 → 命中则跳过 LLM 调用 → 未命中则正常调用并写入缓存
- 验证通过：`玩家是谁` → `[缓存命中 ⚡] 零 Token 消耗`

### 2. 缓存系统核心概念吃透
- **两层架构**：内存字典（`self._cache`）高速读写 + JSON 文件（`logs/cache.json`）持久化
- **为什么全量加载到内存**：磁盘 IO 比内存慢 5-6 个数量级，缓存放内存才能 O(1) 查询
- **为什么全量覆盖写**：JSON 格式不支持追加；全量写实现最简单、一致性最好；中小规模完全够用
- **过期清理策略**：惰性删除（查询时检查 TTL，过期即删）+ 定期统计（`summary()` 显示命中率）

### 3. 并发安全
- `threading.Lock` 写锁：保护 `self._cache` 字典的增删改 + `_save_to_disk_unsafe()` 落盘
- 读不加锁：Python 字典单次读取线程安全（GIL 保证），读多写少场景优化
- 不可重入锁陷阱：内部 `_unsafe` 函数不加锁，由外层 `with self._lock` 统一保护

### 4. 单例 + 懒加载
- 模块级全局变量 `_cache_instance` + `get_cache()` 工厂函数
- 单例保证全局唯一，懒加载减少启动开销

### 5. 面试笔记更新
- 新增 Q20：缓存架构设计面试高频问答（内存vs磁盘、全量写vs增量写、多线程安全、单例懒加载）

## 修改文件
- `rag/base_rag.py`：interactive_qa() 集成 cache 查询/写入 4行
- `F:\AIStudy\study\interview_notes_rag.md`：新增 Q20

## Git 提交（待执行）
```bash
git add .
git commit -m "Day20收尾：cache集成完成 + 缓存命中验证 + 缓存架构面试笔记"
git push
```

---

# Day21（前半）：BM25 检索器 + RRF 混合检索｜2026-06-23

## 完成内容

### 1. `core/bm25_retriever.py`（新建）✅
- `BM25Retriever` 类：`rank_bm25.BM25Okapi` 中文关键词检索器
- 分词策略：`re.findall` 字符级分词（按中文字符 + 英文单词 + 数字），不用 jieba
  - **选型依据**：小说文档含大量自创专有名词，jieba 词典覆盖不到会切错，BM25 的 TF-IDF 自带罕见字加权，字符级天然适配
- 多文档隔离架构：每文档独立 BM25 实例，支持增量更新、互不干扰 IDF 计算
- 返回格式与 `VectorStoreManager.search()` 一致（`List[Dict]`）
- 持久化：`pickle.dump` 二进制保存索引

### 2. `rag/hybrid_retriever.py`（新建）✅
- `_rrf_fusion()` 函数：RRF 算法 `score = 1/(k+rank)`，`k=60`，用文本前 200 字做去重 key
- `HybridRetriever(BaseRetriever)`：组合 BM25 + VectorStoreManager → RRF 融合 → LangChain 兼容
- 依赖注入设计：BM25Retriever 实例从外部传入，HybridRetriever 只管融合

### 3. 关键知识点消化
- **BM25Okapi**：TF-IDF 词频统计，`get_scores()` 返回和语料顺序对应的分数数组
- **corpus 二维列表**：`List[List[str]]`，外层是 chunk 列表，内层是分词后的 token 列表
- **双层排序**：单文档内降序 + 跨文档全局排序，后者是多文档场景的必需步骤
- **RRF vs 加权平均**：RRF 不对原始分数做归一化，只比排名，天然兼容 BM25 和向量两种不同尺度分数
- **pickle vs json**：pickle 保存复杂对象（BM25 索引），json 保存基础数据（缓存配置）

### 4. 易错点总结
1. BM25 初始化必须传二维语料，查询打分传一维列表
2. RRF 排名从 1 开始（`enumerate(..., start=1)`），从 0 会算错
3. pickle 用 `wb`/`rb`，json 用 `w`/`r`
4. JSON `ensure_ascii=False` + `encoding="utf-8"` 避免中文乱码

## 修改文件
- `core/bm25_retriever.py`（新建）
- `rag/hybrid_retriever.py`（新建）

## 明日继续
- 改 `rag/vector_store.py` 的 `load_vector_store()`：创建 BM25Retriever 实例 → 构建索引 → 返回 HybridRetriever
- 语义分块 + 全链路测试

## Git 提交（待执行）
```bash
git add .
git commit -m "Day21前半：BM25检索器 + RRF混合检索框架完成"
git push
```

---

# Day21 后半 + 项目大清理｜2026-06-27

## 完成内容

### 1. 成本追踪复活（Token 统计归零 bug 修复）✅
- **根因**：`LLMClient._openai_compatible_chat()` 里的 `tracker.record()` 从未被调用——RAG 系统用的是 `create_llm()` → `ChatOpenAI`，完全绕过 `LLMClient`
- **修复**：在 `llm_factory.py` 新增 `CostTrackingCallback(BaseCallbackHandler)`，挂到 `ChatOpenAI(callbacks=[...])`，每次 LLM 调用结束自动触发 `on_llm_end()` → `tracker.record()`
- **验证**：退出时输出「总调用 9 次 / 总输入 70831 Token / 总费用 ¥0.0000」✅（费用为 0 待修，PRICING 短名匹配问题）

### 2. llm_client.py + llm_factory.py 合并 ✅
- 删除 `LLMClient` 类、`_openai_compatible_chat()`、`_ollama_chat()`、`get_client()`、`chat()` 全部死代码
- 保留 `ModelType` 枚举 + `MODEL_CONFIG` 字典（唯一配置维护点）+ `create_llm()`
- 新增 `CostTrackingCallback` + `CostTrackingCallback` 挂载
- `llm_client.py` 安全删除（无文件引用）

### 3. 配置文件清理
- `settings.py`：注释掉 5 个死配置（`LLM_MODEL_NAME`、`DEEPSEEK_MODEL_NAME`、`DEEPSEEK_FLASH_MODEL_NAME`、`KIMI_MODEL_NAME`、`COLLECTION_NAME`），所有模型名已收归 `llm_factory.py`
- `config.yaml`：确认无人引用，历史遗留文件
- `vector_store.py`：删除 `COLLECTION_NAME` 导入

### 4. 死代码大清理
**`base_rag.py` 删除：**
- `import random, numpy as np` + `SEED`（MMR 已移除）
- `DASHSCOPE_API_KEY` 导入（只用于注释代码）
- `format_docs()` 壳函数（无人调用）
- 旧版 `interactive_qa()`（被新版覆盖）

**`vector_store.py` 删除：**
- `load_documents_from_json()` — 旧版文档加载，已废弃
- `split_documents()` — 旧版 RecursiveCharacterTextSplitter，已改用 rule_chunk
- `MultiDocRetriever` 类 — 已由 `HybridRetriever` 替代
- `similarity_search()` — 无人调用
- 无用 import：`DashScopeEmbeddings`、`Chroma`、`RecursiveCharacterTextSplitter`、`BaseRetriever`、`json`

## 修改文件
- `core/llm_factory.py`（合并 + CostTrackingCallback）
- `core/llm_client.py`（已删除）
- `config/settings.py`（注释死配置）
- `rag/vector_store.py`（删除死代码 + 清理导入）
- `rag/base_rag.py`（删除死代码）
- `rag/hybrid_retriever.py`（修复 source 不含后缀 bug）

## 关键理解
- **LangChain callback 机制**：`BaseCallbackHandler.on_llm_end()` 是 LLM 调用结束的钩子，挂到 `ChatOpenAI(callbacks=[...])` 自动触发
- **单一配置源**：`MODEL_CONFIG` 在 `llm_factory.py` 是唯一维护点，`settings.py` 只管运行时参数（temperature、chunk_size）
- **死代码清理原则**：先 grep 确认无人引用 → 注释 → 测试通过 → 删除

## Git 提交（待执行）
```bash
git add .
git commit -m "Day21后半：成本追踪复活 + 文件合并 + 项目大清理"
git push
```