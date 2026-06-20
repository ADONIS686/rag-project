import sys
from pathlib import Path

# 把项目根目录（F:\rag-project）加入Python搜索路径
sys.path.append(str(Path(__file__).parent.parent))
# 导入通义千问向量嵌入模型
from langchain_community.embeddings import DashScopeEmbeddings
# 导入ChromaDB向量库
#from langchain_community.vectorstores import Chroma
# 新写法 无警告
from langchain_chroma import Chroma
# 导入分块工具
from langchain_text_splitters import RecursiveCharacterTextSplitter
# 导入Document对象
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
# 导入json模块，加载Day2的预处理文档
import json
# ==========【新增导入删库模块】==========
import os
import shutil
# 导入全局配置
from config.settings import (
    DASHSCOPE_API_KEY,
    EMBEDDING_MODEL_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    VECTOR_DB_PATH,
    COLLECTION_NAME,
    ALLOW_DOC_NAMES
)
#自动调用文档预处理函数，生成processed_documents.json（如果已经有了就覆盖掉，保持最新）
#from utils.document_loader import load_documents_from_folder, clean_text, filter_short_documents, save_documents_to_json
# ------------------- 函数1：加载Day2预处理好的文档 【修改：置空废弃，不再使用】-------------------
def load_documents_from_json(file_path: str) -> list[Document]:
    """
    【废弃】不再手动读取json，全程自动生成
    """
    """
    【新手说明】：从Day2生成的processed_documents.json文件加载文档
    :param file_path: json文件路径
    :return: Document对象列表
    """
    with open(file_path, "r", encoding="utf-8") as f:
        docs_json = json.load(f)
    
    documents = []
    for doc in docs_json:
        documents.append(Document(
            page_content=doc["page_content"],
            metadata=doc["metadata"]
        ))
    
    return documents

# ------------------- 函数2：对文档进行分块 -------------------
def split_documents(documents: list[Document]) -> list[Document]:
    """
    【新手说明】：用刚才选的最优参数对文档进行分块
    :param documents: 完整文档列表
    :return: 分块后的文档片段列表
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )
    
    return text_splitter.split_documents(documents)

# ------------------- 函数3：创建向量库并保存到本地 -------------------
# ==========【修改1：删掉传入参数，无参调用】==========
# 旧：def create_vector_store(documents: list[Document]) -> Chroma:
# 新：
def create_vector_store() -> None:
    """
    全自动：自动预处理文档+生成json+清旧库+建新库
    """
    """
    【新手说明】：把分块后的文档转成向量，存入本地ChromaDB数据库
    :param documents: 分块后的文档片段列表
    :return: Chroma向量库对象
    """
    # ==========【新增：自动删除旧向量库】==========
    if os.path.exists(VECTOR_DB_PATH):
        import gc, time
        for attempt in range(3):
            try:
                shutil.rmtree(VECTOR_DB_PATH)
                print("🗑️ 已清理旧向量库，避免旧数据残留")
                break
            except PermissionError:
                gc.collect()
                time.sleep(0.5)
        else:
            print("⚠️ 清理旧向量库失败（文件被占用），将跳过清理直接导入")

    # ==========【新增：全套自动预处理逻辑】==========
    print("🔄 自动执行文档预处理...")
    # 新：Marker 解析 + 规则分块 + 多文档隔离入库
    from utils.marker_parser import parse_document
    from utils.chunker import rule_chunk
    from core.vector_store_manager import VectorStoreManager

    # 逐文档：Marker解析 → 规则分块 → 独立入库
    manager = VectorStoreManager()
    raw_dir = "data/raw"
    for file_name in os.listdir(raw_dir):
        if file_name not in ALLOW_DOC_NAMES:
            continue
        file_path = os.path.join(raw_dir, file_name)
        if not os.path.isfile(file_path):
            continue
        
        print(f"📄 处理: {file_name}")
        docs = parse_document(file_path)    # ① Marker AI 解析
        chunks = rule_chunk(docs)           # ② 规则分块（表格/图片透传）
        manager.import_document(file_name, chunks)  # ③ 多文档隔离入库
        print(f"   ✅ {len(chunks)} 个 chunk 入库")
    print(f"✅ 全部文档导入完成")

    # # 1. 自动加载白名单文档
    # raw_docs = load_documents_from_folder("data/raw")
    # # 2. 自动清洗
    # cleaned_docs = []
    # for doc in raw_docs:
    #     doc.page_content = clean_text(doc.page_content)
    #     cleaned_docs.append(doc)
    # # 3. 过滤短文本
    # filtered_docs = filter_short_documents(cleaned_docs)
    # # 4. 自动覆盖生成processed_documents.json
    # save_documents_to_json(filtered_docs, "data/processed_documents.json")
    # documents = filtered_docs
    # split_docs = split_documents(documents)
    # documents = split_docs

    # # 初始化向量嵌入模型（把文本转成数字向量）
    # embeddings = DashScopeEmbeddings(
    #     model=EMBEDDING_MODEL_NAME,
    #     dashscope_api_key=DASHSCOPE_API_KEY
    # )
    
    # # 创建向量库
    # vector_store = Chroma.from_documents(
    #     documents=documents,
    #     embedding=embeddings,
    #     persist_directory=VECTOR_DB_PATH,
    #     collection_name=COLLECTION_NAME
    # )
    
    # # 持久化保存到本地硬盘（下次不用重新创建）
    # #vector_store.persist()
    # print(f"新手提示：向量库创建成功，共存储{len(documents)}个文档块")
    
    #return vector_store

# ------------------- 函数4：多文档检索器（LangChain 兼容）-------------------
class MultiDocRetriever(BaseRetriever):
    """LangChain 兼容检索器，对接 VectorStoreManager 多文档隔离检索"""
    
    def __init__(self, manager, top_k: int = 10, doc_filter=None):
        super().__init__()
        self._manager = manager
        self._top_k = top_k
        self._doc_filter = doc_filter

    def _get_relevant_documents(self, query: str) -> list:
        results = self._manager.search(
            query, top_k=self._top_k, doc_filter=self._doc_filter
        )
        return [
            Document(page_content=r["content"], metadata={"source": r["document_name"]})
            for r in results
        ]


# ------------------- 函数4：加载已存在的本地向量库 -------------------
def load_vector_store(doc_filter=None, top_k: int = 10):
    """
    加载多文档向量库，返回 LangChain 兼容检索器
    :param doc_filter: 只搜指定文档，如 ["wenben1.txt"]；None = 搜全部
    :param top_k: 检索返回条数
    :return: MultiDocRetriever（可直接用于 LangChain 链）
    """
    from core.vector_store_manager import VectorStoreManager
    manager = VectorStoreManager()
    return MultiDocRetriever(manager, top_k=top_k, doc_filter=doc_filter)

# ------------------- 函数5：执行相似性查询 -------------------
def similarity_search(vector_store: Chroma, query: str, top_k: int = 3) -> list[tuple[Document, float]]:
    """
    【新手说明】：输入问题，返回最相关的top_k个文本块和相似度分数
    :param vector_store: 向量库对象
    :param query: 用户问题
    :param top_k: 返回结果数量
    :return: 包含(文档块, 相似度分数)的元组列表
    """
    # 带分数的相似性搜索（分数越低，相似度越高）
    results = vector_store.similarity_search_with_score(query, k=top_k)
    return results

# ------------------- 测试代码（直接运行即可）-------------------
if __name__ == "__main__":
    # 1. 创建向量库（多文档隔离入库）
    #create_vector_store()

    # 2. 用 VectorStoreManager 加载并检索
    from core.vector_store_manager import VectorStoreManager
    manager = VectorStoreManager()

    # 测试查询词
    test_queries = [
        "请介绍一下这个文档的主要内容",
    ]
    
    # 可选：指定只搜某个文档，None = 搜全部
    SEARCH_DOC = "wenben1.txt"  # 改成 "wenben1.txt" 则只搜该文档
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"查询问题：{query}")
        if SEARCH_DOC:
            print(f"搜索范围：{SEARCH_DOC}")
        print(f"{'='*50}")
        
        results = manager.search(
            query, top_k=3,
            doc_filter=[SEARCH_DOC] if SEARCH_DOC else None
        )
        
        if not results:
            print("⚠️ 未检索到任何结果")
            continue
        
        for i, result in enumerate(results):
            print(f"\n结果{i+1}（相似度分数：{result['score']:.4f}，越低越相似）：")
            print(f"内容：{result['content'][:300]}...")
            print(f"来源：{result['document_name']} (chunk_{result['chunk_id']})")