# core/cache.py — RAG 问答缓存系统
"""
两层缓存架构：
  内存 dict（快速命中，微秒级）→ JSON 文件（持久化，重启不丢失）

缓存条目结构：
  {
    "cache_key_hex": {
      "query": "用户原始问题",
      "answer": "LLM 生成的最终答案",
      "model": "qwen",              # 记录用哪个模型生成的
      "created_at": "2026-06-12T10:30:00",
      "expires_at": "2026-06-19T10:30:00",  # 7天后自动过期
      "hit_count": 3                 # 命中次数统计
    }
  }

拦截位置（integration point）：
  用户输入 → 护栏检查 → 【缓存检查】→ 命中直接返回 / 未命中走 RAG 链 → 写入缓存
"""
import hashlib
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


# ====================== 全局常量 ======================

# 缓存文件存放路径
CACHE_FILE = Path(__file__).resolve().parent.parent / "logs" / "cache.json"
# 缓存有效期（天），设置为 0 表示永不过期
CACHE_TTL_DAYS = 7


# ====================== 工具函数 ======================

def _make_cache_key(query: str) -> str:
    """
    根据用户原始问题生成唯一缓存键。
    
    设计决策（面试可展开讲）：
    - 当前项目文档集固定（wenben1.pdf），所以只用 query 做 key 就够了
    - 如果未来文档集会变动，应该在 hash 中加入文档名列表，如：
        doc_signature = ",".join(sorted(doc_names))
        raw = f"{query.strip().lower()}|{doc_signature}"
    - 用 MD5 而非 SHA256，因为这里不需要密码学安全，只需要快速散列

    参数:
        query: 用户原始问题字符串
    返回:
        32 位十六进制 MD5 摘要
    """
    # strip + lower：忽略首尾空格和大小写差异，"燕光逸是谁" 和 " 燕光逸是谁 " 共享同一个 key
    raw = query.strip().lower()
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    """返回当前时间的 ISO 8601 格式字符串（精确到秒）"""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _expires_at() -> str:
    """计算 CACHE_TTL_DAYS 天后的过期时间"""
    return (datetime.now() + timedelta(days=CACHE_TTL_DAYS)).strftime("%Y-%m-%dT%H:%M:%S")


def _is_expired(expires_at_str: str) -> bool:
    """
    判断缓存条目是否已过期。

    参数:
        expires_at_str: ISO 8601 格式的过期时间字符串，如 "2026-06-19T10:30:00"
    返回:
        True  = 已过期，应删除
        False = 有效，可复用
    """
    if CACHE_TTL_DAYS == 0:
        return False  # TTL=0 表示永不过期
    try:
        expires_dt = datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M:%S")
        return datetime.now() > expires_dt
    except (ValueError, TypeError):
        # 时间格式损坏，按过期处理
        return True


# ====================== 核心缓存类 ======================

class RAGCache:
    """
    RAG 问答缓存管理器（单例模式）
    
    两层结构：
      Layer 1 — 内存 dict：self._cache，所有 get/set 操作先走这里
      Layer 2 — JSON 磁盘文件：logs/cache.json，每次 set 后自动落盘

    线程安全：
      self._lock 保护写操作（dict 修改 + JSON 序列化），防止并发写入损坏文件

    使用示例：
      >>> cache = RAGCache()
      >>> cache.get("燕光逸是谁")        # 命中 → 返回答案；未命中 → 返回 None
      >>> cache.set("燕光逸是谁", "燕光逸是当朝皇帝", model="qwen")
    """

    def __init__(self):
        # 内存层：{key_hex: {"query": ..., "answer": ..., ...}}
        self._cache: Dict[str, Dict[str, Any]] = {}
        # 读写锁，保护 self._cache + JSON 文件
        self._lock = threading.Lock()
        # 统计计数器
        self.total_queries = 0   # 总查询次数
        self.cache_hits = 0      # 缓存命中次数
        # 启动时恢复磁盘缓存
        self._load_from_disk()

    # ---------- 内存层 ----------

    def get(self, query: str) -> Optional[str]:
        """
        查询缓存：命中返回答案字符串，未命中/已过期返回 None。
        
        执行流程：
        1. 生成缓存键
        2. 内存 dict 查找（O(1)）
        3. 检查 TTL 过期
        4. 更新统计

        参数:
            query: 用户原始问题
        返回:
            缓存的答案字符串，或 None
        """
        self.total_queries += 1
        key = _make_cache_key(query)

        entry = self._cache.get(key)
        if entry is None:
            return None  # 直接 miss，不调 LLM，零成本

        # 惰性过期淘汰：只在被访问时才检查
        if _is_expired(entry.get("expires_at", "")):
            with self._lock:
                self._cache.pop(key, None)
                self._save_to_disk_unsafe()  # 已在锁内，用不加锁版本
            return None

        # 命中：更新计数
        self.cache_hits += 1
        entry["hit_count"] = entry.get("hit_count", 0) + 1
        return entry["answer"]

    def set(self, query: str, answer: str, model: str = "unknown") -> None:
        """
        将问答结果写入缓存（内存 + 磁盘双写）。

        参数:
            query:  用户原始问题
            answer: LLM 生成的最终答案
            model:  生成此答案的模型名称（用于统计）
        """
        key = _make_cache_key(query)
        entry = {
            "query": query.strip(),
            "answer": answer,
            "model": model,
            "created_at": _now_iso(),
            "expires_at": _expires_at(),
            "hit_count": 0,  # 初始命中次数为 0（刚写入还没被命中过）
        }

        with self._lock:
            self._cache[key] = entry
            self._save_to_disk_unsafe()

    def has(self, query: str) -> bool:
        """
        检查缓存是否有效（不更新统计计数器，不走过期淘汰）。
        与 get() 的区别：has() 是纯查询，不产生副作用。

        参数:
            query: 用户原始问题
        返回:
            True = 缓存有效可用；False = 不存在或已过期
        """
        key = _make_cache_key(query)
        entry = self._cache.get(key)
        if entry is None:
            return False
        return not _is_expired(entry.get("expires_at", ""))

    # ---------- JSON 持久化 ----------

    def _load_from_disk(self) -> None:
        """
        从 logs/cache.json 加载历史缓存到内存。

        容错设计：
        - 文件不存在 → 跳过（首次启动正常情况）
        - JSON 格式损坏 → 打印警告，降级为空缓存启动
        - 加载时同步过滤过期条目，不给内存装垃圾
        """
        if not CACHE_FILE.exists():
            return  # 首次启动，无历史缓存

        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            # 逐条扫描，筛掉过期条目
            valid_entries = 0
            expired_entries = 0
            for key, entry in raw_data.items():
                if not isinstance(entry, dict):
                    continue
                if _is_expired(entry.get("expires_at", "")):
                    expired_entries += 1
                    continue
                self._cache[key] = entry
                valid_entries += 1

            if expired_entries > 0:
                print(f"[缓存] 启动时清理了 {expired_entries} 条过期缓存")

        except (json.JSONDecodeError, Exception) as e:
            print(f"[缓存] 加载磁盘缓存失败: {e}，降级为空缓存启动")
            self._cache = {}

    def _save_to_disk_unsafe(self) -> None:
        """
        将内存缓存全量写入磁盘（不加锁版本，调用者必须已持有 self._lock）。
        命名规则：_save_to_disk_unsafe → unsafe 表示"不在内部加锁"，由外层保证安全。
        """
        try:
            # 确保 logs 目录存在
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 磁盘写入失败不应该影响主流程，打印警告即可
            print(f"[缓存] 写入磁盘失败: {e}")

    # ---------- 管理功能 ----------

    def clear_all(self) -> int:
        """
        清空全部缓存（内存 + 磁盘）。
        
        返回:
            被清除的条目数量
        """
        count = len(self._cache)
        with self._lock:
            self._cache.clear()
            try:
                if CACHE_FILE.exists():
                    CACHE_FILE.unlink()  # 删除 JSON 文件
            except Exception as e:
                print(f"[缓存] 删除缓存文件失败: {e}")
            else:
                print(f"[缓存] 已清空全部 {count} 条缓存")
        return count

    def clear_expired(self) -> int:
        """
        只清空过期条目（内存 + 同步写磁盘）。
        
        返回:
            被清除的过期条目数量
        """
        expired_keys = []
        for key, entry in self._cache.items():
            if _is_expired(entry.get("expires_at", "")):
                expired_keys.append(key)

        if not expired_keys:
            return 0

        with self._lock:
            for key in expired_keys:
                self._cache.pop(key, None)
            self._save_to_disk_unsafe()

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息。

        返回字典包含：
          - total_queries:  总查询次数
          - cache_hits:     缓存命中次数
          - hit_rate:       命中率（0.0 ~ 1.0），格式化为百分比字符串
          - cache_size:     当前有效缓存条目数
          - model_breakdown: 各模型生成的缓存数量分布
        """
        hit_rate = 0.0
        if self.total_queries > 0:
            hit_rate = self.cache_hits / self.total_queries

        # 统计各模型的缓存数量
        model_breakdown: Dict[str, int] = {}
        for entry in self._cache.values():
            model = entry.get("model", "unknown")
            model_breakdown[model] = model_breakdown.get(model, 0) + 1

        return {
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "hit_rate": f"{hit_rate:.1%}",
            "cache_size": len(self._cache),
            "model_breakdown": model_breakdown,
        }


# ====================== 全局单例 ======================

# 运行期全局唯一实例，所有模块通过 get_cache() 获取同一个缓存对象
# 保证了 interactive_qa() 和任何其他地方查的是同一份缓存
_cache_instance: Optional[RAGCache] = None


def get_cache() -> RAGCache:
    """
    获取全局缓存单例。

    延迟初始化：第一次调用时创建，之后一直复用。
    这是 Python 中简单可靠的单例实现方式，避免了 __new__ 和 metaclass 的复杂性。
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RAGCache()
    return _cache_instance


# ====================== 独立运行测试 ======================

if __name__ == "__main__":
    cache = get_cache()

    # 测试1：基本读写
    cache.set("燕光逸是谁", "燕光逸是启明帝，当朝皇帝", model="qwen")
    result = cache.get("燕光逸是谁")
    assert result == "燕光逸是启明帝，当朝皇帝", f"测试1失败: {result}"
    print("✅ 测试1通过：基本读写")

    # 测试2：相同 query 大小写/空格容错
    result2 = cache.get("  燕光逸是谁  ")
    assert result2 == "燕光逸是启明帝，当朝皇帝", f"测试2失败: {result2}"
    print("✅ 测试2通过：大小写+空格容错")

    # 测试3：未命中返回 None
    result3 = cache.get("一个从未问过的问题XYZ")
    assert result3 is None, f"测试3失败: {result3}"
    print("✅ 测试3通过：未命中返回 None")

    # 测试4：命中次数统计
    stats = cache.get_stats()
    assert stats["total_queries"] == 3, f"测试4失败: {stats}"
    assert stats["cache_hits"] == 2, f"测试4失败: {stats}"
    print(f"✅ 测试4通过：统计正确 → {stats}")

    # 测试5：清空
    count = cache.clear_all()
    assert count == 1, f"测试5失败: {count}"
    assert cache.get("燕光逸是谁") is None, f"测试5失败：清空后还能查到"
    print("✅ 测试5通过：清空功能")

    # 测试6：JSON 持久化
    cache.set("持久化测试", "重启后应该还在", model="qwen")
    # 模拟重启：创建新实例（同一个 JSON 文件）
    cache2 = RAGCache()  # __init__ 会自动 _load_from_disk()
    result6 = cache2.get("持久化测试")
    assert result6 == "重启后应该还在", f"测试6失败: {result6}"
    cache2.clear_all()  # 清理
    print("✅ 测试6通过：JSON 持久化+重启恢复")

    print("\n🎉 全部 6 项测试通过！")
