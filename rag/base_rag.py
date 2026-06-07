# rag/base_rag.py
# 适配 LangChain 1.3.1 最新版 | 零报错 | 直接运行
from core.guardrails import CITATION_INSTRUCTION
from langchain_community.chat_models import ChatTongyi
# ✅ 修复：PromptTemplate 移到 langchain_core 了
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from config.settings import ALLOW_DOC_NAMES
# 新增全局随机种子固定
import random
import numpy as np
from core.guardrails import apply_input_guard

# 固定三方库随机种子，消除MMR检索随机性
SEED = 42
random.seed(SEED)
np.random.seed(SEED)


# 导入你的向量库和配置
from rag.vector_store import load_vector_store
from config.settings import (
    DASHSCOPE_API_KEY,
    LLM_MODEL_NAME,
    TEMPERATURE,
    RETRIEVER_TOP_K
)
# ====================== 查询重写配置（终极优化版） ======================
QUERY_REWRITE_PROMPT = """
你是一个专门处理宫廷剧本问答的问句改写助手。
你的唯一任务：将用户的原始问句改写成清晰、精准、适合检索的标准问句。

【绝对必须遵守的铁律（违反即错误）】
1. 一字不差保留原始问题的所有核心信息、主体和限定词
2. 仅替换模糊指代：他→文中提到的男性人物；她→文中提到的女性人物；这件事→文中描述的事件
3. 强制遍历问句全部文字，只要出现「陛下、皇帝、圣上」任意称谓，必须无条件统一替换为「燕光逸」，其余人物称谓、名词原样保留，不做改动
尤其「圣上XX」组合句式，务必完成称谓替换，其余人物称谓、名词原样保留，不做改动
4. 只优化语句通顺度，不添加、不删除、不修改任何原始问题的内容
5. 只输出改写后的问句，不要任何其他内容、解释或标点


【错误示例（绝对不能这么写）】
原始：燕光逸的母后是什么身份？
错误：燕光逸的生母身份是什么
正确：燕光逸的母后的身份是什么

原始：国丧阶段后宫有哪些限制要求？
错误：燕光逸在国丧阶段对后宫有哪些限制要求
正确：国丧阶段后宫有哪些限制要求

原始：四月为何严厉整顿后宫规矩？
错误：燕光逸为何在四月严厉整顿后宫规矩
正确：四月份严厉整顿后宫规矩的原因是什么

原始：太后日常居住在哪一处宫殿？
错误：燕光逸的生母太后日常居住的宫殿名称是什么
正确：太后日常居住的宫殿名称是什么

【基础示例】
原始：他是谁？
正确：文中提到的这个男性人物的姓名和身份是什么

原始：{question}
改写后：
"""
#仅输出最终结果，禁止附加解释、推理、多余标点
# ====================== 新增：自我纠正配置 ======================
SELF_CORRECTION_PROMPT = """
你是严格的答案审核员，结合用户问题与上下文文档，核验初步答案正误并修正。

【检查规则】
0. 上下文中的 [chunk_N] 是引用标注编号，不是答案错误，不要因此判定答案不正确
1.答案和文档内容、问题诉求完全匹配，直接原样输出
2.如果答案中出现了文档里没有的内容，且无法根据文档推断出来，说明答案错误，必须修正；如果答案中缺少了文档里明确提到的关键信息，说明答案不完整，必须补齐
3.如果答案错误，仅修正事实错误、关键信息缺漏，然后输出正确答案，**禁止在原答案基础上补充无关细节、背景推断、额外解读**
4.仅当上下文完全不存在和问题相关的描述、线索、行为记录时，才输出：文档中没有明确说明；存在相关线索、行为、场景描述时，必须基于已有内容作答。
5.如果你要改动原答案，仅输出修正后的「正确答案」，严格禁止输出任何解释、推理过程、修改痕迹、原答案内容、额外标点或多余文字，禁止输出思考过程
6.如果不需要改动原答案，仅输出原答案，禁止在原答案基础上添加任何附加解释、推理、多余标点
7.字面无明确佐证的内容且无法根据文档推断出来，不擅自增补进答案。
8.禁止无文档依据在原答案基础上做推测、推断类补充，要以原文为主。


用户问题：
{question}

上下文：
{context}

初步答案：
{answer}

最终答案：
"""


# ====================== 1. 初始化大模型 ======================
def get_llm(temperature: float = None):
    # 如果传入了临时温度，使用临时值；否则使用全局配置的默认温度
    use_temp = temperature if temperature is not None else TEMPERATURE
    return ChatTongyi(
        model=LLM_MODEL_NAME,
        dashscope_api_key=DASHSCOPE_API_KEY,
        model_kwargs={
            "temperature": use_temp,
            "top_p": 0.3
        }
    )

# ====================== 2. 提示词模板 ======================
def get_prompt():
    template ="""
你是一个专业的文档问答助手，仅依托提供的上下文文档作答。

【基础作答准则】
1. 所有内容均取自文档原文，不得使用自身知识，严禁编造、脑补文档未出现的人物、地名、情节细节
2. 全面提取相关信息，不刻意遗漏细节；模型原生答案为空或无有效内容统一回复：文档中没有明确说明
3. 介绍人物时，同步写出姓名与对应身份，表述客观平实
4. 依据文档内容合理梳理逻辑，仅结合已有文本关联信息整合答案

【指代与人名规范】
5. 陛下、皇上、新帝统一对应人名燕光逸，作答全程使用真实人名，不使用人称代词
6. 人物关系、身份归属以文档呈现内容为准，不私自预设设定

【场所与事件处理】
7. 仅依据文中实际出现的宫殿名称，结合活动场景判断居所，不凭空新增地名
8. 涉及事件缘由、过程、结果，严格依照文本信息通顺梳理

【输出格式要求】
9. 直接给出答案，无需额外开头铺垫语句
10. 多个人物、多处地点使用分号分隔；事件类内容条理通顺即可
11. 回答简洁明了直击重点，只回答提问的内容，与问题无关的内容不要过多提及，禁止冗长啰嗦

【通用禁止项】
12. 不得脱离文档拓展延伸，不做主观评价解读
13. 禁止删减关键有效信息作答


【引用标注规则 — 必须严格遵守】
{CITATION_INSTRUCTION}


上下文文档：
{context}

用户问题：{question}
"""

# """
# 依据检索到的所有文本内容作答，允许进行合理人物关系逻辑推导，不必局限于单一片段内容。
# 你可以使用大众通用的宫廷历史基础常识进行判断,遇到不清楚的可以联网搜索理解含义再作答


# 作答要求：
# 1. 可以整合多处信息串联得出答案，支持身份、亲属、称谓互相推导，称谓、本名、帝号、身份自由互换作答
# 2. 有明确对应关系直接简洁回答
# 3. 严禁编造原文不存在的人物与剧情
# 4. 结合基础身份常识，通读上下文，从文内原文找出每个称谓对应的专属人名
# 5. 严格依据文中描写的地位、职权、位份，区分皇后与普通后宫女子
# 6. 真正无任何相关信息，统一回复：根据文档内容，我无法回答这个问题
# 7. 最终答案只输出精准人名或标准固定话术，不额外多余解释
# 8. 询问名字、本名、真名，统一输出人物原生姓名
# 9. 所有指代性称谓（陛下、皇帝、他、她、这个人等），必须从你检索到的上下文文档中找到对应的具体人名
# 10. 回答中禁止使用任何指代性称谓，必须直接使用从文档中提取的具体人名
# 11. 如果上下文文档中没有明确说明指代的是谁，直接回答"文档中没有明确说明"



# 上下文：
# {context}

# 用户问题：
# {question}

# 按规则严谨作答："""
    return PromptTemplate.from_template(template)

# # 格式化文档（增强版：去重+过滤空内容+去除多余空格）
# def format_docs(docs):
#     # 第一步：过滤无关文档、空文档和内容过短的文档 # 过滤掉长度小于20的无效片段
#     valid_docs = [
#         doc
#         for doc in docs 
#         # 过滤条件：长度>20 + 仅目标文档
#         if len(doc.page_content.strip()) > 20 
#         #生成器表达式和列表易混淆：生成器表达式用圆括号()，返回的是generator对象；列表用方括号[]，返回的是列表对象。生成器更节省内存，适合大数据量；列表适合需要多次访问的情况。
#         #any遇到一个True就break,返回True，效率更高；all需要全部True才行，效率较低
#         and any(allow_name in doc.metadata["source"] for allow_name in ALLOW_DOC_NAMES)
#     ]
    
#     # 第二步：去重（去除内容完全一样的文档）
#     # 1. 定义空列表：用来存放【去重后】的有效文档片段
#     unique_docs = []

#     # 2. 定义空集合：专门用来记录【已经出现过的文本内容】
#     # 集合(set)的特点：查询速度极快，自动不允许重复值
#     seen_contents = set()

#     # 3. 遍历【第一步过滤好的有效文档】，逐个检查是否重复
#     for doc in valid_docs:
#         # 4. 取出当前文档的文本内容，并用strip()清洗首尾空格/换行
#         content = doc.page_content.strip()

#         # 5. 关键判断：如果这段文本【从来没出现过】
#         if content not in seen_contents:
#             # 6. 把这段文本标记为「已出现」，存入集合
#             seen_contents.add(content)
#             # 7. 把这个不重复的文档，加入最终的去重列表
#             unique_docs.append(doc)

#     # 第三步：拼接成最终上下文
#     # 8. 把所有去重后的文档，提取纯文本，用 --- 分隔开，拼接成一整段字符串
#     return "\n\n---\n\n".join(doc.page_content.strip() for doc in unique_docs)


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


# 保留旧函数做兼容（其他地方可能调用 format_docs）
def format_docs(docs):
    """旧版兼容，内部调新版"""
    return format_docs_with_chunks(docs)



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
    # 智能截断：只砍掉末尾陈述句、解释内容，保留完整疑问句
    # 以常见结束标点作为分割，只取最前方问句主体 我认为不需要，会误伤问句中本来就有的解释性内容，导致信息缺失；而且大模型已经被提示过「只输出改写后的问句，不要任何其他内容、解释或标点」，一般不会多余输出了，所以这里反而可能适得其反，造成重要信息被砍掉。
    # end_marks = ["。", "：", "；", "\uff1a"]
    # for mark in end_marks:
    #     if mark in rewritten_question:
    #         rewritten_question = rewritten_question.split(mark)[0].strip()
            
    # 兜底校验：防止清洗后为空
    if not rewritten_question:
        rewritten_question = original_question.strip()  # 最后再清洗一次，确保没有多余空格

    # 打印重写结果（方便调试）
    print(f"\n[查询重写] 原始问句：{original_question}")
    print(f"[查询重写] 改写后：{rewritten_question}")
    return rewritten_question

# ====================== 3. 构建RAG链 ======================
def get_rag_chain():
    # rag_chain = (
    #     # 第一步：接收用户原始问句
    #     {"question": RunnablePassthrough()}
    #     # 第二步：执行查询重写，生成rewritten_question
    #     | RunnablePassthrough.assign(rewritten_question=rewrite_query)
    #     # 第三步：用改写后的问句检索文档，同时保留原始问句给大模型
    #     | {
    #     #lambda x：匿名临时函数 x就代表上一步传过来的完整字典对象
    #     #检索器（向量库）很笨，必须用规整、无歧义、精准的改写问题才能找到正确文档；大模型很 “聪明”，能直接理解用户的原始口语 / 指代问题，必须用原问题才能生成自然、贴合用户意图的答案。所以这里同时传入两个版本的问题：一个给检索器（context），一个给大模型（question）。'''
    #     "context": RunnableLambda(lambda x: x["rewritten_question"]) | retriever | RunnableLambda(format_docs),
    #     "question": lambda x: x["question"]
    #     }
    #     # 第四步：生成答案
    #     | get_prompt()
    #     | get_llm()
    #     | StrOutputParser()
    # )

    # # 新版标准RAG链 LangChain 专用流水线语法（LCEL）
    # #把「检索文档→填提示词→AI 答题→转字符串」打包成一条全自动链条
    # #符号 | = 管道符（上一步输出 → 下一步输入）
    # #retriever：检索器 → 去向量库查3 条最相关文档； |：管道符 → 把查到的文档传给后面；format_docs：格式化函数 → 把文档拼接成纯文本 最终结果：上下文文本 填入 {context}
    # #RunnablePassthrough() LangChain 工具 → 原样透传  把用户输入的问题原封不动传给提示词 用户问题 填入 {question}
    # rag_chain = (
    #     {"context": retriever | format_docs, "question": RunnablePassthrough()}
    #     | get_prompt() #返回提示词模板对象； 输入：上一步的字典（context + question）；动作：自动把两个值填入 {context} {question} ；输出：完整的、发给 AI 的提示词
    #     | get_llm() #返回你的大模型（通义千问）输入：完整提示词；动作：AI 阅读上下文 + 思考 + 生成答案；输出：大模型原生响应对象（不是纯字符串）
    #     | StrOutputParser()#LangChain 解析器；输入：大模型复杂响应；动作：剥离多余信息，只保留文字答案；输出："燕光逸" / "根据文档内容，我无法回答这个问题"
    # )


    # 加载向量库
    vector_store = load_vector_store()
    # 创建检索器
    #retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVER_TOP_K})
    # 创建检索器（MMR多样性检索，彻底解决重复问题）
    retriever = vector_store.as_retriever(
        #最大边际相关性检索（Maximal Marginal Relevance），在保持相关性的同时增加结果的多样性，避免重复内容
        search_type="mmr",  # 核心：从默认的"similarity"改成"mmr"多样性检索
        search_kwargs={
            "k": RETRIEVER_TOP_K,  # 你刚才选的最优k值
            "fetch_k": 60,  # 先取x个最相似的候选
            "lambda_mult": 0.7,  # 0.7=相似度优先，兼顾多样性；0 = 只看多样性，1 = 只看相似度，0.7 是通用最优值）
            "random_state": SEED
            #"seed": SEED # 新版 LangChain 1.3.1 的 MMR 检索器参数改成了 "seed"，之前的 "random_state" 已经废弃了
        }
    )

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


# ------------------- 函数4：交互式问答Demo -------------------
def interactive_qa():
    """
    【新手说明】：启动交互式问答，输入问题得到答案，输入'退出'结束
    """
    qa_chain, retriever, generate_answer_chain, self_correction_chain= get_rag_chain()
    print("="*50)
    print("RAG问答系统启动成功！")
    print("输入你的问题，输入'退出'结束程序")
    print("="*50)
    
    while True:
        question = input("\n请输入你的问题：")
        if question.lower() in ["退出", "q"]:
            print("感谢使用，再见！")
            break
        question = question.strip()
        
        print("\n正在检索答案，请稍候...")
        answer = qa_chain.invoke(question)
        print(f"\n回答：{answer}")
        if not check_citations(answer):
            print("⚠️ 注意：本次回答未标注引用来源")

# ------------------- 函数4：交互式问答Demo（测试版：显示两次答案） -------------------
#测试完毕应注释掉使用原版函数，避免重复打印重写日志
def interactive_qa():
    """
    【新手说明】：启动交互式问答，输入问题得到答案，输入'退出'结束程序
    升级功能：同时显示原始初步答案、最终修正答案，以及两轮检索对应的参考来源
    """
    qa_chain, retriever, generate_answer_chain, self_correction_chain= get_rag_chain()
    print("="*50)
    print("RAG问答系统启动成功！")
    print("输入你的问题，输入'退出'结束程序")
    print("="*50)
    
    while True:
        question = input("\n请输入你的问题：")
        if question.lower() in ["退出", "q"]:
            print("感谢使用，再见！")
            break
        question = question.strip()

        reject_msg = apply_input_guard(question)

        if reject_msg:
            print(f"\n回答：{reject_msg}")
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

        # 打印结果（去掉重复的重写打印）
        print(f"\n【原始初步答案】：{raw_answer}")
        print(f"\n【最终修正答案】：{final_answer}")
        print("\n参考来源：")
        for i, doc in enumerate(source_docs):
            print(f"[{i+1}] {doc.metadata['source']}")
            print(f"    内容片段：{doc.page_content[:100]}...")


# ------------------- 新的测试代码 -------------------
if __name__ == "__main__":
    interactive_qa()