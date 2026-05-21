# rag/base_rag.py
# 适配 LangChain 1.3.1 最新版 | 零报错 | 直接运行
from langchain_community.chat_models import ChatTongyi
# ✅ 修复：PromptTemplate 移到 langchain_core 了
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from config.settings import ALLOW_DOC_NAMES

# 导入你的向量库和配置
from rag.vector_store import load_vector_store
from config.settings import (
    DASHSCOPE_API_KEY,
    LLM_MODEL_NAME,
    TEMPERATURE,
    RETRIEVER_TOP_K
)

# ====================== 1. 初始化大模型 ======================
def get_llm():
    return ChatTongyi(
        model=LLM_MODEL_NAME,
        temperature=TEMPERATURE,
        dashscope_api_key=DASHSCOPE_API_KEY
    )

# ====================== 2. 提示词模板 ======================
def get_prompt():
    template ="""
你是一个专业的文档问答助手，只能基于我提供给你的上下文文档回答问题。

【基础核心原则（必须严格遵守）】
1. 你的所有回答必须100%来自下面的上下文文档，绝对不能使用任何你自己的知识
2. 如果上下文文档中没有提到问题的答案，直接回答："文档中没有找到相关信息"
3. 绝对不能编造、猜测、推断任何文档中没有明确说明的内容
4. 回答要简洁、准确、直接，不要添加任何文档中没有的解释和延伸

【指代消解专项规则（核心升级，必须100%执行）】
5. 所有指代性称谓，包括但不限于：陛下、皇帝、皇上、圣上、新帝、当朝君主、他、她、这个人
若同一上下文片段内同时出现该称谓与具体人名，默认二者互相指代绑定
6. 无需文档出现“XX就是XX”直白定义句,依靠上下文同场出现关系即可判定身份
7. 回答中绝对禁止使用任何指代性称谓,必须直接使用从文档中提取的完整人名
8. 仅当全文所有检索片段都无任何可绑定的人名时,再回复：文档中没有明确说明
9. 绝对不能提前预设人物关系，所有绑定关系只来源于检索到的上下文文本

【回答格式要求】
10. 直接给出答案，不要说"根据文档"、"文中提到"等前缀
11. 答案要完整通顺，符合中文表达习惯
12. 如果问题有多个答案，用分号隔开

【禁止行为】
13. 禁止使用任何外部知识回答问题
14. 禁止编造文档中没有的内容
15. 禁止使用任何指代性称谓
16. 禁止对文档内容进行任何主观评价和解读

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

# 格式化文档（增强版：去重+过滤空内容+去除多余空格）
def format_docs(docs):
    # 第一步：过滤无关文档、空文档和内容过短的文档 # 过滤掉长度小于20的无效片段
    valid_docs = [
        doc
        for doc in docs 
        # 过滤条件：长度>20 + 仅目标文档
        if len(doc.page_content.strip()) > 20 
        #生成器表达式和列表易混淆：生成器表达式用圆括号()，返回的是generator对象；列表用方括号[]，返回的是列表对象。生成器更节省内存，适合大数据量；列表适合需要多次访问的情况。
        #any遇到一个True就break,返回True，效率更高；all需要全部True才行，效率较低
        and any(allow_name in doc.metadata["source"] for allow_name in ALLOW_DOC_NAMES)
    ]
    
    # 第二步：去重（去除内容完全一样的文档）
    # 1. 定义空列表：用来存放【去重后】的有效文档片段
    unique_docs = []

    # 2. 定义空集合：专门用来记录【已经出现过的文本内容】
    # 集合(set)的特点：查询速度极快，自动不允许重复值
    seen_contents = set()

    # 3. 遍历【第一步过滤好的有效文档】，逐个检查是否重复
    for doc in valid_docs:
        # 4. 取出当前文档的文本内容，并用strip()清洗首尾空格/换行
        content = doc.page_content.strip()

        # 5. 关键判断：如果这段文本【从来没出现过】
        if content not in seen_contents:
            # 6. 把这段文本标记为「已出现」，存入集合
            seen_contents.add(content)
            # 7. 把这个不重复的文档，加入最终的去重列表
            unique_docs.append(doc)

    # 第三步：拼接成最终上下文
    # 8. 把所有去重后的文档，提取纯文本，用 --- 分隔开，拼接成一整段字符串
    return "\n\n---\n\n".join(doc.page_content.strip() for doc in unique_docs)


# ====================== 3. 构建RAG链 ======================
def get_rag_chain():
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
            "fetch_k": 30,  # 先取20个最相似的候选
            "lambda_mult": 0.8  # 0.7=相似度优先，兼顾多样性；0 = 只看多样性，1 = 只看相似度，0.7 是通用最优值）
        }
    )
    # 新版标准RAG链 LangChain 专用流水线语法（LCEL）
    #把「检索文档→填提示词→AI 答题→转字符串」打包成一条全自动链条
    #符号 | = 管道符（上一步输出 → 下一步输入）
    #retriever：检索器 → 去向量库查3 条最相关文档； |：管道符 → 把查到的文档传给后面；format_docs：格式化函数 → 把文档拼接成纯文本 最终结果：上下文文本 填入 {context}
    #RunnablePassthrough() LangChain 工具 → 原样透传  把用户输入的问题原封不动传给提示词 用户问题 填入 {question}
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | get_prompt() #返回提示词模板对象； 输入：上一步的字典（context + question）；动作：自动把两个值填入 {context} {question} ；输出：完整的、发给 AI 的提示词
        | get_llm() #返回你的大模型（通义千问）输入：完整提示词；动作：AI 阅读上下文 + 思考 + 生成答案；输出：大模型原生响应对象（不是纯字符串）
        | StrOutputParser()#LangChain 解析器；输入：大模型复杂响应；动作：剥离多余信息，只保留文字答案；输出："燕光逸" / "根据文档内容，我无法回答这个问题"
    )
    return rag_chain, retriever


# ------------------- 函数4：交互式问答Demo -------------------
def interactive_qa():
    """
    【新手说明】：启动交互式问答，输入问题得到答案，输入'退出'结束
    """
    qa_chain, retriever = get_rag_chain()
    print("="*50)
    print("RAG问答系统启动成功！")
    print("输入你的问题，输入'退出'结束程序")
    print("="*50)
    
    while True:
        question = input("\n请输入你的问题：")
        if question.lower() in ["退出", "q"]:
            print("感谢使用，再见！")
            break
        
        print("\n正在检索答案，请稍候...")
        source_docs = retriever.invoke(question)
        answer = qa_chain.invoke(question)
        
        print(f"\n回答：{answer}")
        print("\n参考来源：")
        for i, doc in enumerate(source_docs):
            print(f"[{i+1}] {doc.metadata['source']}")
            print(f"    内容片段：{doc.page_content[:100]}...")

# ------------------- 新的测试代码 -------------------
if __name__ == "__main__":
    interactive_qa()