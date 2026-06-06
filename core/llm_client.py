"""
core/llm_client.py - 统一多模型调用客户端

支持 DeepSeek V4 Pro / Flash / 通义千问 / Kimi / 本地 Ollama 五模型切换。
所有云端 API 兼容 OpenAI SDK 格式，切换零成本。

用法：
    from core.llm_client import LLMClient, ModelType

    client = LLMClient(default_model=ModelType.DEEPSEEK)
    answer = client.chat("你是谁？")
    client.set_default_model(ModelType.LOCAL)  # 切到本地模型
"""

import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
from core.request_logger import log_request

load_dotenv(Path(__file__).resolve().parent.parent / "config" / ".env")                      # 执行读 .env，后面 os.getenv() 就能取到值了



class ModelType(Enum):
    """支持的模型类型"""
    DEEPSEEK = "deepseek"           # DeepSeek V4 Pro — 主力，推理最强
    DEEPSEEK_FLASH = "deepseek_flash"  # DeepSeek V4 Flash — 批量跑测，便宜 5~10 倍
    QWEN = "qwen"                   # 通义千问（当前项目已有）
    KIMI = "kimi"                   # 长文档处理
    LOCAL = "local"                 # Ollama 本地 Llama3


class LLMClient:
    """统一大模型调用客户端，一个参数切换模型"""

    # 各模型的 API 配置
    MODEL_CONFIG = {
        ModelType.DEEPSEEK: {
            "base_url": "https://api.deepseek.com/v1",
            "api_key_env": "DEEPSEEK_API_KEY",
            "model_name": "deepseek-v4-pro",
        },
        ModelType.DEEPSEEK_FLASH: {
            "base_url": "https://api.deepseek.com/v1",
            "api_key_env": "DEEPSEEK_API_KEY",
            "model_name": "deepseek-v4-flash",
        },
        ModelType.QWEN: {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key_env": "DASHSCOPE_API_KEY",
            "model_name": "qwen-plus",
        },
        ModelType.KIMI: {
            "base_url": "https://api.moonshot.cn/v1",
            "api_key_env": "KIMI_API_KEY",
            "model_name": "moonshot-v1-2.6",
        },
    }

    def __init__(self, default_model: ModelType = ModelType.DEEPSEEK):
        self.default_model = default_model
        # 延迟初始化，用到哪个才 import 哪个
        self._openai = None

    @property
    def openai(self):
        """延迟导入 openai，避免不必要时加载"""
        if self._openai is None:
            import openai
            self._openai = openai
        return self._openai

    def set_default_model(self, model: ModelType):
        """切换默认模型"""
        self.default_model = model

    def chat(self, prompt: str, model: ModelType = None, temperature: float = 0.1, max_tokens: int = 1024) -> str:
        """
        调用大模型生成回答。

        参数:
            prompt: 提示词 / 用户问题
            model: 指定模型，不传就用默认模型
            temperature: 0=严谨 1=有创造力
            max_tokens: 最大生成长度
        返回:
            模型回答文本
        """
        if model is None:
            model = self.default_model

        if model == ModelType.LOCAL:
            return self._ollama_chat(prompt, temperature, max_tokens)
        else:
            return self._openai_compatible_chat(prompt, model, temperature, max_tokens)

    def _openai_compatible_chat(self, prompt: str, model: ModelType, temperature: float, max_tokens: int) -> str:
        """调用 OpenAI 兼容 API（DeepSeek / Qwen / Kimi）"""
        config = self.MODEL_CONFIG[model]
        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            raise ValueError(
                f"未找到 {config['api_key_env']} 环境变量！"
                f"请在 .env 文件中设置 {config['api_key_env']}=你的密钥"
            )

        client = self.openai.OpenAI(
            api_key=api_key,
            base_url=config["base_url"],
        )
        response = client.chat.completions.create(
            model=config["model_name"],
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        #response
        # ├─ choices：AI回答内容（response.choices[0].message.content）
        # └─ usage：Token消耗统计对象
        #    ├─ prompt_tokens：输入token（用户提问） → input_tokens
        #    └─ completion_tokens：输出token（AI回复） → output_tokens

        # ========== 新增：Token统计 ==========
        from core.cost_tracker import get_tracker
        tracker = get_tracker()
        cost = tracker.record(
            model=model.value,
            #OpenAI 规范接口返回对象自带的内置属性，调用完 create() 请求大模型后，服务商返回的完整数据包里自带 usage 字段，里面有 prompt_tokens（输入 tokens 数量）和 completion_tokens（输出 tokens 数量）
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )
        log_request(
            model=model.value,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            cost=cost,                          # tracker.record 返回的费用
        )
        #AI 生成的候选回答列表,取第一个、最优的回答,回答的消息对象的纯文本回答内容,去掉首尾空白
        return response.choices[0].message.content.strip()

    def _ollama_chat(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """调用本地 Ollama 模型"""
        import ollama
        response = ollama.chat(
            model="llama3:8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )
        # === 新增：Token统计 ===
        from core.cost_tracker import get_tracker
        tracker = get_tracker()
        tracker.record(
            model="local",
            input_tokens=response.get("prompt_eval_count", 0),
            output_tokens=response.get("eval_count", 0),
        )
        return response["message"]["content"].strip()


# ---------- 便捷函数 ----------

# 全局单例，避免重复创建
_global_client = None


def get_client(model: ModelType = ModelType.DEEPSEEK) -> LLMClient:
    """获取全局 LLM 客户端（单例）"""
    global _global_client
    if _global_client is None:
        _global_client = LLMClient(default_model=model)
    return _global_client


def chat(prompt: str, model: ModelType = None) -> str:
    """快捷调用：一行代码调用大模型"""
    #_global_client接收到的实例对象调用了chat函数
    return get_client().chat(prompt, model=model)
