# 导入系统路径模块，处理文件和文件夹路径
import os
# 导入正则模块，处理文本格式
import re
# 导入JSON模块，保存处理后的文档
import json
# 导入两个加载器工具
from langchain_community.document_loaders import PyPDFLoader, TextLoader
# 导入Document对象，规范返回格式
from langchain_core.documents import Document
# ==========【新增白名单】==========
from config.settings import ALLOW_DOC_NAMES

# ------------------- 函数1：读取单个文档（自动识别PDF/TXT）-------------------
def load_single_document(file_path: str) -> Document:
    """
    功能：传入一个文件路径，自动判断是PDF还是TXT，返回合并后的完整Document对象
    参数：file_path - 单个文档的完整路径
    返回：一个规整的Document对象
    """
    # 获取文件后缀（比如.pdf/.txt），转小写避免大小写问题（比如.PDF和.pdf）
    file_extension = os.path.splitext(file_path)[1].lower()

    # 如果是PDF文件
    if file_extension == ".pdf":
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        # 合并所有页的内容 []可以不用加，直接在join里写生成器表达式
        combined_content = "\n".join([page.page_content for page in pages])
        # 返回Document对象，包含内容和元信息
        return Document(
            page_content=combined_content,
            metadata={"source": file_path, "type": "pdf"}
        )

    # 如果是TXT文件
    elif file_extension == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
        # TXT只有1页，直接取第一个元素
        doc = loader.load()[0]
        # 补充元信息
        doc.metadata["type"] = "txt"
        return doc

    # 不支持的格式，直接报错提示
    else:
        raise ValueError(f"目前只支持PDF和TXT格式，当前文件格式：{file_extension}")

# ------------------- 函数2：批量读取文件夹内所有文档 -------------------
def load_documents_from_folder(folder_path: str) -> list[Document]:
    """
    功能：传入一个文件夹路径，自动读取里面所有的PDF和TXT文件
    参数：folder_path - 存放原始文档的文件夹路径
    返回：所有文档的Document对象列表
    """
    documents = []
    # 遍历文件夹里的所有文件
    for file_name in os.listdir(folder_path):
        # 先判断：文件名不在白名单 → 直接跳过忽略
        if file_name not in ALLOW_DOC_NAMES:
            print(f"⏭ 自动忽略非指定文档：{file_name}")
            continue
        # 拼接完整的文件路径（避免路径写错）
        file_path = os.path.join(folder_path, file_name)
        # 判断是不是文件（排除子文件夹）
        if os.path.isfile(file_path):
            # 获取文件后缀
            file_extension = os.path.splitext(file_name)[1].lower()
            # 只处理PDF和TXT
            if file_extension in [".pdf", ".txt"]:
                try:
                    # 调用上面的单个读取函数
                    doc = load_single_document(file_path)
                    documents.append(doc)
                    print(f"✅ 成功加载：{file_name}")
                except Exception as e:
                    print(f"❌ 加载失败：{file_name}，错误原因：{e}")

    return documents

# ------------------- 函数3：清洗文本（去除杂乱内容）-------------------
def clean_text(text: str) -> str:
    """
    功能：去掉文档里多余的空格、空行、制表符，让文本更规整
    为什么要做：原始文档里的杂乱内容会影响大模型理解和向量检索效果
    """
    # 把多个连续的换行符换成1个
    text = re.sub(r'\n+', '\n', text)
    # 把多个连续的空格、制表符换成1个空格
    text = re.sub(r'\s+', ' ', text)
    # 去掉文本开头和结尾的空格
    text = text.strip()
    return text

# ------------------- 函数4：过滤无效短文本 -------------------
def filter_short_documents(documents: list[Document], min_length: int = 50) -> list[Document]:
    """
    功能：删掉太短的无效内容（比如只有几个字的标题、空白页）
    参数：min_length - 最小有效字符数，少于50的直接删掉
    """
    return [doc for doc in documents if len(doc.page_content) >= min_length]

# ------------------- 函数5：保存处理后的文档为JSON文件 -------------------
def save_documents_to_json(documents: list[Document], output_path: str):
    """
    功能：把清洗后的文档保存为JSON文件，后续直接调用，不用重新读取
    """
    # 把Document对象转换成字典格式
    docs_json = []
    for doc in documents:
        docs_json.append({
            "page_content": doc.page_content,
            "metadata": doc.metadata
        })

    # 保存为JSON文件，ensure_ascii=False避免中文乱码 ascii不启动 indent是缩进=2让文件更易读
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docs_json, f, ensure_ascii=False, indent=2)

# 从JSON文件加载预处理好的文档（Day3专用）
def load_documents_from_json(file_path: str) -> list[Document]:
    with open(file_path, "r", encoding="utf-8") as f:
        docs_json = json.load(f)
    
    documents = []
    for doc in docs_json:
        documents.append(Document(
            page_content=doc["page_content"],
            metadata=doc["metadata"]
        ))
    return documents

# ------------------- 测试代码（直接运行即可）-------------------
if __name__ == "__main__":
    # 1. 读取原始文档
    raw_folder = "data/raw"
    raw_docs = load_documents_from_folder(raw_folder)
    print(f"原始文档总数：{len(raw_docs)}")

    # 2. 清洗所有文档的文本内容 还是一个元素是Document对象的列表，直接在循环里修改对象的属性就行了，不用重新创建新的Document对象
    cleaned_docs = []
    for doc in raw_docs:
        doc.page_content = clean_text(doc.page_content)
        cleaned_docs.append(doc)

    # 3. 过滤掉太短的无效文档 筛选过Document对象的文档列表，只有内容长度大于等于50的才保留
    filtered_docs = filter_short_documents(cleaned_docs)
    print(f"清洗过滤后有效文档数：{len(filtered_docs)}")

    # 4. 保存处理后的文档
    save_documents_to_json(filtered_docs, "data/processed_documents.json")
    print("✅ 文档预处理完成，结果已保存到：data/processed_documents.json")