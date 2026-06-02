# config/settings.py 全局配置文件
import os
from pathlib import Path
from dotenv import load_dotenv

# ------------------- 路径自动定位（更稳、不写死） -------------------
# 项目根目录（自动找，不怕挪位置）
BASE_DIR = Path(__file__).resolve().parent.parent


# 自动加载.env文件里的API密钥（不用手动写在这里，防止泄露）
load_dotenv(BASE_DIR / "config" / ".env")

# ------------------- API配置 -------------------
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
KIMI_API_KEY = os.getenv("KIMI_API_KEY")

# ------------------- 模型配置 -------------------
# 可用模型：qwen-plus | deepseek-v4-pro | deepseek-v4-flash | moonshot-v1-2.6
LLM_MODEL_NAME = "qwen-plus"
# 深度求索 DeepSeek V4 Pro（推理最强版，RAG回答、Scorer打分用）
DEEPSEEK_MODEL_NAME = "deepseek-v4-pro"
# 深度求索 DeepSeek V4 Flash（极速便宜版，批量测试/护栏过滤用）
DEEPSEEK_FLASH_MODEL_NAME = "deepseek-v4-flash"
# Kimi v2.6（长文档处理）
KIMI_MODEL_NAME = "moonshot-v1-2.6"
# 向量嵌入模型名称
EMBEDDING_MODEL_NAME = "text-embedding-v1"
# 大模型温度
TEMPERATURE = 0.1

# ------------------- 文本分块配置（填你刚才选的最优参数）-------------------
CHUNK_SIZE = 800  # 替换成你的最优值
CHUNK_OVERLAP = 80  # 替换成你的最优值

# ------------------- 向量库配置 -------------------
# 本地向量库保存路径
VECTOR_DB_PATH = "./chroma_db"
# 向量库集合名称（不用改）
COLLECTION_NAME = "rag_collection"

# ------------------- 检索配置 -------------------
# 每次搜索返回最相关的k个文本块
RETRIEVER_TOP_K = 20

# 文档加载白名单，只加载列表内文件
ALLOW_DOC_NAMES = [
    "wenben1.pdf",
    # 后续新增文档只填这里，不用改任何代码
    # "wenben2.pdf"
]