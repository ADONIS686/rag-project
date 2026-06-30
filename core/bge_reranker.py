"""
core/bge_reranker.py — c 精排器

职责：
  - 封装 BAAI/bge-reranker-v2-m3 模型
  - 对 RRF 融合后的候选做二次精排
  - 返回重排后的 Top-K Document 列表

用法：
  reranker = BgeReranker()
  top_docs = reranker.rerank(query, candidates, top_k=5)
"""

import os
from typing import List, Dict
from langchain_core.documents import Document


class BgeReranker:
    """BGE 交叉编码器精排器"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self._model_name = model_name
        self._model = None  # 懒加载

    def _load_model(self):
        if self._model is None:
            # 兼容新版 transformers（prepare_for_model 在 5.x 中被移除）
            from transformers import PreTrainedTokenizerBase
            if not hasattr(PreTrainedTokenizerBase, 'prepare_for_model'):
                def _prepare_for_model(self, *args, truncation=True, padding=False, **kwargs):
                    # FlagEmbedding 传的是已 tokenize 的 list[int]，
                    # 先 decode 回文本，再用现代 tokenizer 的 __call__ 编码
                    texts = [
                        self.decode(a, skip_special_tokens=True)
                        if isinstance(a, list) else a
                        for a in args
                    ]
                    return self(
                        texts[0],
                        text_pair=texts[1] if len(texts) > 1 else None,
                        truncation=truncation,
                        padding=padding,
                        **kwargs,
                    )
                PreTrainedTokenizerBase.prepare_for_model = _prepare_for_model
            # 改用本地路径加载，避免连 HuggingFace
            local_base = os.path.join(
                os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface")),
                "hub", "models--BAAI--bge-reranker-v2-m3"
            )
            # 自动找最新 snapshot 目录
            snapshots = os.path.join(local_base, "snapshots")
            model_path = self._model_name  # 默认走在线
            if os.path.isdir(snapshots):
                dirs = sorted(os.listdir(snapshots), reverse=True)
                if dirs:
                    model_path = os.path.join(snapshots, dirs[0])
            from FlagEmbedding import FlagReranker
            print(f"  🔄 正在加载 BGE Reranker 模型（首次使用，约 2GB）...")
            #重排模型对象
            self._model = FlagReranker(model_path, use_fp16=True)
            print(f"  ✅ BGE Reranker 加载完成")
        return self._model

    def rerank(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 5,
    ) -> List[Document]:
        """
        对候选文档精排。

        参数:
          query: 用户问题
          candidates: RRF 融合后的候选列表（每条含 content/document_name/source 字段）
          top_k: 返回条数

        返回:
          重排后的 LangChain Document 列表（按相关性降序）
        """
        if not candidates:
            return []

        model = self._load_model()

        # BGE reranker 有输入长度限制（v2-m3 约 8192 tokens），截断到安全范围
        MAX_CONTENT_LEN = 4096  # 约对应 8192 tokens 的安全线

        # 批量打分：[(query, doc_content), ...]
        pairs = [
            [query[:MAX_CONTENT_LEN], c["content"][:MAX_CONTENT_LEN]]
            for c in candidates
        ]
        #normalize=True 归一化，把所有分数压缩到 0 ~ 1 区间
        scores = model.compute_score(pairs, normalize=True)

        # 按分数降序排列
        ranked = sorted(
            #zip按顺序一一配对，生成 (c, score) 元组迭代器
            zip(candidates, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            Document(
                page_content=c["content"],
                metadata={
                    "source": c.get("source", c.get("document_name", "")),
                    #四舍五入保留 4 位小数。
                    "rerank_score": round(score, 4),
                },
            )
            for c, score in ranked[:top_k]
        ]
