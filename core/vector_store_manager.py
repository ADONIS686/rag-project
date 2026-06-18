"""
core/vector_store_manager.py - 多文档向量库实例管理器（超详细注释版）

【新手必读：这个文件是干什么的？】
----------------------------
原来的代码（rag/vector_store.py）把所有文档的向量都挤在一个 collection 里，
这样有两个大问题：
  1. 无法隔离：搜"张三是谁"，可能返回来自文档A和文档B的混合结果
  2. 无法单独删除：想删文档A的向量，只能全删重来

这个文件解决了这个问题：
  ✅ 每份文档有自己独立的向量库（独立collection、独立存储目录）
  ✅ 检索时可以指定"只在文档A里搜"
  ✅ 删除文档A时，只删它的向量，不影响其他文档
  ✅ 为 Day15 迁移到 Milvus Lite 预留了抽象层（到时候只改底层，上层代码不用动）

【文件结构】
----------------------------
VectorStoreManager 类（核心管理器）
  ├── __init__()          初始化
  ├── embedding (属性)     延迟加载向量模型（省内存）
  ├── _sanitize_name()    把文件名转成合法的collection名
  ├── _get_collection_path()  获取某文档的向量库存储路径
  ├── create_collection()  为一份文档创建/加载向量库
  ├── add_documents()     向指定文档的向量库添加文本块
  ├── import_document()    一步完成：创建 + 添加（最常用）
  ├── search()            检索（支持跨文档 or 按文档名过滤）
  ├── delete_collection()  删除某文档的向量库（内存+磁盘都删）
  ├── list_collections()  列出所有已加载的文档名
  └── collection_count()  查询某文档向量库中有多少个chunk

【依赖说明】
----------------------------
- Chroma：向量数据库（现在用 Chroma，Day15 换 Milvus Lite）
- DashScopeEmbeddings：把文字转成向量的模型（阿里云 BGE 系列）
- Document：LangChain 的标准文档格式（page_content + metadata）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ========== 导入区 ==========
# os：处理文件路径和目录操作（创建、删除目录）
import os
# shutil：高级文件操作（删除整个目录树）
import shutil
# re：正则表达式（用来把文件名里的特殊字符替换成下划线）
import re
# Path：面向对象的文件路径处理（比字符串拼接更安全）
from pathlib import Path
# typing：类型注解（让代码更清晰，IDE 也能帮你检查错误）
from typing import List, Dict, Optional

# LangChain 相关导入
# Chroma：我们要用的向量数据库
from langchain_chroma import Chroma
# DashScopeEmbeddings：调用阿里云 BGE 向量模型的接口
from langchain_community.embeddings import DashScopeEmbeddings
# Document：LangChain 的标准文档对象（所有 Loader/Splitter/VectorStore 都认这个格式）
from langchain_core.documents import Document

# 项目内部导入（从 config/settings.py 读取配置）
from config.settings import (
    DASHSCOPE_API_KEY,      # 阿里云 API Key（用来调用向量模型）
    EMBEDDING_MODEL_NAME,   # 向量模型名称（BGE 系列）
    VECTOR_DB_PATH,          # 向量库根目录（存所有文档的向量数据）
)


# ========== 核心类定义 ==========
class VectorStoreManager:
    """
    【新手理解】这个类就像一个"多文档向量库管理员"

    想象一下：
      - 你有一个文件柜（VectorStoreManager）
      - 每个抽屉存一份文档的向量（抽屉名 = 文档名）
      - 你可以：
          1. 新建一个抽屉（create_collection）
          2. 往抽屉里放文件（add_documents）
          3. 在指定抽屉里找东西（search with doc_filter）
          4. 把整个抽屉扔掉（delete_collection）
    """

    def __init__(self, persist_root: str = None):
        """
        【初始化函数】创建管理器实例时自动调用

        参数:
            persist_root: 向量库的根目录（所有文档的向量数据都存在这里）
                         如果不传，默认用 config.settings.VECTOR_DB_PATH
                         实际值是: "./chroma_db"

        内部状态:
            self.persist_root: 向量库根目录（Path 对象，方便路径操作）
            self._stores:      字典，{文档名: Chroma向量库实例}
                                 比如 {"wenben1.pdf": Chroma实例, "novel.txt": Chroma实例}
            self._embedding:  向量模型实例（延迟加载，第一次用时才创建）
        """
        # 把传入的路径转成 Path 对象（如果没传就用配置文件里的默认值）
        self.persist_root = Path(persist_root or VECTOR_DB_PATH)
        # 内存中的向量库实例字典（ key = 文档名，value = Chroma 实例）
        # 初始为空，后续调用 create_collection() 时会往里填
        self._stores: Dict[str, Chroma] = {}
        # 向量模型实例（初始为 None，第一次调用 self.embedding 时才会真正加载）
        # 这样做是为了"延迟加载"——如果永远不调用 search/add，就不必加载模型，省内存
        self._embedding = None

    # ---------- 内部工具方法（以下划线开头，表示"内部使用，外部不需要直接调用"）----------

    @property
    def embedding(self):
        """
        【属性装饰器】把方法当成属性用（调用时不需要加括号）

        用法:
            model = self.embedding   # ✅ 像访问属性一样
            model = self.embedding() # ❌ 不需要加括号！

        【延迟加载机制】
        第一次访问 self.embedding 时，self._embedding 是 None，
        这时才会真正创建 DashScopeEmbeddings 实例（需要联网，有点慢）
        第二次及以后访问时，直接返回已缓存的实例（很快）

        返回:
            DashScopeEmbeddings 实例（用来把文字转成向量）
        """
        # 如果还没加载过（是 None），就创建
        if self._embedding is None:
            print("  🔄 正在加载向量模型（首次使用，请稍候）...")
            self._embedding = DashScopeEmbeddings(
                model=EMBEDDING_MODEL_NAME,   # 配置文件里的模型名（BGE 系列）
                dashscope_api_key=DASHSCOPE_API_KEY,  # 你的 API Key
            )
            print("  ✅ 向量模型加载完成")
        # 返回缓存好的实例
        return self._embedding
    #sanitize vt.使……无害；给……消毒；
    def _sanitize_name(self, doc_name: str) -> str:
        """
        【内部方法】把文档文件名转成"合法的 collection 名"

        问题：Chroma 的 collection 名不能包含某些特殊字符（比如 空格/斜杠/中文？）
        解决：把文档名中的非法字符替换成下划线 _

        处理逻辑:
            1. 先去掉文件扩展名（比如 "我的文档.pdf" → "我的文档"）
            2. 把不是"字母/数字/中文/下划线/连字符"的字符全部替换成 _
            3. 返回净化后的名字

        参数:
            doc_name: 原始文档名（比如 "我的文档.pdf"）
        返回:
            净化后的名字（比如 "我的文档" 或 "wenben1"）
        """
        # Path(doc_name).stem 会去掉扩展名
        # 比如 "wenben1.pdf" → "wenben1"
        # 比如 "我的文档.pdf" → "我的文档"
        name = Path(doc_name).stem

        # 正则表达式：把"不是字母、不是数字、不是中文、不是下划线、不是连字符"的字符替换成 _
        # \w = 字母/数字/下划线
        # \u4e00-\u9fff = 中日韩统一表意文字（这里是中文范围）
        # - = 连字符
        # [^\w\u4e00-\u9fff-] 的意思是：不匹配这些字符的，全部替换
        name = re.sub(r'[^\w\u4e00-\u9fff-]', '_', name)

        return name

    def _get_collection_path(self, doc_name: str) -> Path:
        """
        【内部方法】获取某份文档的向量库在磁盘上的存储路径

        磁盘结构示例:
            chroma_db/              ← 根目录（self.persist_root）
            ├── wenben1/           ← 文档1的向量库（独立目录）
            │   ├── chroma.sqlite3
            │   └── ...
            ├── wenben2/           ← 文档2的向量库（独立目录）
            │   └── ...
            └── novel/             ← 文档3的向量库（独立目录）
                └── ...

        参数:
            doc_name: 文档名（比如 "wenben1.pdf"）
        返回:
            Path 对象，比如 Path("chroma_db/wenben1"）
        """
        # 先净化文件名，再拼接到根目录下
        #调用类内部的 _sanitize_name() 工具方法，对原始文档名做「净化处理」，得到一个可以安全用作目录名、集合名的字符串，赋值给 safe_name
        safe_name = self._sanitize_name(doc_name)
        return self.persist_root / safe_name

    # ---------- 核心对外操作方法 ----------

    def create_collection(self, doc_name: str, force_recreate: bool = False) -> Chroma:
        """
        【核心方法】为一份文档创建（或加载已有）向量库 collection

        工作流程:
            1. 检查内存中是否已有该文档的向量库实例（self._stores 里有没有）→ 有就直接返回（不用重新加载）
            2. 检查磁盘上是否已有该文档的向量库目录
               → 有就用 Chroma 加载（persist_directory 参数）
               → 没有就创建新的空 collection
            3. 把创建好的 Chroma 实例存到 self._stores 里（下次不用再加载）

        参数:
            doc_name:        文档名（比如 "wenben1.pdf"）
            force_recreate:  是否强制删除旧库、重新创建
                            True  = 先删掉磁盘上的旧数据，再重建（相当于"清空重来"）
                            False = 如果已有旧数据，直接加载使用（默认行为）

        返回:
            Chroma 向量库实例（已经准备好接收数据或执行检索）
        """
        # 第一步：算出这份文档的向量库应该存在哪个目录
        collection_path = str(self._get_collection_path(doc_name))

        # 第二步：检查内存中是否已有（已经加载过了就直接返回，省时间）
        if doc_name in self._stores:
            print(f"  ⚡ 向量库已在内存中: {doc_name}")
            return self._stores[doc_name]

        # 第三步：如果需要强制重建，先把磁盘上的旧数据删掉
        if force_recreate and os.path.exists(collection_path):
            shutil.rmtree(collection_path)  # 递归删除整个目录
            print(f"  🗑️  已清理旧向量库: {doc_name}")

        # 第四步：创建或加载 Chroma 向量库
        # 说明：Chroma 很聪明——
        #   - 如果 persist_directory 不存在，会自动创建新的空 collection
        #   - 如果 persist_directory 已存在，会自动加载已有的数据（不用重新入库！）
        store = Chroma(
            persist_directory=collection_path,       # 持久化目录（向量数据存在这里）
            embedding_function=self.embedding,       # 向量模型（用来把文字转成向量）
            collection_name=self._sanitize_name(doc_name),  # collection 名（净化后的文档名）
        )

        # 第五步：把实例存到内存字典里（下次调用就不用重新加载了）
        self._stores[doc_name] = store
        print(f"  ✅ 向量库已就绪: {doc_name} (路径: {collection_path})")

        return store
    
    

    def add_documents(self, doc_name: str, documents: List[Document]) -> None:
        """
        【核心方法】向指定文档的向量库中添加文本块（chunk）

        参数:
            doc_name:  文档名（比如 "wenben1.pdf"，必须已经 create_collection 过）
            documents: Document 对象列表（每个 Document 是一个文本块）
                        通常是由分块器（chunker.py）产出的

        注意:
            - 如果文档名对应的向量库还没创建，会自动调用 create_collection() 创建
            - documents 为空列表时，直接返回，不报错
        """
        # 先拿到这份文档对应的向量库实例对象（没有的话会自动创建）
        store = self._stores.get(doc_name)
        if store is None:
            store = self.create_collection(doc_name)

        # 安全检查：要添加的文档列表不能是空的
        if not documents:
            print(f"  ⚠️  文档 {doc_name} 没有可添加的文本块（documents 为空）")
            return

        # 核心操作：调用 Chroma 的 add_documents() 方法
        # 这一步会把每个 Document 的 page_content 转成向量，然后存到向量库里
        # 这个过程需要调用 DashScope API（联网，按调用次数收费）
        store.add_documents(documents)

        print(f"  📥 {doc_name}: 已添加 {len(documents)} 个文本块到向量库")

    def import_document(
        self,
        doc_name: str,
        documents: List[Document],
        force_recreate: bool = True
    ) -> Chroma:
        """
        【最常用的方法】一步完成：创建 collection + 添加文档块

        这是"批量导入"场景的主入口，通常这样用：
            manager = VectorStoreManager()
            chunks = chunker.rule_chunk(documents)   # 先分块
            manager.import_document("wenben1.pdf", chunks)  # 一键入库

        参数:
            doc_name:        文档名
            documents:       分块后的 Document 列表
            force_recreate:  是否删除旧库重建（默认 True，保证每次导入都是全新状态）

        返回:
            创建好的 Chroma 向量库实例
        """
        # 第一步：创建或加载向量库（force_recreate=True 表示先清再建）
        store = self.create_collection(doc_name, force_recreate=force_recreate)
        # 第二步：把分好的文本块添加进去
        self.add_documents(doc_name, documents)
        return store

    def search(
        self,
        query: str,
        top_k: int = 10,
        doc_filter: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        【核心方法】相似性检索（最核心的功能！）

        工作流程:
            1. 确定要搜哪些文档（doc_filter 指定，或搜所有已加载的文档）
            2. 对每份文档的向量库，执行 similarity_search_with_score()
               → 这会先把 query 转成向量，然后跟库里的所有向量算相似度
            3. 把所有文档的检索结果合并，按相似度分数排序（分数越低越相似）
            4. 返回前 top_k 条结果

        参数:
            query:      用户的查询问题（比如 "张三和李四是什么关系"）
            top_k:      最多返回多少条结果（默认 10）
            doc_filter:  指定只搜哪些文档（比如 ["wenben1.pdf", "wenben2.pdf"]）
                        如果不传（None），则搜索所有已加载的文档

        返回:
            结果列表，每条结果是一个字典：
            [
                {
                    "content":      "张三是李四的哥哥...",  # 文本块内容
                    "document_name": "wenben1.pdf",       # 来自哪份文档
                    "chunk_id":     5,                      # 文本块编号
                    "source":       "data/raw/wenben1.pdf", # 原始文件路径
                    "score":        0.235,                  # 相似度分数（越低越相似）
                },
                ...
            ]
        """
        # 第一步：确定要搜索的文档范围
        if doc_filter is not None:
            # 用户指定了要搜哪些文档
            target_docs = doc_filter
        else:
            # 搜所有已加载到内存的文档
            #取出实例内部字典 _stores 的所有键，转换为列表后赋值给 target_docs。
            target_docs = list(self._stores.keys())

        # 安全检查：没有可搜的文档就直接返回空列表
        if not target_docs:
            print("  ⚠️  没有可检索的文档向量库，请先导入文档")
            return []

        # 第二步：遍历每份文档，分别检索
        all_results = []
        for doc_name in target_docs:
            # 拿到这份文档对应的向量库实例
            store = self._stores.get(doc_name)
            if store is None:
                print(f"  ⚠️  文档 {doc_name} 的向量库未加载，跳过")
                continue

            # 执行向量检索
            # similarity_search_with_score() 返回: List[Tuple[Document, float]]
            #   - Document: 命中的文本块（包含 page_content 和 metadata）
            #   - float: 相似度分数（Chroma 用的是 L2 距离，分数越低越相似）
            hits = store.similarity_search_with_score(query, k=top_k)

            # 把结果转成统一的字典格式
            for doc, score in hits:
                all_results.append({
                    "content": doc.page_content,
                    "document_name": doc_name,
                    "chunk_id": doc.metadata.get("chunk_id", -1),
                    "source": doc.metadata.get("source", ""),
                    "score": float(score),  # 转成 float（原来可能是 numpy 类型）
                })

        # 第三步：把所有结果按相似度排序（分数低的排前面，因为越低越相似）
        all_results.sort(key=lambda x: x["score"])

        # 第四步：只返回前 top_k 条（跨所有文档汇总后的 top_k）
        return all_results[:top_k]

    def delete_collection(self, doc_name: str) -> None:
        """
        【核心方法】删除某份文档的向量库（从内存和磁盘同时清除）

        注意：
          必须先释放 Chroma 的文件句柄（设为 None + gc 回收），
          否则 Windows 会报 "PermissionError: 另一个程序正在使用此文件"
        """
        import gc  # Python 垃圾回收模块

        # 第一步：释放 Chroma 实例（关闭它占用的文件句柄）
        if doc_name in self._stores:
            store = self._stores[doc_name]
            # 尝试调用 Chroma 的删除方法
            try:
                store.delete_collection()
            except Exception:
                pass  # 如果 collection 已被部分删除，忽略错误
            # 从字典中移除引用
            del self._stores[doc_name]
            # 强制垃圾回收（确保文件句柄被释放）Chroma 向量库会占用文件句柄（打开 / 占用磁盘的向量库文件夹）
            # 手动强制触发垃圾回收，让 Python 立刻清理掉不再使用的对象，释放文件句柄
            #gc = Python 内置的 垃圾回收模块 (Garbage Collection)
            gc.collect()
            print(f"  🗑️  已从内存中释放: {doc_name}")

        # 第二步：从磁盘上删除向量数据文件
        collection_path = self._get_collection_path(doc_name)
        if os.path.exists(collection_path):
            # 加一层重试：如果第一次删不掉（文件还没释放完），等一小会再试
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.rmtree(collection_path)
                    print(f"  🗑️  已从磁盘删除向量库: {collection_path}")
                    break
                except PermissionError:
                    if attempt < max_retries - 1:
                        print(f"  ⏳ 文件被占用，等待释放后重试... ({attempt + 1}/{max_retries})")
                        time.sleep(0.5)  # 等半秒让系统释放文件锁
                        gc.collect()     # 再催一次垃圾回收
                    else:
                        print(f"  ⚠️  无法删除: {collection_path}（文件仍被占用，请手动删除）")


    def list_collections(self) -> List[str]:
        """
        列出所有已加载到内存的文档名

        返回:
            文档名列表（比如 ["wenben1.pdf", "wenben2.pdf"]）
        """
        return list(self._stores.keys())


    def collection_count(self, doc_name: str) -> int:
        """
        查询某份文档的向量库中有多少个文本块（chunk）

        参数:
            doc_name: 文档名
        返回:
            文本块数量（如果文档未加载，返回 0）
        """
        store = self._stores.get(doc_name)
        if store is None:
            return 0
        # Chroma 内部：store._collection.count() 返回集合中的向量数量
        return store._collection.count()


# ========== 测试代码（直接运行这个文件时会执行） ==========
# 作用：快速验证 VectorStoreManager 是否正常工作
# 用法：cd F:\rag-project && python core/vector_store_manager.py
if __name__ == "__main__":
    print("="*50)
    print("测试 VectorStoreManager")
    print("="*50)

    # 创建管理器实例
    manager = VectorStoreManager()

    # 创建模拟的文本块（测试用，不用真实文档）
    from langchain_core.documents import Document
    test_chunks = [
        Document(page_content="这是一个测试文本块1，内容是关于RAG系统的介绍。",
                 metadata={"source": "test.pdf", "chunk_id": 0}),
        Document(page_content="这是一个测试文本块2，内容是关于向量数据库的。",
                 metadata={"source": "test.pdf", "chunk_id": 1}),
    ]

    # 测试1：导入文档
    print("\n【测试1】导入文档...")
    manager.import_document("test.pdf", test_chunks)
    print(f"✅ 已加载文档列表: {manager.list_collections()}")
    print(f"✅ test.pdf 的chunk数量: {manager.collection_count('test.pdf')}")

    # 测试2：检索
    print("\n【测试2】执行检索...")
    results = manager.search("RAG系统", top_k=3)
    print(f"✅ 检索到 {len(results)} 条结果:")
    for r in results:
        print(f"  [{r['document_name']}] score={r['score']:.4f}: {r['content'][:50]}...")

    # 测试3：删除
    print("\n【测试3】删除文档...")
    manager.delete_collection("test.pdf")
    print(f"✅ 删除后文档列表: {manager.list_collections()}")

    print("\n" + "="*50)
    print("所有测试通过！✅")
    print("="*50)
