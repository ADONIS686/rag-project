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

### 2. 报错名称：
- 错误提示：(rag-project) PS F:\rag-project> & f:\rag-project\.venv\Scripts\python.exe f:/rag-project/rag/vector_store.py
Traceback (most recent call last):
  File "f:\rag-project\rag\vector_store.py", line 12, in <module>
    from config.settings import (
    ...<6 lines>...
    )
ModuleNotFoundError: No module named 'config'
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

### 3. 报错名称：
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
### 2. 报错名称：
- 错误提示：
- 原因：
- 解决方法：