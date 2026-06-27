"""
core/llm_factory.py — 统一模型工厂（合并配置 + LangChain 封装 + 成本追踪）
"""
import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.outputs import LLMResult
from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from core.cost_tracker import get_tracker
from core.request_logger import log_request

load_dotenv(Path(__file__).resolve().parent.parent / "config" / ".env")
from config.settings import (
    TEMPERATURE,
    KIMI_MODEL_NAME,
    DEEPSEEK_MODEL_NAME,
    DEEPSEEK_FLASH_MODEL_NAME,
    QWEN_MODEL_NAME, 
)


# ========== 模型配置 ==========
class ModelType(Enum):
    DEEPSEEK = "deepseek"
    DEEPSEEK_FLASH = "deepseek_flash"
    QWEN = "qwen"
    KIMI = "kimi"
    LOCAL = "local"

MODEL_CONFIG = {
    ModelType.DEEPSEEK: {
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_name": DEEPSEEK_MODEL_NAME,
    },
    ModelType.DEEPSEEK_FLASH: {
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_name": DEEPSEEK_FLASH_MODEL_NAME,
    },
    ModelType.QWEN: {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "model_name": QWEN_MODEL_NAME,
    },
    ModelType.KIMI: {
        "base_url": "https://api.moonshot.cn/v1",
        "api_key_env": "KIMI_API_KEY",
        "model_name": KIMI_MODEL_NAME,
    },
}

_TYPE_MAP = {
    "deepseek":       ModelType.DEEPSEEK,
    "deepseek_flash": ModelType.DEEPSEEK_FLASH,
    "qwen":           ModelType.QWEN,
    "kimi":           ModelType.KIMI,
}

# ========== 成本追踪 ==========
class CostTrackingCallback(BaseCallbackHandler):
    def on_llm_end(self, response: LLMResult, *, run_id, **kwargs) -> None:
        llm_out = response.llm_output or {}
        usage = llm_out.get("token_usage", {})
        if not usage:
            return
        cost = get_tracker().record(
            model=llm_out.get("model_name", "unknown"),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )
        log_request(
            model=llm_out.get("model_name", "unknown"),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            cost=cost,
        )

# ========== 创建 LLM ==========
def create_llm(model_type: str = "qwen", temperature: float = TEMPERATURE):
    if model_type == "local":
        return ChatOllama(model="llama3:8b", temperature=temperature)

    config = MODEL_CONFIG[_TYPE_MAP[model_type]]
    api_key = os.getenv(config["api_key_env"])
    if not api_key:
        raise ValueError(f"未找到环境变量 {config['api_key_env']}")

    if model_type == "kimi":
        temperature = 1.0

    return ChatOpenAI(
        model=config["model_name"],
        api_key=api_key,
        base_url=config["base_url"],
        temperature=temperature,
        callbacks=[CostTrackingCallback()],
    )
