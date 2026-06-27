"""
core/cost_tracker.py — Token消耗统计 & 成本核算

职责：
  1. 记录每轮对话的 input/output token 数
  2. 按模型不同自动计算费用（DeepSeek/Qwen/Kimi 价格不同）
  3. 输出会话统计：总Token、总费用、调用次数

用法：
  from core.cost_tracker import CostTracker
  tracker = CostTracker()
  tracker.record("deepseek", input_tokens=520, output_tokens=180)
  print(tracker.summary())
"""

import json
import time
from pathlib import Path
from typing import Dict, List

# ========== 各模型定价（人民币 / 百万token）==========
# 数据来源：各自官网公开定价，2026年6月
PRICING = {
    "deepseek":       {"input": 0.14, "output": 0.28},   # DeepSeek V4 Pro
    "deepseek_flash": {"input": 0.03, "output": 0.06},   # Flash 便宜 5~10x
    "qwen":           {"input": 0.20, "output": 0.20},   # 通义千问 qwen-plus
    "kimi":           {"input": 0.60, "output": 0.60},   # Kimi（长文档，贵一些）
    "local":          {"input": 0.0,  "output": 0.0},    # Ollama 本地，免费
}


class CostTracker:
    """
    轻量级统计器，不依赖任何第三方库。
    所有数据存内存 + 可选 JSON 持久化。
    """

    def __init__(self, log_dir: str = None):
        """
        参数:
          log_dir: 日志目录。默认项目根目录下 ./logs/
                  传 None 仅内存统计，不落盘
        """
        # 每条请求记录：[{model, input_tokens, output_tokens, cost, timestamp}, ...]
        #_records是一个列表，里面的每个元素都是字典
        self._records: List[Dict] = []

        # 日志持久化目录
        #如果传入了日志目录 log_dir，就转成 Path 对象；如果没传（为空 / None），就设为 None
        self._log_dir = Path(log_dir) if log_dir else None
        if self._log_dir:
            #Path 对象的「创建文件夹」方法 mkdir()，参数 parents=True 表示如果父目录不存在就一起创建，exist_ok=True 表示如果目录已经存在也不报错
            self._log_dir.mkdir(parents=True, exist_ok=True)

        # 当前日志文件（每天一个，文件名 = 日期）
        self._log_file = None
        self._today = None

    # ---------- 核心方法 ----------

    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        extra: Dict = None
    ) -> float:
        """
        记录一次 LLM 调用。

        参数:
          model:        模型标识，如 "deepseek" / "qwen" / "local"
          input_tokens: 提示词消耗的 token 数
          output_tokens: 模型输出消耗的 token 数
          extra:        额外信息（请求ID、query文本等，可选）

        返回:
          本次调用的费用（元）
        """
        # 1. 查定价，算费用
        short_name = model
        if model not in PRICING:
            for key in PRICING:
                if key in model:
                    short_name = key
                    break
        price = PRICING.get(short_name, {"input": 0, "output": 0})
        cost_input = (input_tokens / 1_000_000) * price["input"]
        cost_output = (output_tokens / 1_000_000) * price["output"]
        total_cost = cost_input + cost_output

        # 2. 构建一条记录
        entry = {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": round(total_cost, 6),          # 保留6位小数
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if extra:
            entry.update(extra)

        # 3. 存内存
        self._records.append(entry)

        # 4. 存磁盘（JSON追加模式）
        if self._log_dir:
            self._append_to_file(entry)

        return total_cost

    # ---------- 统计查询 ----------

    def summary(self) -> Dict:
        """
        返回当前会话的汇总统计。

        返回值示例:
        {
            "total_calls": 15,
            "total_input_tokens": 12345,
            "total_output_tokens": 6789,
            "total_cost": 0.0123,
            "by_model": {
                "deepseek": {"calls": 10, "input": 8000, "output": 4000, "cost": 0.0056},
                "qwen":     {"calls": 5,  "input": 4345, "output": 2789, "cost": 0.0067}
            }
        }
        """
        if not self._records:
            return {"total_calls": 0, "total_input_tokens": 0,
                    "total_output_tokens": 0, "total_cost": 0.0, "by_model": {}}

        by_model = {}
        total_input = 0
        total_output = 0
        total_cost = 0.0
        #_records是一个列表，里面的每个元素都是字典，每个字典都有 model、input_tokens、output_tokens、cost 等字段
        for r in self._records:
            model = r["model"]
            if model not in by_model:
                by_model[model] = {"calls": 0, "input": 0, "output": 0, "cost": 0.0}
            by_model[model]["calls"] += 1
            by_model[model]["input"] += r["input_tokens"]
            by_model[model]["output"] += r["output_tokens"]
            by_model[model]["cost"] += r["cost"]
            total_input += r["input_tokens"]
            total_output += r["output_tokens"]
            total_cost += r["cost"]

        return {
            "total_calls": len(self._records),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost": round(total_cost, 6),
            "by_model": by_model,
        }

    def last(self) -> Dict | None:
        """返回最近一次调用的记录，没有则返回 None"""
        return self._records[-1] if self._records else None

    # ---------- 持久化（内部用） ----------

    def _get_log_file(self) -> Path:
        """确保日志文件按日期轮转（每天一个文件）"""
        today = time.strftime("%Y-%m-%d")
        if today != self._today or self._log_file is None:
            self._today = today
            self._log_file = self._log_dir / f"cost_{today}.jsonl"
        return self._log_file

    def _append_to_file(self, entry: Dict) -> None:
        """JSONL 格式追加：每行一个 JSON 对象"""
        log_path = self._get_log_file()
        with open(log_path, "a", encoding="utf-8") as f:
            # Python 字典对象 entry → 转换成 JSON 格式字符串，ensure_ascii=False 保持中文不被转义，然后写入文件并换行
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ========== 便捷函数：全局单例 ==========
# 避免每次用都 new 一个，全局共用同一个 tracker

_global_tracker = None


def get_tracker(log_dir: str = "./logs") -> CostTracker:
    """获取全局共享的 CostTracker 实例"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = CostTracker(log_dir=log_dir)
    return _global_tracker



