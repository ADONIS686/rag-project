import sys
from pathlib import Path

# 把项目根目录（F:\rag-project）加入Python搜索路径
sys.path.append(str(Path(__file__).parent.parent))
# 导入Document对象
from langchain_core.documents import Document
import os
import shutil
# 导入全局配置
from config.settings import (
    DASHSCOPE_API_KEY,
    EMBEDDING_MODEL_NAME,
    VECTOR_DB_PATH,
    ALLOW_DOC_NAMES
)

# ------------------- 函数：创建向量库并保存到本地 -------------------
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


# ------------------- 加载已存在的本地向量库 -------------------
def load_vector_store(doc_filter=None, top_k: int = 10):
    """
    加载多文档向量库 + BM25 索引，返回 LangChain 兼容混合检索器
    """
    from core.vector_store_manager import VectorStoreManager
    from core.bm25_retriever import BM25Retriever
    from rag.hybrid_retriever import HybridRetriever

    manager = VectorStoreManager()

    # 构建 BM25 索引（如果还没构建的话）
    bm25 = BM25Retriever()
    for doc_name in list(manager._stores.keys()):
        # 从 Chroma 拿回该文档的所有 chunk
        store = manager._stores[doc_name]
        all_chunks = store.get()  # Chroma.get() 返回所有文档
        if all_chunks and all_chunks["ids"]:
            from langchain_core.documents import Document
            chunks = [
                Document(
                    page_content=content,
                    metadata=meta,
                )
                for content, meta in zip(
                    all_chunks["documents"], all_chunks["metadatas"]
                )
            ]
            bm25.index_documents(doc_name, chunks)
        else:
            print(f"  ⚠️  {doc_name} 向量库为空，跳过 BM25 索引")

    return HybridRetriever(manager, bm25, top_k=top_k, doc_filter=doc_filter)

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