# rag/base_rag.py
# 适配 LangChain 1.3.1 最新版 | 零报错 | 直接运行
from langchain_community.chat_models import ChatTongyi
# ✅ 修复：PromptTemplate 移到 langchain_core 了
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

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
    template = """你是专业的文档问答助手，请严格根据提供的上下文回答问题。
文中【陛下】指代皇帝，结合上下文找出陛下对应的人名；
上下文中没有答案，必须回答：根据文档内容，我无法回答这个问题。
禁止编造信息，回答简洁准确。

上下文：
{context}

用户问题：
{question}
请根据上下文回答用户问题："""

    return PromptTemplate.from_template(template)

# ====================== 3. 构建RAG链 ======================
def get_rag_chain():
    # 加载向量库
    vector_store = load_vector_store()
    # 创建检索器
    retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVER_TOP_K})

    # 格式化文档
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

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
        if question.lower() == "退出":
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