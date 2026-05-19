# 导入TextLoader PyPDFLoader工具
from langchain_community.document_loaders import TextLoader, PyPDFLoader


# ========== 1. 读取 TXT 文件 ==========
# 1. 初始化加载器，指定文件路径和utf-8编码（必须加encoding）
loader = TextLoader(file_path="data/test.txt", encoding="utf-8")

# 2. 执行读取操作，返回Document对象的列表
documents = loader.load()

# 3. 打印结果，理解Document对象
print("===== 读取到的TXT内容 =====")
# documents[0]：因为TXT只有1页，所以取列表第一个元素
print(documents[0].page_content)

print("\n===== TXT文件的元信息 =====")
print(documents[0].metadata)

# ========== 2. 读取 PDF 文件 ==========

# 1. 初始化加载器，指定PDF文件路径
loader = PyPDFLoader(file_path="data/test.pdf")

# 2. 执行读取操作，返回Document对象的列表（每个元素对应一页）
pages = loader.load()

# 3. 打印结果，理解PDF的分页特性
print(f"PDF总页数：{len(pages)}")
print("\n===== 第1页内容 =====")
print(pages[0].page_content)
print("\n===== 第1页元信息 =====")
print(pages[0].metadata)  # 会显示页码和文件路径

# 4. 合并多页内容为一个整体（RAG项目必须做的步骤）
full_content = "\n".join([page.page_content for page in pages])
print("\n===== 合并后的完整PDF内容 =====")
print(full_content)