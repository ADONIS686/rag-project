"""
core/guardrails.py — 精简护栏系统（通用文档检索版）

职责：
  1. 输入护栏：敏感词过滤 + 空输入检查（调 LLM 之前拦截，零 Token 消耗）
  2. 输出护栏：强制 LLM 回答时标注引用来源 [chunk_N]，避免无凭据编造

设计思路（面试可讲）：
  这是典型的 "输入护栏 + 输出护栏" 双层架构。
  - 输入护栏：只保留安全底线（敏感词 + 空输入），不再用正则做"无关话题"拦截。
    原因：通用文档检索场景下，无法预知用户文档的主题，正则话题过滤会误拦正当问题。
    相关性判断交给检索器处理——相似度分数天然能区分相关和不相关。
  - 输出护栏：引用标注验证，LLM 返回后校验，确保不胡说

演进历史（面试亮点）：
  最初是三层输入护栏（敏感词 → 正则话题过滤 → 超短词拦截），
  在项目从"宫廷剧本专用"升级为"通用文档检索"后，
  砍掉了后两层。核心理念：检索器本身就是最好的相关性过滤器。

用法：
  from core.guardrails import check_query, apply_input_guard
"""

from typing import Tuple, Optional


# ============================================================
# 第一部分：敏感词黑名单
# ============================================================
# 命中这里任何一个词 → 直接拒答，不调 LLM
# 面试时可以说："这是最外层的安全护栏，零成本拦截"
SENSITIVE_KEYWORDS = [
    # 暴力/违法类
    "暴力", "色情", "赌博", "毒品", "枪支", "杀人", "炸弹",
    "贩毒", "走私", "诈骗", "黑客", "攻击网站",
    # 如需补充政治敏感词，在这里添加
    # "敏感词示例1", "敏感词示例2",
]


# ============================================================
# 拒答话术（统一管理，方便后续改文案）
# ============================================================
REJECT_SENSITIVE = "抱歉，此问题包含不当内容，我无法回答。"
REJECT_EMPTY     = "请输入您的问题。"


# ============================================================
# 核心判断函数
# ============================================================

def contains_sensitive_words(query: str) -> bool:
    """
    检查问题是否包含敏感词。

    实现细节：
      - 大小写不敏感
      - 时间复杂度 O(n * m)，n=query长度，m=敏感词数量
      - 对于几十个敏感词的场景，性能完全够用

    参数:
        query: 用户原始问题
    返回:
        True  → 包含敏感词，应拒答
        False → 安全，放行
    """
    query_lower = query.lower()
    for word in SENSITIVE_KEYWORDS:
        if word.lower() in query_lower:
            return True
    return False


# ============================================================
# 护栏总入口（一条龙检查）
# ============================================================

def check_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    护栏总入口：对用户问题执行两层检查（通用版，不限文档主题）。

    执行顺序采用短路逻辑（Short-Circuit）：
      1. 空输入检查 → 拒答
      2. 敏感词检查 → 拒答
      3. 全部通过   → 放行，让检索器自己判断相关性

    设计原则：
      "在通用文档检索场景下，检索器本身就是最好的相关性过滤器。
       输入护栏只负责安全底线，不替检索器做内容判断。"

    参数:
        query: 用户原始问题（可能是空字符串）

    返回:
        (是否放行, 拒答理由)
        - (True, None)    → 放行，继续检索+生成
        - (False, "xxx")  → 拦截，直接展示拒答话术，不调 LLM
    """
    # 第零关：空问题直接拒答
    if not query or not query.strip():
        return False, REJECT_EMPTY

    # 第一关：敏感词（安全底线，必须保留）
    if contains_sensitive_words(query):
        return False, REJECT_SENSITIVE

    # 放行 —— 相关性判断交给检索器
    return True, None


# ============================================================
# 便捷集成函数
# ============================================================
# 让 base_rag.py 里的调用只需要一行代码

def apply_input_guard(query: str) -> Optional[str]:
    """
    对用户输入执行护栏检查，返回拒答话术或 None。

    在 interactive_qa() 里的用法（只需要加 3 行）：

        reject_msg = apply_input_guard(question)
        if reject_msg:
            print(f"回答：{reject_msg}")
            continue  # 不调 LLM，直接进入下一轮

    参数:
        query: 用户输入的问题
    返回:
        - 被拦截 → 返回拒答话术字符串
        - 放行   → 返回 None
    """
    passed, reject_reason = check_query(query)
    if not passed:
        return reject_reason
    return None


# ============================================================
# 输出格式约束
# ============================================================
# 强制 LLM 在回答中标注引用来源，是输出护栏的核心。
# citation n.引文，引语
CITATION_INSTRUCTION = """
【引用标注规则 — 必须严格遵守】
1. 你的每一句回答，都必须标注信息来源：
   - 格式：[chunk_N] 文档名
   - N 是文档块编号，从 0 开始
   -如果某句话综合了多个文档块的信息，列出所有来源
2. 基于多个文档片段整合推断的结论属于正常归纳，无需逐句标注来源，可在末尾标注"基于文档整体推断"
3. 如果整个问题超出文档范围，回答："抱歉，此问题超出文档范围，我无法回答。"
4. 禁止输出任何没有标注来源的事实陈述。
"""


# ============================================================
# 自测代码（运行 `python core/guardrails.py` 即可验证）
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Guardrails 单元测试")
    print("=" * 60)

    # 定义测试用例：(问题, 期望被拦截吗？, 分类标签)
    test_cases = [
        # ---- 应该被拦截的（预期 True）----
        ("",                 True,  "空输入"),
        ("   ",              True,  "纯空格"),
        ("如何制作炸弹？",    True,  "敏感词"),
        ("贩卖毒品的方法",    True,  "敏感词"),

        # ---- 应该放行的（预期 False）----
        # 通用文档检索场景，不再预判"什么是无关话题"
        ("你好",              False, "短闲聊-放行"),
        ("今天天气怎么样？",   False, "闲聊话题-放行"),
        ("你叫什么名字？",     False, "AI身份-放行"),
        ("推荐一部好看的电影",  False, "无关话题-放行"),
        ("文档里提到了哪些人物？", False, "文档问题"),
        ("这篇文章讲的是什么？",   False, "文档问题"),
        ("好",               False, "单字回复-放行"),
        ("嗯",               False, "语气词-放行"),
        ("什么是人工智能",    False, "通用知识-放行"),
    ]

    passed = 0
    failed = 0

    for query, expect_reject, category in test_cases:
        should_pass, reason = check_query(query)
        is_rejected = not should_pass

        if is_rejected == expect_reject:
            status = "✅"
            passed += 1
        else:
            status = "❌"
            failed += 1

        actual   = "拦截" if is_rejected else "放行"
        expected = "拦截" if expect_reject else "放行"
        print(f"\n{status} [{category}] '{query}'")
        print(f"   实际: {actual} | 期望: {expected}")
        if is_rejected:
            print(f"   拒答话术: {reason}")

    print(f"\n{'=' * 60}")
    print(f"测试结果: {passed} 通过 / {failed} 失败 / {len(test_cases)} 总计")
    if failed == 0:
        print("✅ 全部通过！")
    else:
        print("❌ 有失败用例，请检查！")
    print(f"{'=' * 60}")
