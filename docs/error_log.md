# 报错记录与解决方法
1：解决 GitHub 同步问题（永久生效）
新手解释：之前 GitHub 同步失败是因为远程地址配置错误，现在重新设置为你的仓库地址
终端执行以下命令（直接复制）：
powershell
# 1. 查看当前远程地址（确认是否正确）
git remote -v
# 2. 设置为你的GitHub仓库地址
git remote set-url origin https://github.com/ADONIS686/rag-project.git
# 3. 拉取远程最新代码（避免冲突）
git pull origin main --allow-unrelated-histories
# 4. 推送本地所有提交
git push -u origin main
✅ 成功标准：
终端显示Everything up-to-date
刷新 GitHub 页面，能看到最新的 "Day5：升级提示词..." 提交记录


## Day1 报错记录
### 1. 报错名称：
- 错误提示：Author identity unknown
*** Please tell me who you are.

Run

  git config --global user.email "you@example.com"
  git config --global user.name "Your Name"

to set your account's default identity.
Omit --global to set the identity only in this repository.
- 原因：不知道作者
- 解决方法：终端告诉git谁是作者
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的GitHub邮箱"

### 2. 报错名称：ModuleNotFoundError: No module named 'config'
- 错误提示：(rag-project) PS F:\rag-project> & f:\rag-project\.venv\Scripts\python.exe f:/rag-project/rag/vector_store.py
Traceback (most recent call last):
  File "f:\rag-project\rag\vector_store.py", line 12, in <module>
    from config.settings import (
    ...<6 lines>...
    )
- 原因：Python 运行 rag/vector_store.py 时，找不到 config 模块，核心问题是：
你运行脚本时，Python 的「模块搜索路径」里没有包含你的项目根目录 F:\rag-project
当它执行 from config.settings import ... 时，只会在 rag/ 文件夹里找 config，而你的 config 文件夹在项目根目录，自然找不到
- 解决方法：
1.
// 在文件最顶部（所有import之前）添加这3行
import sys
from pathlib import Path
 //把项目根目录（F:\rag-project）加入Python搜索路径
sys.path.append(str(Path(__file__).parent.parent))
2.
//先激活虚拟环境（如果没激活的话）
.venv\Scripts\activate
//关键命令：从项目根目录运行rag模块下的vector_store.py
python -m rag.vector_store
原理：-m 会自动把当前工作目录加入 Python 搜索路径，让它能找到 config

### 3. Day4 报错名称：ModuleNotFoundError: No module named 'langchain.prompts'
- 错误提示：(rag-project) PS F:\rag-project> & f:\rag-project\.venv\Scripts\python.exe f:/rag-project/rag/base_rag.py
Traceback (most recent call last):
  File "f:\rag-project\rag\base_rag.py", line 4, in <module>
    from langchain.prompts import PromptTemplate
- 原因：版本是 langchain 1.3.1（最新版），这个版本彻底删除了 RetrievalQA，全世界所有旧的导入方式都失效了！
- 解决方法：直接用新版官方标准写法（LCEL）
# rag/base_rag.py
# 适配 langchain 1.3.1 最新版 | 无RetrievalQA | 直接运行
from langchain_community.chat_models import ChatTongyi
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
### 2. 报错名称：
- 错误提示：
- 原因：
- 解决方法：
### 2. 报错名称：
- 错误提示：
- 原因：
- 解决方法：
### 2. 报错名称：
- 错误提示：
- 原因：
- 解决方法：
# error_log.md 今日day5 报错&问题记录
### 1. 报错名称：问答溯源展示混入无关test.pdf文档
- 错误提示：交互式问答**参考来源列表**依旧出现`data/raw\test.pdf`无关文档，仅最终答案不受影响
- 原因：
  1. 代码中`format_docs`函数仅对**送入大模型的上下文**做了`wenben1.pdf`文件过滤；
  2. 前端展示用的`source_docs = retriever.invoke(question)`是独立检索调用，没有添加文件筛选逻辑；
  3. 检索阶段未做元数据过滤，无关文档依旧会被正常召回展示。
- 解决方法：
  在循环打印参考来源处增加过滤判断，只打印目标文档，修改交互式输出代码：
  ```python
  # 替换原有来源打印逻辑
  print("\n参考来源：")
  show_docs = [d for d in source_docs if "wenben1.pdf" in d.metadata["source"]]
  for i, doc in enumerate(show_docs):
      print(f"[{i+1}] {doc.metadata['source']}")
      print(f"    内容片段：{doc.page_content[:100]}...")
  ```

### 2. 报错名称：同人物不同问句作答结果不一致
- 错误提示：
  问`文中的陛下是谁`偶尔回答错误/判定无信息；
  问`陛下叫什么名字`、`皇后配偶是谁`可正常答对，语义互通识别不稳定。
- 原因：
  1. 仅依靠提示词文字引导人物关系，无强制实体绑定，模型自主整合逻辑弱；
  2. MMR检索召回片段随机，部分片段只出现称谓、未同步出现对应本名，无法跨片段拼接信息；
  3. 后置过滤仅筛选文件，无法主动聚合分散的人物关系文本。
- 解决方法：
  1. 进一步强化`get_prompt`内部固定人物对应关系，明文写清双向绑定规则；
  2. 保持`fetch_k=30`高候选值，扩大召回范围，提高关联人物段落同时命中概率；
  3. 日常测试优先使用标准问句，口语化衍生问句延后做查询重写优化。

### 3. 报错名称：MMR多样性检索丢失部分精准核心语句
- 错误提示：切换`search_type="mmr"`后，部分专属称谓、小众剧情短句难以被优先检索到
- 原因：
  当前`lambda_mult=0.7`偏向兼顾内容多样性，压低了纯语义相似度权重，极致匹配短句排序靠后。
- 解决方法：
  修改检索器参数，调高相似度权重，平衡精准度与多样性
  ```python
  "lambda_mult": 0.8
  ```

### 4. 报错名称：检索结果仍存在少量高度重复文本片段
- 错误提示：已添加内容去重逻辑，依旧出现内容高度相似的文档片段
- 原因：
  1. 文本分块`chunk_overlap`重叠值偏大，拆分后产生大量近似重复文本；
  2. 现有去重仅判断**完全一致字符串**，无法过滤语义相近、文字略有差异的重复内容。
- 解决方法：
  1. 下周调整全局`CHUNK_OVERLAP`重叠字符数量，减少切片冗余；
  2. 后续新增语义层面去重逻辑，彻底剔除同类重复剧情片段。

### 5. 报错名称：无答案场景模型偶尔违规编造内容
- 错误提示：文档完全无相关信息时，模型偶尔整合无关文本作答，不执行固定回复话术
- 原因：
  1. 检索带入过多冗余长文本，干扰模型对「有无答案」的判断；
  2. 提示词约束语句优先级不足，容易被长上下文覆盖。
- 解决方法：
  1. 严格执行短文档过滤，过滤字符长度过低的无效碎片；
  2. 在提示词最前端置顶无答案强制回复规则，提升约束优先级。

### 6. 报错名称：ChromaDB向量库无法使用检索端filter过滤
- 错误提示：写入`"filter": {"source": {"$contains": "wenben1.pdf"}}`直接检索结果为空，查询失效
- 原因：
  当前使用的ChromaDB本地版本**不支持`$contains`这类元数据运算符**，仅支持精准等值匹配。
- 解决方法：
  彻底放弃检索层filter写法，全程沿用当前代码：**检索全量文档 + 后置Python代码过滤指定PDF文件**，稳定兼容无报错。


# error_log.md 今日day6 报错&问题记录
### 1. 报错名称：宫廷称谓指代消解失败
- 错误提示：询问**陛下、当朝皇帝、启明帝**身份时，AI回复「文档中没有明确说明」，无法正确识别称谓对应人物为燕光逸
- 原因：
  1. 初始检索召回数量不足（`k=3`），未抓取到完整的关联上下文；
  2. 原始提示词指代规则过于严格，仅识别直白定义句，无法通过**上下文同场出现**判定称谓与人名的指代关系。
- 解决方法：
  1. 调整检索参数，将`vector_store.as_retriever`的`k`值从3改为5，提升上下文召回量；
  2. 优化提示词指代规则，放宽判定逻辑，自动绑定同上下文内的宫廷称谓与人名，实现精准指代匹配。

# error_log.md 今日day7 报错&问题记录
### 1. 报错名称：Python管道符类型不支持错误
- 错误提示：`TypeError: unsupported operand type(s) for '|': 'list' and 'function'`，程序运行直接崩溃，无法执行问答流程
- **错误代码**：
```python
# 报错核心代码段
{
    "context": lambda x: retriever.invoke(x["rewritten_question"]) | format_docs,
    "question": lambda x: x["question"]
}
```
- 原因：
  1. **核心语法错误**：在 `lambda` 匿名函数中手动调用 `retriever.invoke()`，该方法会**立即执行检索**，返回结果是**文档列表（list）** 这类实际数据，而非 LangChain 的 `Runnable` 可运行对象；
  2. **管道符使用规则混淆**：LCEL 管道符 `|` 是 LangChain 专用语法，**仅支持连接 Runnable 可运行对象**（如 retriever、llm、prompt），不支持 Python 普通数据与普通函数直接拼接；
  3. **执行逻辑错误**：`invoke()` 是触发执行的方法，调用后链路终止，无法再用管道符衔接后续函数。
- 解决方法：
  1. **方案1（推荐，纯Python函数调用）**：移除管道符，将检索结果作为参数直接传入格式化函数：
  ```python
  "context": lambda x: format_docs(retriever.invoke(x["rewritten_question"])),
  ```
  2. **方案2（纯LCEL规范）**：使用 `RunnableLambda` 包装所有自定义函数，全程用管道符链式编写：
  ```python
  "context": RunnableLambda(lambda x: x["rewritten_question"]) | retriever | RunnableLambda(format_docs),
  ```


### 2. 问题名称：查询重写功能违规改写（核心业务问题）
- 错误提示：模型私自篡改用户问题，如`母后→生母`、`皇后整顿宫规→燕光逸整顿宫规`、`国丧规矩→燕光逸制定的国丧规矩`，导致检索匹配失败，最终回答`文档中没有找到相关信息`
- **错误代码/配置**：
  1. **旧版错误重写函数**（传参错误）：
  ```python
  # 错误：接收字符串参数，实际传入字典，导致改写逻辑混乱
  def rewrite_query(question: str) -> str:
      prompt = PromptTemplate.from_template(QUERY_REWRITE_PROMPT)
      rewrite_chain = prompt | get_llm() | StrOutputParser()
      return rewrite_chain.invoke({"question": question})
  ```
  2. **旧版无约束重写提示词**：无禁止规则，模型自主脑补内容
- 原因：
  1. **函数传参BUG**：`RunnablePassthrough.assign` 会自动传入完整字典，旧函数仅接收字符串，参数不匹配导致改写异常；
  2. **提示词规则缺失**：初始重写 Prompt 无严格约束，大模型凭借宫廷常识**私自添加限定词、替换问题主体**；
  3. **否定规则失效**：单纯禁止性话术对大模型约束力极低，模型会优先忽略规则，篡改原始问题语义；
  4. **指代逻辑错误**：将通用称谓（母后、太后）错误绑定为专属身份（生母），完全偏离文档内容。
- 解决方法：
  1. **修复重写函数**：修改为接收字典参数，正确提取问题字符串：
  ```python
  def rewrite_query(input_dict: dict) -> str:
      original_question = input_dict["question"]
      prompt = PromptTemplate.from_template(QUERY_REWRITE_PROMPT)
      rewrite_chain = prompt | get_llm() | StrOutputParser()
      return rewrite_chain.invoke({"question": original_question})
  ```
  2. **优化重写提示词**：新增**强制正向规则+禁止反例**，严格禁止模型增删修改问题主体和限定词；
  3. **规范改写逻辑**：仅优化语句通顺度，**100%保留原始问题的核心语义、主体、限定条件**。

---

### 3. 问题名称：回答信息不完整
状态：未完成优化
错误提示：检索参数已上调至k=5，改写语句合规，但作答依旧存在信息缺失。示例查询皇后四月生辰当天做了什么？，仅回复当日家宴、歇息相关内容，遗漏三月下旬上奏恳请罢黜庆典进贡、收受简约贺礼等前置关键行为
当前检索配置代码
python
运行
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,
        "fetch_k": 30,
        "lambda_mult": 0.8
    }
)
# 原因：
语义检索偏向性局限：改写问句聚焦当日行为，向量匹配优先抓取同期片段，跨时序筹备内容相似度偏低，无法有效召回；
文档切片碎片化：事件筹备、申请、当日活动拆分存储在不同文本块，单次检索难以串联完整时间线；
信息整合能力不足：模型仅独立解读单条片段，不会主动关联前后事件，忽略铺垫类关键信息。
# 待优化方案：
微调查询改写语义，放宽时间检索范围，兼容生辰前后关联事件；
调整 MMR 检索权重，平衡相似度与内容多样性，提升冷门片段召回概率；
优化问答提示词，要求模型整合多段内容，梳理完整事件脉络作答。
当前状态：问题依旧存在，相关优化工作延后至次日处理


# error_log.md 今日day8 报错&问题记录
### 报错名称：交互式问答函数参考来源与实际文档不匹配
- 错误提示：`interactive_qa()` 函数打印展示的参考来源文档，与 `qa_chain` 链路内部**实际生成答案、自我纠正**所用的检索文档不一致，调试信息失真
- 原因：
  1. 函数内手动调用 `retriever.invoke()` 获取文档仅用于打印展示；
  2. `generate_answer_chain`、`self_correction_chain` 内部均内置独立的 `retriever` 检索逻辑，会再次自动执行检索；
  3. 向量库采用MMR多样性检索，多次调用结果存在随机性，最终导致**打印的文档≠实际生成答案的文档**
- 解决方法：
  1. 拆分RAG链路分步执行，仅执行1次检索并复用结果，统一打印和业务调用的文档；
  2. 改造答案生成链、自我纠正链，取消内部自动检索，改为接收外部传入的上下文文档；
  3. 保证函数打印的参考来源，与链路实际使用的检索文档100%一致

# error_log.md 今日day10 报错&问题记录
## 问题 1：子链调用逻辑错误，代码直接报错
现象：误用 self_correction_chain 生成原始答案，且对字符串类型的返回值调用 .get()，触发 AttributeError: 'str' object has no attribute 'get'。
原因：混淆两条业务链职责，self_correction_chain 输出为纯字符串，并非字典，不能使用字典方法。
解决方案：
严格按照链路顺序调用：rewrite_query → generate_answer_chain → self_correction_chain；
修正入参：答案修正链必须传入 question / rewritten_question / raw_answer 三个字段。
## 问题 2：try 块部分代码执行成功后报错，中间数据全部丢失
现象：某条用例执行到后半段报错，except 块强制将 rewritten_question、raw_answer 置空，已成功生成的中间数据无法写入 CSV，不利于问题排查。
解决方案：
使用 变量名 if '变量名' in locals() else "" 语法：
变量已定义（代码执行成功）：保留原有值；
变量未定义（未执行就报错）：填充空字符串兜底。
## 问题 3：Windows 环境导出 CSV 出现大量多余空行
现象：CSV 数据行之间穿插空行，Excel/WPS 打开格式错乱。
原因：csv 库每行自动追加 \n，Windows 默认开启换行符自动转换，\n 转为 \r\n，最终叠加为 \r\n\r\n 双换行。
解决方案：
文件写入时固定添加 newline=''，关闭 Python 自动换行转换，保证全平台 CSV 格式统一。
## 问题 4：仅通过 str(e) 只能看到错误描述，无法定位具体报错行（）（实际未使用）
现象：报错信息模糊，不知道 try 代码块中哪一行代码触发异常，调试效率低。
解决方案：
顶部导入 import traceback；
在 except 块中添加 traceback.print_exc()，打印完整堆栈信息，精准定位文件、行号、报错代码。