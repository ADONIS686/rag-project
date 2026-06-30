# rag/base_rag.py
# 适配 LangChain 1.3.1 最新版 | 零报错 | 直接运行
from core.guardrails import CITATION_INSTRUCTION
#from langchain_community.chat_models import ChatTongyi
# ✅ 修复：PromptTemplate 移到 langchain_core 了
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from config.settings import ALLOW_DOC_NAMES
from core.guardrails import apply_input_guard
from core.cost_tracker import get_tracker
from core.llm_factory import create_llm
from core.cache import get_cache



# 导入你的向量库和配置
from rag.vector_store import load_vector_store
from config.settings import (
    TEMPERATURE,
    RETRIEVER_TOP_K
)
# ====================== 查询重写配置（终极优化版） ======================
QUERY_REWRITE_PROMPT = """
你是一个问句改写助手，适用于各类文档（小说、技术文档、论文、剧本等）。
你的唯一任务：将用户的原始问句改写成清晰、精准、适合向量检索的标准问句。

【绝对必须遵守的铁律（违反即错误）】
1. 一字不差保留原始问题的所有核心信息、主体和限定词
2. 仅替换模糊指代（代词→具体描述）：
   - 他/她 → 「文中提到的这个人物」
   - 它/这个 → 「文中提到的这个东西/概念」
   - 这件事/那次 → 「文中描述的这个事件」
   - 这里/那里 → 「文中提到的这个地点」
   如果原文已经包含具体名称，不做任何替换
3. 不修改任何专有名词、术语、人名、地名、产品名 —— 原样保留
4. 只优化语句通顺度（补全主语、理顺语序），不添加、不删除、不修改任何原始问题的内容
5. 只输出改写后的问句，不要任何其他内容、解释或标点


【错误示例（绝对不能这么写）】
原始：这个函数怎么用？
错误：请告诉我如何使用这个函数
正确：文中提到的这个函数的使用方法是什么

原始：第三章讲了什么？
错误：第三章的主要内容是什么
正确：第三章讲的内容是什么

原始：他为什么做这个决定？
错误：这个人物做这个决定的原因
正确：文中提到的这个人物做文中提到的这个决定的原因是什么


【基础示例】
原始：他是谁？
正确：文中提到的这个人物的姓名和身份是什么

原始：这个地方在哪里？
正确：文中提到的这个地点的位置是哪里

原始：{question}
改写后：
"""
#仅输出最终结果，禁止附加解释、推理、多余标点
# ====================== 新增：自我纠正配置 ======================
SELF_CORRECTION_PROMPT = """
你是严格的答案校验员，只能基于下方给定的上下文文档修正答案，绝对禁止使用任何外部知识。

【校验步骤（必须严格执行）】
第一步：逐一核对初步答案中的所有人名、地名、事件、书名，确认每一项都在上下文文档里出现过。
第二步：如果有任何内容或者额外的符号字母比如[chunk_数字]不在上下文里，就是幻觉，必须全部删除，只保留上下文能支撑的内容。
第三步：如果初步答案有信息遗漏，从上下文中补充对应的关键信息；如果初步答案正确，直接原样输出。
第四步：只输出最终修正后的答案正文，不要解释、不要推理、不要标注修改过程。

用户问题：
{question}

上下文文档：
{context}

初步答案：
{answer}

最终答案：
"""
# SELF_CORRECTION_PROMPT = """
# 你是严格的答案审核员，结合用户问题与上下文文档，核验初步答案正误并修正。

# 【检查规则】
# 0. 上下文中的 [chunk_N] 是引用标注编号，不是答案错误，不要因此判定答案不正确
# 0b. 如果初步答案是"文档中没有明确说明""超出范围""无法回答"等兜底回复，且上下文中确实没有能唯一确定答案的明确线索，禁止强行编造答案，直接原样输出初步答案
# 1.答案和文档内容、问题诉求完全匹配，直接原样输出
# 2.如果答案中出现了文档里没有的内容，且无法根据文档推断出来，说明答案错误，必须修正；如果答案中缺少了文档里明确提到的关键信息，说明答案不完整，必须补齐
# 2b.修正答案时，只能使用上下文文档中实际出现的人名、地名、术语。禁止编造文档中不存在的任何名称
# 3.如果答案错误，仅修正事实错误、关键信息缺漏，然后输出正确答案，**禁止在原答案基础上补充无关细节、背景推断、额外解读**
# 4."文档中没有明确说明"仅用于文档确实对此话题零提及的情况；如果文档中出现了相关人名、事件、场景，即使没有一句话直接回答用户问题，也必须基于已出现的信息整合回答，严禁用"没有明确说明"敷衍
# 5.如果你要改动原答案，仅输出修正后的「正确答案」，严格禁止输出任何解释、推理过程、修改痕迹、原答案内容、额外标点或多余文字，禁止输出思考过程
# 6.如果不需要改动原答案，仅输出原答案，禁止在原答案基础上添加任何附加解释、推理、多余标点
# 7.字面无明确佐证的内容且无法根据文档推断出来，不擅自增补进答案。
# 8.禁止无文档依据在原答案基础上做推测、推断类补充，要以原文为主。


# 用户问题：
# {question}

# 上下文：
# {context}

# 初步答案：
# {answer}

# 最终答案：
# """


# ====================== 1. 初始化大模型 ======================

# 默认模型,后续可以通过输入 "switch 模型名" 来切换模型，模型名必须在 MODEL_CONFIG 里定义，或者是 "local"（切换到 Ollama 本地模型）
#千问系列建议在settings里直接改默认模型，前期白嫖千问切换比较频繁，MODEL_CONFIG来回改太麻烦
_RAG_MODEL = "qwen"
def get_llm(temperature: float = None):
    use_temp = temperature if temperature is not None else TEMPERATURE
    return create_llm(_RAG_MODEL, temperature=use_temp)


# def get_llm(temperature: float = None):
#     # 如果传入了临时温度，使用临时值；否则使用全局配置的默认温度
#     use_temp = temperature if temperature is not None else TEMPERATURE
#     return ChatTongyi(
#         model=LLM_MODEL_NAME,
#         dashscope_api_key=DASHSCOPE_API_KEY,
#         model_kwargs={
#             "temperature": use_temp,
#             "top_p": 0.3
#         }
#     )

# ====================== 2. 提示词模板 ======================
def get_prompt():
    template =f"""
你是一个文档问答助手，仅依托提供的上下文文档作答。

【最高优先级规则】
你只能使用下方【上下文文档】里的内容回答问题，绝对禁止使用你自身的任何知识、常识、小说储备。
如果上下文里没有答案，就如实说明，绝对不可以编造人物、情节、书名。
所有引用标注必须对应上下文里真实存在的 [chunk_N] 编号以及文档来源，禁止伪造引用。

【作答规则】
1. 答案信息可以分散在多个片段中，必须整合所有相关片段后归纳回答，禁止因单个片段没有直接陈述句就声称"文档未说明"。
2. 上下文中高频出现的人名、称谓，就是对应问题的核心答案，必须明确提取。
3. 仅当所有上下文片段完全不相关、没有任何对应线索时，才可回复：文档中没有明确说明。
4. 优先使用文档原文表述，不做同义替换，回答简洁直击重点，不要铺垫语句。


【引用标注规则 — 必须严格遵守】
{CITATION_INSTRUCTION}


上下文文档：
{{context}}

用户问题：{{question}}
"""

    return PromptTemplate.from_template(template)


# ============================================================
# 格式化文档（升级版：每个 chunk 标注编号 + 文档名）
# ============================================================
def format_docs_with_chunks(docs):
    """
    将检索到的文档格式化为 LLM 可用的上下文，
    同时给每个 chunk 加上 [chunk_N] 编号，方便 LLM 引用来源。
    
    参数:
        docs: 检索器返回的 Document 列表
    返回:
        带编号的纯文本上下文字符串，示例:
        [chunk_0] 来源：宫廷剧本全集.txt
        燕光逸是当朝皇帝，居住在养心殿...
        
        [chunk_1] 来源：宫廷剧本全集.txt
        太后日常居住于寿康宫...
    """
    # 第一步：过滤 + 去重（和原来一样）
    valid_docs = [
        doc for doc in docs
        if len(doc.page_content.strip()) > 20
        and any(allow_name in doc.metadata.get("source", "")
                for allow_name in ALLOW_DOC_NAMES)
    ]
    
    unique_docs = []
    seen_contents = set()
    for doc in valid_docs:
        content = doc.page_content.strip()
        if content not in seen_contents:
            seen_contents.add(content)
            unique_docs.append(doc)
    
    # 第二步：给每个 chunk 标编号 + 文档名
    chunks = []
    for i, doc in enumerate(unique_docs):
        # 从 metadata 里取文档名，如果取不到就用 "未知文档"
        source_name = doc.metadata.get("source", "未知文档")
        # 构建带编号的 chunk：[chunk_N] 来源：xxx.txt
        #两个相邻的字符串字面量（中间无运算符），会被自动拼接成一个完整字符串，所以这里的换行和缩进不会影响最终输出的格式，反而让代码更清晰易读了。
        chunk_text = (
            f"[chunk_{i}] 来源：{source_name}\n"
            f"{doc.page_content.strip()}"
        )
        chunks.append(chunk_text)
    
    # 用 --- 分隔，方便 LLM 区分不同 chunk
    return "\n\n---\n\n".join(chunks)


# ====================== 新增：查询重写函数 ======================
def rewrite_query(input_dict: dict) -> str:# ✅ 改成接收字典，不是字符串
    """
    【新手解释】
    把用户的模糊口语化问句改写成清晰的标准问句
    :param input_dict: 包含原始问句的字典，格式为 {"question": "用户的原始问句"}
    :return: 改写后的标准问句
    """
    # ✅ 从字典里提取原始问题字符串
    original_question = input_dict["question"]

    # 创建提示词模板
    prompt = PromptTemplate.from_template(QUERY_REWRITE_PROMPT)
    # 构建重写链：提示词 → 大模型 → 输出字符串
    rewrite_chain = prompt | get_llm() | StrOutputParser()
    # 执行重写
    rewritten_question = rewrite_chain.invoke({"question": original_question})


    # 基础空白清洗：去除换行、制表、首尾空格
    rewritten_question = rewritten_question.strip()
    rewritten_question = rewritten_question.replace("\n", "").replace("\r", "").replace("\t", "")

    # 兜底校验：防止清洗后为空
    if not rewritten_question:
        rewritten_question = original_question.strip()  # 最后再清洗一次，确保没有多余空格

    # 打印重写结果（方便调试）
    print(f"\n[查询重写] 原始问句：{original_question}")
    print(f"[查询重写] 改写后：{rewritten_question}")
    return rewritten_question

# ====================== 3. 构建RAG链 ======================
def get_rag_chain():


    # 加载多文档向量库检索器（VectorStoreManager → LangChain 兼容）
    retriever = load_vector_store(top_k=RETRIEVER_TOP_K)

    # ------------------- 第一步：生成初步答案（仅检索一次） -------------------
    generate_answer_chain = (
        RunnablePassthrough.assign(
            # 只做一次检索，生成 context
            ##检索器（向量库）很笨，必须用规整、无歧义、精准的改写问题才能找到正确文档；
            context=RunnableLambda(lambda x: x["rewritten_question"]) | retriever | RunnableLambda(format_docs_with_chunks)
        )
        | RunnablePassthrough.assign(
            # 复用 context 生成答案
            answer=(
                #大模型很 “聪明”，能直接理解用户的原始口语 / 指代问题，必须用原问题才能生成自然、贴合用户意图的答案。
                {"context": lambda x: x["context"], "question": lambda x: x["question"]}
                | get_prompt()
                | get_llm()
                | StrOutputParser()
            )
        )
    )

    # ------------------- 第二步：自我纠正 -------------------
    self_correction_chain = (
        {
            #token不够用了，先不复用了，直接把之前的检索结果传过来用着；后续如果想优化再想办法增加token预算或者改成分段纠正
            "context": RunnableLambda(lambda x: x["context"]),
            "answer": RunnableLambda(lambda x: x["answer"]),
            "question": RunnableLambda(lambda x: x["question"])
        }
        | PromptTemplate.from_template(SELF_CORRECTION_PROMPT)
        | get_llm()
        | StrOutputParser()
    )

# ------------------- 完整RAG链路 -------------------
    rag_chain = (
        # 1. 接收用户原始问句
        {"question": RunnablePassthrough()}
        # 2. 查询重写
        | RunnablePassthrough.assign(rewritten_question=rewrite_query)
        # 3. 生成初步答案
        | generate_answer_chain
        # 4. 自我纠正，得到最终答案
        | self_correction_chain
    )

    return rag_chain, retriever,generate_answer_chain,self_correction_chain

# ============================================================
# 引用标注校验（输出护栏）面试题时可以说：
# "我们设计了一个输出护栏，专门校验 LLM 的回答是否正确标注了引用来源，如果完全没有标注，就会触发重试机制，要求 LLM 重新生成答案。"
# ============================================================
def check_citations(answer: str) -> bool:
    """
    检查 LLM 回答是否包含 [chunk_N] 格式的引用标注。
    
    如果没有引用 → LLM 可能忽略了你给的标注规则 → 建议重新生成。
    
    参数:
        answer: LLM 生成的回答文本
    返回:
        True  → 至少有一个 [chunk_N] 引用
        False → 完全没有引用标注
    """
    import re
    #\d+ 匹配一个或多个数字，\[ 和 \] 匹配字面上的方括号，整体匹配 [chunk_0]、[chunk_1] 等格式的引用标注
    return bool(re.search(r"\[chunk_\d+\]", answer))



# ------------------- 当前版本：交互式问答Demo（显示两次答案 + 成本统计） -------------------
def interactive_qa():
    """
    【新手说明】：启动交互式问答，输入问题得到答案，输入'退出'结束程序
    升级功能：同时显示原始初步答案、最终修正答案，以及两轮检索对应的参考来源
    """
    qa_chain, retriever, generate_answer_chain, self_correction_chain= get_rag_chain()
    cache = get_cache()
    print("="*50)
    print("RAG问答系统启动成功！")
    print("输入你的问题，输入'退出'结束程序")
    print("="*50)
    
    while True:
        question = input("\n请输入你的问题：")
        if question.lower() in ["退出", "q"]:
            tracker = get_tracker()
            stats = tracker.summary()
            if stats["total_calls"] > 0:
                print(f"\n本次会话统计：")
                print(f"  总调用次数：{stats['total_calls']}")
                print(f"  总输入Token：{stats['total_input_tokens']}")
                print(f"  总输出Token：{stats['total_output_tokens']}")
                print(f"  总费用：¥{stats['total_cost']:.4f}")
                #.items()把一个字典，转换成 (键, 值) 格式的元组列表，用于遍历键值对
                for model, mstat in stats["by_model"].items():
                    print(f"  [{model}] {mstat['calls']}次 ¥{mstat['cost']:.4f}")
            print("感谢使用，再见！")
            break
        question = question.strip()
        # 模型切换命令
        if question.lower().startswith("switch "):
            model_name = question.split()[1].strip()
            if model_name in ("qwen", "deepseek", "deepseek_flash", "kimi", "local"):
                global _RAG_MODEL
                _RAG_MODEL = model_name
                print(f"✅ 已切换到 {model_name}")
            else:
                print(f"❌ 未知模型: {model_name}，可用: qwen/deepseek/kimi/local")
            continue
        reject_msg = apply_input_guard(question)

        if reject_msg:
            print(f"\n回答：{reject_msg}")
            continue

        cached = cache.get(question)
        if cached is not None:
            print(f"\n[缓存命中 ⚡] 零 Token 消耗")
            print(f"\n回答：{cached}")
            continue
        
        print("\n正在检索答案，请稍候...")

        # 分步执行链路，捕获所有中间结果（重写函数内部会自动打印重写日志）
        #拿到改写过的问题
        step1_result = {"question": question}
        step2_result = RunnablePassthrough.assign(rewritten_question=rewrite_query).invoke(step1_result)
        
        # 步骤1：初次检索+生成初步答案
        step3_result = generate_answer_chain.invoke(step2_result)
        raw_answer = step3_result["answer"]
        #拿到改写问题对应的检索文档（给后续纠正链使用）
        source_docs = retriever.invoke(step2_result["rewritten_question"])
        if not source_docs:
            print("\n回答：抱歉，当前文档库为空，请先导入文档。")
            continue

        # 步骤2：矫正阶段检索+生成最终答案
        final_answer = self_correction_chain.invoke(step3_result)
        cache.set(query=question, answer=final_answer, model=_RAG_MODEL)
        # 打印结果（去掉重复的重写打印）
        print(f"\n【原始初步答案】：{raw_answer}")
        print(f"\n【最终修正答案】：{final_answer}")
        # 过滤：只显示实际喂给 LLM 的有效 chunk
        valid_source_docs = [
            doc for doc in source_docs
            if len(doc.page_content.strip()) > 20
            and any(allow_name in doc.metadata.get("source", "")
                    for allow_name in ALLOW_DOC_NAMES)
        ]
        # 去重
        unique_source_docs = []
        seen = set()
        for doc in valid_source_docs:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                unique_source_docs.append(doc)

        print("\n参考来源：")
        for i, doc in enumerate(unique_source_docs[:5]):
            print(f"[{i+1}] {doc.metadata['source']}")
            print(f"    内容片段：{doc.page_content[:100]}...")


# ------------------- 新的测试代码 -------------------
if __name__ == "__main__":
    interactive_qa()