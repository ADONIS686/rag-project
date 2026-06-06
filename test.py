# 在 F:\rag-project 根目录新建 test_log.py 跑一下：

from core.request_logger import log_request

# 模拟一条日志
rid = log_request(
    model="deepseek",
    query="用一句话解释RAG",
    input_tokens=80,
    output_tokens=120,
    cost=0.000044,
)

print(f"✅ 日志已写入，request_id = {rid}")
print(f"📁 查看: logs/requests_{__import__('time').strftime('%Y-%m-%d')}.jsonl")
