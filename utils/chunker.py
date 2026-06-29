"""
utils/chunker.py — 规则分块器

职责：
  接收 marker_parser.py 的 List[Document]，
  表格/图片原样透传，相邻文本段落合并到 chunk_size 大小。

【为什么不需要内部 split("\\n\\n")】
  marker_parser.py 第93行已经 `text.split("\\n\\n")` 把全文拆成段落级 Document。
  表格/图片因为格式不含 \\n\\n，天然不会被拆碎；
  文本因为段落间自带 \\n\\n，已经被拆成小段。
  所以每个 text Document 的 page_content 已经是「一段话」，
  chunker 不需要再拆，只需要「拼」——把多个短段合并到 chunk_size。

用法：
  from utils.marker_parser import parse_pdf
  from utils.chunker import rule_chunk

  docs = parse_pdf("doc.pdf")
  chunks = rule_chunk(docs, chunk_size=800)
  manager.import_document("doc.pdf", chunks)   # 直接喂给向量库
"""

import sys
from pathlib import Path

# 把项目根目录加入 Python 搜索路径（直接运行这个文件时也能找到 utils.core 等模块）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import List
from langchain_core.documents import Document
from config.settings import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

def rule_chunk(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """
    对 marker 解析结果进行规则分块。

    核心逻辑（"拼接"而非"拆分"）：
      - type="table"  → 直接作为一个独立 chunk（表格拆了没意义）
      - type="image"  → 直接作为一个独立 chunk
      - type="text"   → 把相邻的短文本段落拼接成 chunk_size 大小
                         满了一个 chunk 就落盘，留 overlap 个字符给下一个

    参数:
      documents:    marker_parser.parse_pdf() 的返回值
      chunk_size:   每个 text chunk 的目标长度（字符数）。默认 800。
                    表格和图片不受此限制。
      chunk_overlap: 相邻 chunk 的重叠长度。默认 80。

    返回:
      List[Document]，可直接传给 vector_store_manager.import_document()
    """
    chunks = []              # 最终输出
    chunk_id = 0             # chunk 序号递增
    current_chunk = ""       # 正在攒的文本
    current_source = ""      # 来源文件路径

    for doc in documents:
        content = doc.page_content.strip()
        block_type = doc.metadata.get("block_type", "text")
        source = doc.metadata.get("source", "")

        if not content:
            continue

        # ============================================================
        # 表格 / 图片：先把当前攒的文本段落落盘，再单独存表格/图片
        # ============================================================
        if block_type in ("table", "image"):
            # 如果之前攒了一堆文本，先落盘
            if current_chunk.strip():
                chunks.append(Document(
                    page_content=current_chunk.strip(),
                    metadata={
                        "source": current_source,
                        "block_type": "text",
                        "chunk_id": chunk_id,
                    }
                ))
                chunk_id += 1
                current_chunk = ""   # 清空，准备攒下一批

            # 表格/图片直接作为一个独立 chunk
            chunks.append(Document(
                page_content=content,
                metadata={
                    **doc.metadata,
                    "chunk_id": chunk_id,
                }
            ))
            chunk_id += 1
            continue

        # ============================================================
        # 文本段落：往 current_chunk 里攒，满了就落盘
        # ============================================================
        current_source = source or current_source

        # 如果当前段落加上去不超过 chunk_size，直接拼接
        if len(current_chunk) + len(content) <= chunk_size:
            current_chunk += content + "\n\n"
        else:
            # 满了，先把当前 chunk 落盘
            if current_chunk.strip():
                chunks.append(Document(
                    page_content=current_chunk.strip(),
                    metadata={
                        "source": current_source,
                        "block_type": "text",
                        "chunk_id": chunk_id,
                    }
                ))
                chunk_id += 1
                # 重叠机制：上一个 chunk 末尾留 overlap 个字符
                overlap_text = (
                    current_chunk[-chunk_overlap:]
                    if len(current_chunk) > chunk_overlap
                    else ""
                )
                current_chunk = ""
            else:
                overlap_text = ""
            # 如果新段落本身就超过 chunk_size，当场强制拆分成多个 chunk
            if len(content) > chunk_size:
                for i in range(0, len(content), chunk_size - chunk_overlap):
                    sub = content[i:i + chunk_size]
                    prefix = overlap_text if i == 0 else ""
                    chunks.append(Document(
                        page_content=prefix + sub,
                        metadata={
                            "source": current_source,
                            "block_type": "text",
                            "chunk_id": chunk_id,
                        }
                    ))
                    chunk_id += 1
                current_chunk = ""  # 已经全部落盘，不需要攒着了
            else:
                # 段落本身不超长，放到 current_chunk 里，带上 overlap
                current_chunk = overlap_text + content + "\n\n"

    # ================================================================
    # 最后一片：如果还有没落盘的文本，收尾
    # ================================================================
    if current_chunk.strip():
        chunks.append(Document(
            page_content=current_chunk.strip(),
            metadata={
                "source": current_source,
                "block_type": "text",
                "chunk_id": chunk_id,
            }
        ))

    return chunks


def semantic_chunk(
    documents: List[Document],
    embedding_model=None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    similarity_threshold: float = 0.5,
) -> List[Document]:
    """
    基于 Embedding 相似度的语义自适应分块。
    
    核心：用 embedding 算相邻段落相似度，低于阈值就断开。
         表格/图片原样透传。
    """
    import numpy as np

    if embedding_model is None:
        from langchain_community.embeddings import DashScopeEmbeddings
        from config.settings import DASHSCOPE_API_KEY, EMBEDDING_MODEL_NAME
        embedding_model = DashScopeEmbeddings(
            model=EMBEDDING_MODEL_NAME,
            dashscope_api_key=DASHSCOPE_API_KEY,
        )

    # 第 0 步：TXT 全文按空行拆段落（对齐 PDF 的段落粒度）
    text_docs = [d for d in documents if d.metadata.get("block_type", "text") == "text"]
    if len(text_docs) == 1 and len(text_docs[0].page_content) > 500:
        big_doc = text_docs[0]
        paragraphs = []
        for p in big_doc.page_content.split("\n\n"):
            p = p.strip()
            if not p or len(p) < 5:
                continue
            # 超长段落：在句末标点处智能切分，避免断在句子中间
            if len(p) > 2000:
                start = 0
                while start < len(p):
                    end = min(start + 2000, len(p))
                    if end < len(p):
                        for sep in ("。", "！", "？", "\n"):
                            #rfind = reverse find，从右往左反向查找子串，返回子串第一次出现的下标；找不到返回 -1。
                            pos = p.rfind(sep, start, end)
                            if pos > start + 1000:
                                end = pos + 1
                                break
                    sub = p[start:end].strip()
                    if sub and len(sub) >= 5:
                        paragraphs.append(sub)
                    start = end
            else:
                paragraphs.append(p)
        documents = [
            Document(page_content=p, metadata={**big_doc.metadata, "block_type": "text"})
            for p in paragraphs
        ]

    # 第 1 步：区分文本和特殊块
    text_cache = []         # [(index_in_documents, content)]
    special_cache = []      # [(index_in_documents, doc)]
    for i, doc in enumerate(documents):
        if not doc.page_content.strip():
            continue
        bt = doc.metadata.get("block_type", "text")
        if bt in ("table", "image"):
            special_cache.append((i, doc))
        else:
            text_cache.append((i, doc.page_content.strip()))


    if not text_cache:
        return rule_chunk(documents)

    # 第 2 步：批量算 embedding
    texts_only = [t[:2048] for _, t in text_cache]
    #embedding_model.embed_documents把文本转为多维向量，输出一个元素是多维向量的列表（本质嵌套列表）
    #最终转为 numpy 数组，方便后续计算余弦相似度
    text_vectors = np.array(embedding_model.embed_documents(texts_only))

    # 第 3 步：相邻相似度 → 标记断点
    split_after = set()
    for j in range(len(text_vectors) - 1):
        v1, v2 = text_vectors[j], text_vectors[j + 1]
        cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
        if cos < similarity_threshold:
            split_after.add(j)  # 在第 j 段后断开

    # 第 4 步：按断点分组，组内用规则拼接
    chunks = []
    chunk_id = 0
    special_ptr = 0
    current_chunk = ""
    current_source = ""

    def flush():
        #变量 chunk_id 不在当前 flush() 函数内部定义，也不是全局变量，而是外层包裹函数 semantic_chunk 里定义的局部变量。
        nonlocal chunk_id
        if current_chunk.strip():
            chunks.append(Document(
                page_content=current_chunk.strip(),
                metadata={"source": current_source, "block_type": "text", "chunk_id": chunk_id},
            ))
            chunk_id += 1

    for group_start in range(len(text_cache)):
        # 输出 special blocks that appear before this text
        while special_ptr < len(special_cache) and special_cache[special_ptr][0] < text_cache[group_start][0]:
            _, sp_doc = special_cache[special_ptr]
            #把手里正在积攒的文本current_chunk落盘生成 chunk
            flush()
            current_chunk = ""
            #把表格 / 图片单独作为一个 chunk 存入结果列表。
            chunks.append(Document(
                page_content=sp_doc.page_content.strip(),
                metadata={**sp_doc.metadata, "chunk_id": chunk_id},
            ))
            chunk_id += 1
            special_ptr += 1

        _, content = text_cache[group_start]
        current_source = documents[text_cache[group_start][0]].metadata.get("source", "")

        # 当前段落 + 当前缓存不超 → 追加
        if len(current_chunk) + len(content) <= chunk_size:
            current_chunk += content + "\n\n"
        else:
            flush()
            overlap = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else ""
            current_chunk = overlap + content + "\n\n"

        # 遇到断点 → flush
        if group_start in split_after:
            flush()
            current_chunk = ""

    flush()  # 最后一片

    # 尾部剩余的特殊块
    while special_ptr < len(special_cache):
        _, sp_doc = special_cache[special_ptr]
        flush()
        current_chunk = ""
        chunks.append(Document(
            page_content=sp_doc.page_content.strip(),
            metadata={**sp_doc.metadata, "chunk_id": chunk_id},
        ))
        chunk_id += 1
        special_ptr += 1

    return chunks



# ========== 便捷函数：一键分块 ==========

def chunk_document(file_path: str, chunk_size: int = 800) -> List[Document]:
    """
    一步完成：Marker 解析 → 规则分块。

    参数:
      file_path:  PDF 或 TXT 文件路径
      chunk_size: text chunk 目标大小

    返回:
      List[Document]，可直接传给 vector_store_manager
    """
    from utils.marker_parser import parse_document

    docs = parse_document(file_path)
    return rule_chunk(docs, chunk_size=chunk_size)


# ========== 测试代码 ==========
if __name__ == "__main__":
    file_path = "data/raw/wenben2.pdf"
    chunks = chunk_document(file_path)

    print(f"\n✅ 分块完成！共 {len(chunks)} 个 chunk：\n")

    # 统计各类型数量
    from collections import Counter
    #Counter自动数每个元素出现了多少次，返回一个 dict {元素: 出现次数}
    type_counts = Counter(c.metadata.get("block_type", "?") for c in chunks)
    #.items()：一组一组拿出 (键, 值) 元组，方便格式化输出
    for t, n in type_counts.items():
        print(f"  {t}: {n} 个")

    # 打印前 3 个预览
    print("\n--- 前 3 个 chunk 预览 ---")
    for c in chunks[:3]:
        preview = c.page_content[:120].replace("\n", "\\n")
        cid = c.metadata.get("chunk_id", "?")
        ctype = c.metadata.get("block_type", "?")
        print(f"\n[chunk_id={cid}] [type={ctype}]")
        print(f"  {preview}...")
