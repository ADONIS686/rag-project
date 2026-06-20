"""
core/llm_factory.py — LangChain 模型工厂
从 llm_client 拿配置 → 包装成 LangChain ChatOpenAI/ChatOllama
"""
import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from core.llm_client import ModelType, LLMClient

load_dotenv(Path(__file__).resolve().parent.parent / "config" / ".env")

# string key → ModelType 枚举映射（唯一维护点在 llm_client.py）
_TYPE_MAP = {
    "deepseek":       ModelType.DEEPSEEK,
    "deepseek_flash": ModelType.DEEPSEEK_FLASH,
    "qwen":           ModelType.QWEN,
    "kimi":           ModelType.KIMI,
}

def create_llm(model_type: str = "qwen", temperature: float = 0.1):
    """
    创建 LangChain 兼容的 LLM 实例。
    参数:
        model_type: "qwen" / "deepseek" / "deepseek_flash" / "kimi" / "local"
        temperature: 0=严谨 1=创造
    返回:
        LangChain Runnable（ChatOpenAI 或 ChatOllama）
    """
    if model_type == "local":
        return ChatOllama(model="llama3:8b", temperature=temperature)
    
    config = LLMClient.MODEL_CONFIG[_TYPE_MAP[model_type]]
    api_key = os.getenv(config["api_key_env"])
    if not api_key:
        raise ValueError(f"未找到环境变量 {config['api_key_env']}")
    
    # 🆕 Kimi 模型特殊处理：temperature 只能为 1

    if model_type == "kimi":
        temperature = 1.0

    return ChatOpenAI(
        model=config["model_name"],
        api_key=api_key,
        base_url=config["base_url"],
        temperature=temperature,
    )