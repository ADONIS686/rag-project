# 导入分块工具
from langchain_text_splitters import RecursiveCharacterTextSplitter
# 导入Day2写的文档加载函数
from utils.document_loader import load_documents_from_json

# 加载清洗好的文档
documents = load_documents_from_json("data/processed_documents.json")
# 取第一个文档做测试
test_text = documents[0].page_content

# 定义3组测试参数
test_params = [
    (500, 50),   # 组1：小块
    (800, 80),   # 组2：中块（推荐默认）
    (1000, 100)  # 组3：大块
]

# 循环测试每组参数 enumerate是Python内置函数，返回元素的索引和值，这里用来打印当前是第几组参数测试
#separators是分块时优先考虑的分隔符，越前面的优先级越高，最后一个空字符串是兜底，保证不会死循环（如果文本里没有任何分隔符，就按chunk_size硬切）
for i, (chunk_size, chunk_overlap) in enumerate(test_params):
    print(f"\n===== 测试第{i+1}组参数：chunk_size={chunk_size}, chunk_overlap={chunk_overlap} =====")
    
    # 初始化分块器（中文专属分割规则）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )
    
    # 执行分块
    chunks = text_splitter.split_text(test_text)
    
    print(f"共分成{len(chunks)}个块\n")
    # 打印每个块的关键信息（开头+结尾+长度）
    for idx, chunk in enumerate(chunks):
        print(f"【块{idx+1}】总长度：{len(chunk)} 字")
        print(f"开头前50字：{chunk[:50]}...")
        print(f"结尾后100字：...{chunk[-100:]}\n")
        print("-"*40)