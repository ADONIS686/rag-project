"""
core/bm25_retriever.py — BM25 关键词检索器

职责：
  - 对已入库的所有文档 chunk 构建 BM25 稀疏索引
  - 提供 search() 方法，返回格式与 VectorStoreManager.search() 一致
  - 索引按文档隔离（每文档独立 BM25Okapi 实例），方便增量更新

依赖：rank-bm25（pip install rank-bm25）
"""
import sys
import pickle
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rank_bm25 import BM25Okapi
from langchain_core.documents import Document


# -------- 简易中文分词（不用 jieba，减少依赖）--------
def _tokenize(text: str) -> List[str]:
    """
    中文分词：按字切分 + 按空格切分英文词。
    BM25 不需要精确分词，字符级即可工作良好。
    [\u4e00-\u9fff]    分支1：单个中文字符
    [a-zA-Z]+          分支2：连续英文大小写单词
    \d+                分支3：连续数字
    """
    import re
    # 保留中文字符、英文单词、数字
    #re.findall(pattern, string)：遍历文本，把所有匹配正则的片段全部提取出来，返回列表，就是分词结果
    tokens = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+|\d+', text.lower())
    return tokens


class BM25Retriever:
    """
    BM25 关键词检索器（多文档隔离）

    用法:
        retriever = BM25Retriever()
        retriever.index_documents("wenben1.txt", chunks)   # 构建索引
        results = retriever.search("主角叫什么名字", top_k=10)
    """

    def __init__(self, index_dir: str = "data/bm25_index"):
        self._indexes: Dict[str, BM25Okapi] = {}       # {doc_name: BM25Okapi实例}
        self._corpus: Dict[str, List[List[str]]] = {}   # {doc_name: [分词后的chunk列表]}
        self._chunks: Dict[str, List[Dict]] = {}        # {doc_name: [原始chunk信息]}
        self._index_dir = Path(index_dir)

    # ========== 索引构建 ==========

    def index_documents(self, doc_name: str, chunks: List[Document]):
        """
        为一份文档的 chunk 构建 BM25 索引。

        参数:
            doc_name: 文档名（如 "wenben1.txt"）
            chunks:   分块后的 Document 列表
        """
        # ① 对每个chunk的page_content进行分词，得到一个二维列表tokenized，每个元素是一个chunk的分词结果
        tokenized = [_tokenize(chunk.page_content) for chunk in chunks]

        # ② 构建 BM25 索引
        #把所有分好词的语料喂给 BM25 算法，让它内部统计好词频、IDF、文档长度，建好索引，之后就能快速打分了。
        bm25 = BM25Okapi(tokenized)

        # ③ 保存原始 chunk 信息（检索时返回）
        chunk_infos = []
        for chunk in chunks:
            chunk_infos.append({
                "content": chunk.page_content,
                "source": chunk.metadata.get("source", ""),
                "chunk_id": chunk.metadata.get("chunk_id", -1),
            })

        # 存入实例
        self._indexes[doc_name] = bm25 #BM25Okapi实例
        self._corpus[doc_name] = tokenized #chunk的page_content分词后的列表
        self._chunks[doc_name] = chunk_infos  #原始chunk信息

        print(f"  📇 BM25 索引已构建: {doc_name} ({len(tokenized)} 个 chunk)")

    # ========== 检索 ==========

    def search(
        self,
        query: str,
        top_k: int = 20,
        doc_filter: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        BM25 检索，返回格式与 VectorStoreManager.search() 一致。

        参数:
            query:      查询文本
            top_k:      返回条数
            doc_filter: 只搜指定文档（None = 搜全部）

        返回:
            [
                {
                    "content":       "文本内容...",
                    "document_name": "wenben1.txt",
                    "chunk_id":      5,
                    "source":        "data/raw/wenben1.txt",
                    "score":         12.345,   # BM25 分数（越高越相关）
                },
                ...
            ]
        """
        if doc_filter is not None:
            target_docs = [d for d in doc_filter if d in self._indexes]
        else:
            target_docs = list(self._indexes.keys())

        if not target_docs:
            return []

        all_results = []
        tokenized_query = _tokenize(query) # 分词后的查询文本

        for doc_name in target_docs:
            bm25 = self._indexes.get(doc_name)
            chunks = self._chunks.get(doc_name)
            if bm25 is None or chunks is None:
                continue

            # BM25 打分 eg. [8.1, 1.4, 0.0, 3.2, ...]chunks里面有几个元素scores里面就有几个分数
            scores = bm25.get_scores(tokenized_query)

            # 取每份文档的 top_k
            doc_top_k = min(top_k, len(scores))#最小值
            #sorted对下标排序，排序依据是该下标对应的分数 scores[i]。
            top_indices = sorted(
                range(len(scores)), key=lambda i: scores[i], reverse=True#降序
            )[:doc_top_k]

            for idx in top_indices:
                c = chunks[idx]#_chunk里的原始信息
                all_results.append({
                    "content": c["content"],
                    "document_name": doc_name,
                    "chunk_id": c["chunk_id"],
                    "source": c["source"],
                    "score": float(scores[idx]),
                })

        # 按 BM25 分数降序排列（分数越高越相关）
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k]

    # ========== 持久化（可选）==========

    def save_index(self):
        """将 BM25 索引保存到磁盘（pickle）"""
        self._index_dir.mkdir(parents=True, exist_ok=True)
        for doc_name, bm25 in self._indexes.items():
            filepath = self._index_dir / f"{doc_name}.pkl"
            with open(filepath, "wb") as f:
                pickle.dump({
                    "bm25": bm25,
                    "corpus": self._corpus[doc_name],
                    "chunks": self._chunks[doc_name],
                }, f)
        print(f"  💾 BM25 索引已保存到 {self._index_dir}")

    def load_index(self, doc_name: str) -> bool:
        """从磁盘加载 BM25 索引"""
        filepath = self._index_dir / f"{doc_name}.pkl"
        if not filepath.exists():
            return False
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        self._indexes[doc_name] = data["bm25"]
        self._corpus[doc_name] = data["corpus"]
        self._chunks[doc_name] = data["chunks"]
        return True


# ========== 测试代码 ==========
if __name__ == "__main__":
    from utils.chunker import chunk_document

    file_path = "data/raw/wenben1.txt"
    chunks = chunk_document(file_path)

    retriever = BM25Retriever()
    retriever.index_documents("wenben1.txt", chunks)

    results = retriever.search("主角叫什么名字", top_k=3)
    for i, r in enumerate(results):
        print(f"\n结果{i+1}（BM25分数: {r['score']:.2f}）：")
        print(f"  内容: {r['content'][:120]}...")