"""
core/request_logger.py — 全链路请求日志

职责：
  每次 LLM 调用记录一条日志，包含 request_id / query / 模型 / Token / 费用 / 时间戳。
  JSONL 格式，每天一个文件，存放在 logs/ 目录。

跟 cost_tracker 的关系：
  cost_tracker 负责「统计」（汇总、按模型分组、总费用）
  request_logger 负责「记录」（每条请求的完整快照，方便回溯排查）

用法：
  from core.request_logger import log_request
  log_request(request_id="abc123", query="什么是RAG", model="deepseek",
              input_tokens=80, output_tokens=120, cost=0.000044)
"""

import json
import time
import uuid
from pathlib import Path
from typing import Optional


# ========== 日志写入 ==========

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def log_request(
    request_id: Optional[str] = None,
    query: str = "",
    model: str = "",
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost: float = 0.0,
    cache_hit: bool = False,
    extra: Optional[dict] = None,
) -> str:
    """
    记录一条 LLM 请求日志，返回这条日志的 request_id。

    参数:
      request_id:  请求唯一ID，不传自动生成（uuid）
      query:       用户的原始问题
      model:       使用的模型名
      input_tokens: 提示词 token 数
      output_tokens: 输出 token 数
      cost:        本次调用费用（元）
      cache_hit:   是否命中缓存（先留字段，缓存系统 D18 做好后填值）
      extra:       额外字段（检索耗时等，可以随便加）

    返回:
      request_id 字符串，方便调用方拿到后做后续关联
    """
    # 确保日志目录存在
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 自动生成 request_id
    if request_id is None:
        #Python 生成「全球唯一、永不重复」随机 ID 的工具，uuid4() 基于随机数生成一个 UUID，通常足够用作请求 ID。取前8位，既保证了唯一性，又更短更好看。
        request_id = str(uuid.uuid4())[:8]  # 取前8位，够用且好看

    # 组装记录
    entry = {
        "request_id": request_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "query": query[:200],  # 截断，防止超长问题撑爆日志
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": round(cost, 6),
        "cache_hit": cache_hit,
    }
    if extra:
        entry.update(extra)

    # 写 JSONL（每天一个文件，按日期自动轮转）
    today = time.strftime("%Y-%m-%d")
    log_path = LOG_DIR / f"requests_{today}.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        #将 Python 字典（文档块数据）转换为 JSON 格式字符串，且 中文原样输出、不转成乱码，并写入文件，每条记录占一行
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return request_id
