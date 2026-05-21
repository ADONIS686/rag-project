# 报错记录与解决方法

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