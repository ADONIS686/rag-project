"""
utils/marker_parser.py - 基于 Marker 的文档解析器（超详细注释版）

【新手必读：这个文件是干什么的？】
--------------------------------
RAG 系统的第一步永远是"把文档读进来"。
原来用 PyPDFLoader 读 PDF，但它有几个硬伤：
  1. 表格被拆成零散的文字行，列的对应关系全丢了
  2. 图片直接丢弃，文档里的图表、截图全没了
  3. 双栏 PDF、竖排中文排版经常读乱

Marker 是专门解决这些问题的：
  ✅ 表格保留完整的行列结构（markdown 表格格式）
  ✅ 图片自动标注位置（比如 "[图片1：系统架构图]"）
  ✅ 中文支持好，排版不乱

【这个文件的结构】
----------------
  parse_pdf_with_marker()  →  用 Marker 解析 PDF
  parse_txt_file()         →  用 TextLoader 解析 TXT
  parse_document()         →  统一入口：根据后缀自动选解析器

【数据流向】
  磁盘上 PDF 文件
    → marker.converters.pdf.PdfConverter（Marker 引擎）
    → marker 输出（markdown 文本 + 图片信息）
    → 按空行拆成段落
    → 每个段落转成一个 LangChain Document 对象
    → 返回 Document 列表（下一步交给 chunker 分块）
"""

# ========== 导入区 ==========
# os：操作系统相关功能（检查文件是否存在、获取文件名等）
import os
# Path：面向对象的文件路径处理（比字符串拼接更安全、更易读）
from pathlib import Path
# List：类型注解用（告诉读者"这个函数返回一个列表，列表里都是 Document"）
from typing import List
# Document：LangChain 的标准文档格式
#   每个 Document 包含两部分：
#     page_content：文档的文字内容（字符串）
#     metadata：    元信息字典（比如来源文件、页码、块类型等）
from langchain_core.documents import Document


# ========== 函数1：用 Marker 解析 PDF ==========
def parse_pdf_with_marker(file_path: str) -> List[Document]:
    """
    【核心函数】用 Marker 解析 PDF 文件，返回结构化的 Document 列表

    【工作流程】
      1. 导入 Marker 的三个核心组件（延迟导入，不用时不加载）
      2. 初始化 PdfConverter（Marker 的 PDF 转换引擎）
      3. 把 PDF 丢给 converter，得到解析结果
      4. 从结果中提取 markdown 文本
      5. 按空行把文本拆成段落
      6. 识别每个段落的类型（文本/表格/图片）
      7. 每个段落包装成一个 Document 对象

    【参数】
      file_path: PDF 文件的完整路径（比如 "data/raw/wenben2.pdf"）

    【返回】
      Document 对象列表，每个 Document 代表文档中的一个"块"
      每个 Document 的 metadata 里包含：
        - source:     源文件路径（原始 PDF 在哪里）
        - block_type: 块类型，三种可能：
                      "text"  → 普通文本段落
                      "table" → 表格（内容是 markdown 表格，以 | 开头结尾）
                      "image" → 图片标注（内容是 "![图片X：描述]"）
        - chunk_id:   块编号（从 0 开始，按出现顺序递增）
    """
    # ---------- 延迟导入 Marker ----------
    # 为什么要延迟导入？
    #   因为 Marker 依赖 PyTorch（2-3GB），加载很慢
    #   如果这个文件只是被 import（比如其他模块想用 parse_document 函数），
    #   但用户可能只需要解析 TXT 文件，根本用不到 Marker
    #   这时如果一上来就 import marker，白白等好几秒
    #
    # 所以把 import 写在函数内部，只在真正调用 parse_pdf_with_marker() 时才加载
    try:
        # PdfConverter：Marker 的核心引擎，负责把 PDF 转成结构化输出
        from marker.converters.pdf import PdfConverter
        # create_model_dict：创建 Marker 需要的 AI 模型字典（OCR、布局分析等）
        from marker.models import create_model_dict
        # text_from_rendered：从 Marker 的渲染结果中提取文本 + 图片信息
        from marker.output import text_from_rendered
    except ImportError as e:
        # 如果 Marker 没装，抛出清晰的错误提示
        # 用户一看就知道是缺依赖，而不是代码写错了
        raise ImportError(
            "❌ Marker 未安装！请先执行:\n"
            "  pip install marker-pdf -i https://pypi.tuna.tsinghua.edu.cn/simple\n"
            f"  原始错误: {e}"
        )

    # ---------- 开始解析 ----------
    # 打印进度，让用户知道正在处理哪个文件
    # os.path.basename() 从完整路径中提取文件名
    #   比如 "data/raw/wenben2.pdf" → "wenben2.pdf"
    print(f"  🔍 Marker 正在解析: {os.path.basename(file_path)}")

    # 把文件路径转成绝对路径（防止后续操作因相对路径出错）
    # Path(file_path).resolve() 会把相对路径补全为绝对路径
    #   比如 "data/raw/../raw/wenben2.pdf" → "F:/rag-project/data/raw/wenben2.pdf"
    file_path = str(Path(file_path).resolve())

    # 创建 Marker 转换器
    # create_model_dict() 会初始化多个 AI 模型：
    #   - OCR 模型：识别 PDF 中的文字（处理扫描件/图片型 PDF）
    #   - 布局分析模型：识别哪里是正文、哪里是表格、哪里是图片
    #   - 公式识别模型：识别数学公式
    # 如果是第一次运行，这些模型会自动下载（可能需要几分钟）
    converter = PdfConverter(
        artifact_dict=create_model_dict(),
    )

    # 执行解析！把 PDF 丢给 converter
    # converter(file_path) 返回一个"渲染结果"对象
    #   这个对象里包含了解析后的所有信息
    rendered = converter(file_path)

    # 从渲染结果中提取：
    #   text:   解析后的 markdown 文本（纯文字 + markdown 表格 + 图片标注）
    #   _:      中间的返回值（我们用不到，用 _ 忽略）
    #   images: 图片信息字典（图片位置、描述等）
    #
    # text_from_rendered() 返回值: (text, something, images)
    text, _, images = text_from_rendered(rendered)

    # ---------- 按空行拆成段落 ----------
    # text 是整个文档的完整文本，用 "\n\n"（空行）分隔段落
    # .split("\n\n") 把全文按空行切成一个段落列表
    #   比如 "第一章\n\n这是一段内容\n\n| 表头 |\n|------|" 
    #     → ["第一章", "这是一段内容", "| 表头 |\n|------|"]
    paragraphs = text.split("\n\n")

    documents = []  # 存放最终结果的列表

    # 遍历每个段落，把它转成 Document 对象
    for i, para in enumerate(paragraphs):
        # 去掉段落首尾的空格和换行
        para = para.strip()

        # 跳过两种无效段落：
        #   1. 空字符串（空行拆分产生的空白）
        #   2. 太短的文本（少于 10 个字符，可能是页码、标题残留等）
        if not para or len(para) < 10:
            continue

        # ---------- 识别段落类型 ----------
        # 利用 Marker 输出的 markdown 特征来判断类型

        if para.startswith("|") and para.endswith("|"):
            # 表格：markdown 表格以 | 开头、以 | 结尾
            #   比如 "| 姓名 | 年龄 |\n|------|------|\n| 张三 | 25 |"
            block_type = "table"

        elif para.startswith("!["):
            # 图片标注：markdown 图片语法 ![描述](路径)
            #   比如 "![图片1：系统架构图]"
            #   以 ! 开头、[ 紧跟的是图片语法
            block_type = "image"

        else:
            # 其他都算普通文本
            block_type = "text"

        # ---------- 包装成 LangChain Document ----------
        # Document 是 LangChain 中所有数据处理的标准格式
        # page_content: 段落内容（纯文本或 markdown）
        # metadata:     元信息字典（告诉下游"这个块是哪来的、什么类型"）
        doc = Document(
            page_content=para,
            metadata={
                "source": file_path,        # 源文件路径（方便追溯）
                "block_type": block_type,   # 块类型（chunker 看这个决定是否拆分）
                "chunk_id": i,              # 临时编号（最终编号由 chunker 统一分配）
            }
        )
        documents.append(doc)

    # ---------- 打印统计信息 ----------
    # 让用户知道解析了多少块，其中多少表格、多少图片
    table_count = sum(1 for d in documents if d.metadata["block_type"] == "table")
    image_count = sum(1 for d in documents if d.metadata["block_type"] == "image")
    print(f"  ✅ Marker 解析完成: {len(documents)} 块 "
          f"(表格:{table_count}, 图片:{image_count})")

    return documents


# ========== 函数2：解析 TXT 文件 ==========
def parse_txt_file(file_path: str) -> List[Document]:
    """
    【简单函数】解析 TXT 文件

    TXT 文件不需要 AI 模型，直接用 Python 读就行。
    这里用 LangChain 的 TextLoader 来读（统一接口，方便后续处理）。

    【参数】
      file_path: TXT 文件路径

    【返回】
      Document 对象列表
    """
    # 延迟导入 TextLoader（如果不上传 TXT 文件就不加载）
    from langchain_community.document_loaders import TextLoader

    print(f"  📄 正在加载 TXT: {os.path.basename(file_path)}")

    # TextLoader 是 LangChain 提供的文本文件加载器
    # encoding="utf-8" 确保中文不会乱码
    loader = TextLoader(file_path, encoding="utf-8")

    # .load() 返回一个 Document 列表
    #   对于 TXT 文件，通常只有一个 Document（整个文件是一个 Document）
    #   但我们保持返回列表格式，和 parse_pdf_with_marker() 统一
    docs = loader.load()

    # 补充元信息（TextLoader 不会自动加 block_type 和 chunk_id）
    for i, doc in enumerate(docs):
        doc.metadata["block_type"] = "text"   # TXT 文件里全是文本
        doc.metadata["chunk_id"] = i          # 临时编号

    print(f"  ✅ TXT 加载完成: {len(docs)} 块")
    return docs


# ========== 函数3：统一入口 ==========
def parse_document(file_path: str) -> List[Document]:
    """
    【统一入口】根据文件后缀自动选择解析器

    【设计思想】
      调用者不需要关心文件是 PDF 还是 TXT，只需要：
        docs = parse_document("随便什么文件路径")
      这个函数会自动判断后缀、选择对应的解析器。

    【参数】
      file_path: 文档路径（支持 .pdf 和 .txt）

    【返回】
      Document 对象列表
    """
    # 获取文件后缀，转小写（防止 .PDF、.Pdf 这种大小写不统一的情况）
    # os.path.splitext("wenben1.pdf") → ("wenben1", ".pdf")
    # 取 [1] 得到 ".pdf"，再 .lower() 转成 ".pdf"
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        # PDF → 用 Marker（功能强大，但加载慢）
        return parse_pdf_with_marker(file_path)

    elif ext == ".txt":
        # TXT → 用 TextLoader（轻量快速）
        return parse_txt_file(file_path)

    else:
        # 不支持的格式，报错提示
        raise ValueError(
            f"不支持的文档格式: {ext}\n"
            f"目前只支持 PDF (.pdf) 和 TXT (.txt)\n"
            f"如果确实需要其他格式，可以先用工具转成 PDF"
        )


# ========== 测试代码 ==========
# 直接运行这个文件时会执行下面的测试
# 用法: cd F:\rag-project && python utils/marker_parser.py
if __name__ == "__main__":
    import sys
    # 把父目录（项目根目录）加入搜索路径
    # 这样我们才能 import config 和 core 模块
    sys.path.insert(0, str(Path(__file__).parent.parent))

    print("="*50)
    print("测试 Marker 文档解析器")
    print("="*50)

    # 测试1：解析一份 PDF（先用 wenben2.pdf，换成你的文件名）
    test_file = "data/raw/wenben2.pdf"
    if os.path.exists(test_file):
        print(f"\n【测试1】解析 PDF: {test_file}")
        docs = parse_document(test_file)

        # 打印前 3 个块的预览
        print(f"\n  解析结果 ({len(docs)} 块)：")
        for doc in docs[:3]:
            ctype = doc.metadata['block_type']
            preview = doc.page_content[:100].replace("\n", " ")
            print(f"  [{ctype:5s}] {preview}...")

        # 统计各类型数量
        text_count = sum(1 for d in docs if d.metadata['block_type'] == 'text')
        table_count = sum(1 for d in docs if d.metadata['block_type'] == 'table')
        image_count = sum(1 for d in docs if d.metadata['block_type'] == 'image')
        print(f"\n  类型统计: 文本={text_count}, 表格={table_count}, 图片={image_count}")
    else:
        print(f"❌ 文件不存在: {test_file}")
        print("请确认 data/raw/ 下有 PDF 文件，或修改 test_file 变量")

    # 测试2：解析一份 TXT
    test_txt = "data/raw/wenben1.txt"
    if os.path.exists(test_txt):
        print(f"\n【测试2】解析 TXT: {test_txt}")
        docs = parse_document(test_txt)
        print(f"  TXT 解析完成: {len(docs)} 块")
    else:
        print(f"⚠️  跳过 TXT 测试（文件不存在: {test_txt}）")

    print("\n" + "="*50)
    print("测试完成！")
    print("="*50)
