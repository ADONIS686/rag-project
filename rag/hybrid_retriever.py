"""
rag/hybrid_retriever.py — 混合检索器（BM25 + 向量 + RRF 融合）

职责：
  - 组合 BM25Retriever + VectorStoreManager
  - 用 RRF（Reciprocal Rank Fusion）融合两类结果
  - 提供 BaseRetriever 接口，无缝接入 LangChain 管道

用法：
  retriever = HybridRetriever(manager, bm25, top_k=20)
  docs = retriever.invoke("主角叫什么名字")
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.vector_store_manager import VectorStoreManager
from core.bm25_retriever import BM25Retriever
from core.bge_reranker import BgeReranker
from typing import List, Dict, Optional
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document


def _rrf_fusion(
    results_a: List[Dict],
    results_b: List[Dict],
    top_k: int = 20,
    k: int = 60,
) -> List[Dict]:
    """
    RRF（Reciprocal Rank Fusion）融合算法。

    原理：
      - 对两组结果分别按排名打分：rrf_score = 1 / (k + rank)
      - rank 从 1 开始，k=60 是论文推荐默认值
      - 同一文档出现在两边时，分数相加
      - 最终按 rrf_score 降序排列

    参数:
        results_a: 第一组结果列表（每条含 score 字段）
        results_b: 第二组结果列表（每条含 score 字段）
        top_k:     最终返回条数
        k:         RRF 平滑参数（默认 60）

    返回:
        融合后的结果列表
    """
    # 用 content 做去重 key
    rrf_scores: Dict[str, Dict] = {}

    # 处理第一组
    for rank, item in enumerate(results_a, start=1):
        key = item["content"][:200]  # 用内容前200字做唯一标识
        rrf = 1.0 / (k + rank)
        if key in rrf_scores:
            rrf_scores[key]["rrf_score"] += rrf
            rrf_scores[key]["sources"].add(item.get("document_name", ""))
        else:
            rrf_scores[key] = {
                "content": item["content"],
                "document_name": item.get("document_name", ""),
                "chunk_id": item.get("chunk_id", -1),
                "source": item.get("source", ""),
                "rrf_score": rrf,
                "sources": {item.get("document_name", "")},
            }

    # 处理第二组
    for rank, item in enumerate(results_b, start=1):
        key = item["content"][:200]
        rrf = 1.0 / (k + rank)
        if key in rrf_scores:
            rrf_scores[key]["rrf_score"] += rrf
            rrf_scores[key]["sources"].add(item.get("document_name", ""))
        else:
            rrf_scores[key] = {
                "content": item["content"],
                "document_name": item.get("document_name", ""),
                "chunk_id": item.get("chunk_id", -1),
                "source": item.get("source", ""),
                "rrf_score": rrf,
                "sources": {item.get("document_name", "")},
            }

    # 排序 + 取 top_k
    merged = sorted(
        rrf_scores.values(),
        key=lambda x: x["rrf_score"],
        reverse=True,
    )
    return merged[:top_k]


class HybridRetriever(BaseRetriever):
    """
    混合检索器（BM25 + 向量），LangChain 兼容。

    架构:
        invoke(query)
          ├─→ BM25Retriever.search(query)      → bm25_results
          ├─→ VectorStoreManager.search(query)  → vector_results
          └─→ RRF Fusion                       → merged_docs
    """

    def __init__(
        self,
        manager: VectorStoreManager,      # VectorStoreManager 实例
        bm25: BM25Retriever,              # BM25Retriever 实例
        top_k: int = 20,
        doc_filter: Optional[List[str]] = None,
    ):
        super().__init__()
        self._manager = manager
        self._bm25 = bm25
        self._top_k = top_k
        self._reranker = None  # BGE 精排器（懒加载）
        self._doc_filter = doc_filter

    def _get_relevant_documents(self, query: str) -> List[Document]:
        """
        混合检索：BM25 + 向量 → RRF 融合 → Document 列表
        """
        # ① BM25 关键词检索
        bm25_results = self._bm25.search(
            query, top_k=self._top_k, doc_filter=self._doc_filter
        )

        # ② 向量检索
        vector_results = self._manager.search(
            query, top_k=self._top_k, doc_filter=self._doc_filter
        )

        # ③ RRF 融合
        merged = _rrf_fusion(bm25_results, vector_results, top_k=max(20, self._top_k))

        # ④ BGE 精排
        if self._reranker is None:
            self._reranker = BgeReranker()
        return self._reranker.rerank(query, merged, top_k=self._top_k)
