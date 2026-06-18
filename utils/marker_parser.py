"""
utils/marker_parser.py - RAG系统文档解析器
========================================
【模块功能】
RAG系统的文档加载入口，统一处理PDF和TXT格式文件
解决传统PyPDFLoader的三大痛点：表格结构丢失、图片信息丢弃、中文排版混乱

【核心能力】
✅ PDF解析：基于Marker AI引擎，保留完整表格(Markdown格式)、图片标注、排版结构
✅ TXT解析：轻量快速加载，自动处理中文编码
✅ 自动适配：根据文件后缀自动选择解析器，对外提供单一调用入口

【文件结构】
parse_pdf_with_marker()  →  AI驱动的PDF结构化解析
parse_txt_file()         →  纯文本TXT文件加载
parse_document()         →  统一对外入口，自动分发解析任务

【数据流向】
磁盘文件 → 对应解析器 → 结构化段落拆分 → LangChain标准Document对象 → 分块器
"""

# ========== 导入依赖 ==========
# 操作系统文件操作：检查文件存在、提取文件名、路径处理
import os
# 面向对象路径工具：跨平台兼容Windows/Linux路径分隔符，避免手动拼接错误
from pathlib import Path
# 类型注解：明确函数输入输出类型，提升代码可读性和IDE提示能力
from typing import List
# LangChain标准文档格式：所有RAG组件统一识别的数据结构
# 包含page_content(文本内容)和metadata(元信息字典)两个核心属性
from langchain_core.documents import Document

# 强制使用 CPU 运行 PyTorch，避免没有 CUDA 运行库时进程崩溃
# 本机无 NVIDIA GPU，不设置此环境变量会导致 import marker 时直接崩溃
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# ========== PDF解析核心函数 ==========
def parse_pdf_with_marker(file_path: str) -> List[Document]:
    """
    使用Marker AI引擎解析PDF文件，输出结构化的Document列表
    
    参数:
        file_path: PDF文件的本地路径（支持相对路径和绝对路径）
        
    返回:
        Document对象列表，每个对象对应一个独立段落
        metadata包含三个字段：
        - source: 源文件的绝对路径（用于后续问题溯源）
        - block_type: 段落类型（text=普通文本/table=表格/image=图片标注）
        - chunk_id: 段落临时编号（按文档出现顺序从0开始）
    """
    # 延迟导入Marker依赖（关键优化）
    # Marker依赖PyTorch(约2-3GB)，加载速度慢
    # 仅在真正需要解析PDF时才导入，避免解析TXT时白白等待
    try:
        # Marker核心PDF转换引擎
        from marker.converters.pdf import PdfConverter
        # 自动创建AI模型配置字典（OCR、布局分析、公式识别）
        from marker.models import create_model_dict
        # 从解析结果中提取Markdown格式文本和图片信息
        from marker.output import text_from_rendered
    except ImportError as e:
        # 抛出清晰的错误提示，直接告诉用户安装命令
        raise ImportError(
            "❌ Marker依赖未安装，请在终端执行以下命令：\n"
            "  pip install marker-pdf -i https://pypi.tuna.tsinghua.edu.cn/simple\n"
            f"  原始错误信息：{e}"
        )

    # 打印处理进度，让用户知道程序正在运行
    print(f"  🔍 正在解析PDF: {os.path.basename(file_path)}")
    
    # 统一转换为绝对路径也即是文件的完整路径，解决不同运行目录下相对路径找不到文件的问题
    file_path = str(Path(file_path).resolve())

    # 初始化PDF转换器 首次运行会自动下载OCR、布局分析等AI模型（约几分钟，仅下载一次）
    #把创建好的PDF 转换器实例，赋值给变量 converter
    #给artifact_dict传入一个工具 / 模型配置字典，告诉转换器用什么模型、配置解析 PDF
    converter = PdfConverter(artifact_dict=create_model_dict())
    
    # 执行PDF解析，返回包含所有结构化信息的渲染结果对象
    rendered = converter(file_path)
    
    # 提取解析，结果固定返回 3 个返回值：(完整md文本, 无用中间对象, 图片信息字典)
    # text: 完整的Markdown格式文本（包含表格和图片标注）
    # _: 中间返回值（我们不需要，用下划线忽略）
    # images: 图片详细信息字典（本项目暂未使用，保留供后续扩展）
    text, _, images = text_from_rendered(rendered)

    # 按空行拆分全文为独立段落
    # Marker输出的Markdown文本用两个换行符分隔不同段落
    paragraphs = text.split("\n\n")
    documents = []  # 存储最终解析结果

    # 遍历所有段落，处理并包装为Document对象
    for idx, para in enumerate(paragraphs):
        # 清理段落首尾的空白字符（空格、换行、制表符）
        para = para.strip()
        
        # 过滤无效内容：空段落和过短文本（可能是页码、页眉页脚残留）
        if not para or len(para) < 10:
            continue
        # 根据Markdown语法特征自动识别段落类型
        if para.startswith("|") and para.endswith("|"):
            block_type = "table"  # Markdown表格以|开头和结尾
        elif para.startswith("!["):
            block_type = "image"  # Markdown图片语法：![描述](路径)
        else:
            block_type = "text"   # 其他均为普通文本

        # 包装为LangChain标准Document对象
        documents.append(Document(
            page_content=para,
            metadata={
                "source": file_path,
                "block_type": block_type,
                "chunk_id": idx
            }
        ))

    # 统计并打印解析结果
    table_count = sum(1 for d in documents if d.metadata["block_type"] == "table")
    image_count = sum(1 for d in documents if d.metadata["block_type"] == "image")
    print(f"  ✅ PDF解析完成：共{len(documents)}块(表格:{table_count}, 图片:{image_count})")

    return documents


# ========== TXT文件解析函数 ==========
def parse_txt_file(file_path: str) -> List[Document]:
    """
    解析纯文本TXT文件
    
    参数:
        file_path: TXT文件的本地路径
        
    返回:
        Document对象列表（通常只有一个元素，包含全文内容）
    """
    # 延迟导入TextLoader（仅解析TXT时加载）
    from langchain_community.document_loaders import TextLoader

    print(f"  📄 正在加载TXT: {os.path.basename(file_path)}")
    
    # 使用UTF-8编码加载，避免中文乱码
    loader = TextLoader(file_path, encoding="utf-8")
    # load()方法返回Document列表，TXT文件默认整个文件为一个Document
    docs = loader.load()

    # 补充统一的元信息，和PDF解析结果保持格式一致
    for idx, doc in enumerate(docs):
        doc.metadata["block_type"] = "text"
        doc.metadata["chunk_id"] = idx

    print(f"  ✅ TXT加载完成：共{len(docs)}块")
    return docs


# ========== 统一对外入口 ==========
def parse_document(file_path: str) -> List[Document]:
    """
    文档解析统一入口，自动根据文件后缀选择对应的解析器
    
    设计思想：上层调用者不需要关心文件格式，只需传入文件路径即可
    后续新增支持的格式（如.docx）只需在这里添加判断分支即可
    
    参数:
        file_path: 文档路径（支持.pdf和.txt格式，大小写不敏感）
        
    返回:
        结构化的Document对象列表
        
    异常:
        ValueError: 传入不支持的文件格式时抛出
    """
    # 获取文件后缀并转为小写，兼容.PDF、.Pdf等大小写混合的情况
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == ".pdf":
        return parse_pdf_with_marker(file_path)
    elif file_ext == ".txt":
        return parse_txt_file(file_path)
    else:
        raise ValueError(
            f"不支持的文件格式：{file_ext}\n"
            "目前仅支持PDF(.pdf)和TXT(.txt)格式\n"
            "如需处理其他格式，请先转换为PDF后再导入"
        )


# ========== 模块测试代码 ==========
# 直接运行本文件时执行，用于快速验证解析器功能
# 运行命令：cd F:\rag-project && python utils/marker_parser.py
if __name__ == "__main__":
    import sys
    # 将项目根目录加入Python搜索路径
    # 解决跨模块导入时找不到config、core等包的问题
    sys.path.insert(0, str(Path(__file__).parent.parent))

    print("="*50)
    print("文档解析器测试")
    print("="*50)

    # 测试1：PDF解析
    test_pdf = "data/raw/wenben2.pdf"
    if os.path.exists(test_pdf):
        print(f"\n【测试1】PDF解析: {test_pdf}")
        docs = parse_document(test_pdf)
        
        # 打印前3个块的内容预览
        print(f"\n  解析结果预览：")
        for doc in docs[:3]:
            content_preview = doc.page_content[:100].replace("\n", " ")
            #:5s 字符串占 5 个字符的宽度，不足的用空格补齐 eg: [text ] [table] [image]
            print(f"  [{doc.metadata['block_type']:5s}] {content_preview}...")
        
        # 统计各类型段落数量
        text_count = sum(1 for d in docs if d.metadata["block_type"] == "text")
        table_count = sum(1 for d in docs if d.metadata["block_type"] == "table")
        image_count = sum(1 for d in docs if d.metadata["block_type"] == "image")
        print(f"\n  类型统计：文本={text_count}, 表格={table_count}, 图片={image_count}")
    else:
        print(f"\n❌ 测试PDF不存在: {test_pdf}")
        print("请将测试文件放入data/raw目录，或修改test_pdf变量为你的文件路径")

    # 测试2：TXT解析
    test_txt = "data/raw/wenben1.txt"
    if os.path.exists(test_txt):
        print(f"\n【测试2】TXT解析: {test_txt}")
        docs = parse_document(test_txt)
    else:
        print(f"\n⚠️  跳过TXT测试(文件不存在: {test_txt})")

    print("\n" + "="*50)
    print("测试完成！")
    print("="*50)