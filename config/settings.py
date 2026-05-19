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

# ------------------- 模型配置 -------------------
# 大模型名称（用通义千问免费版足够）
LLM_MODEL_NAME = "qwen-turbo"
# 向量嵌入模型名称（专门用来把文本转成向量）
EMBEDDING_MODEL_NAME = "text-embedding-v1"
# 大模型温度（0=最严谨，不编造内容）
TEMPERATURE = 0

# ------------------- 文本分块配置（填你刚才选的最优参数）-------------------
CHUNK_SIZE = 800  # 替换成你的最优值
CHUNK_OVERLAP = 80  # 替换成你的最优值

# ------------------- 向量库配置 -------------------
# 本地向量库保存路径
VECTOR_DB_PATH = "./chroma_db"
# 向量库集合名称（不用改）
COLLECTION_NAME = "rag_collection"

# ------------------- 检索配置 -------------------
# 每次搜索返回最相关的3个文本块
RETRIEVER_TOP_K = 3