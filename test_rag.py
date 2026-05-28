import csv
import time
from datetime import datetime
from rag.base_rag import get_rag_chain, rewrite_query

# 初始化RAG链
qa_chain, retriever, generate_answer_chain, self_correction_chain = get_rag_chain()

def batch_test(test_cases_file: str, output_file: str):
    """
    批量运行测试用例，生成测试报告
    :param test_cases_file: 测试用例CSV文件路径

    :param output_file: 测试报告输出路径
    """
    # 读取测试用例
    test_cases = []
    with open(test_cases_file, 'r', encoding='utf-8') as f:
        #将 CSV 每一行数据转为字典，并添加到 test_cases 列表中
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append(row)
    
    # 运行测试
    results = []
    total = len(test_cases)
    for i, case in enumerate(test_cases):
        question = case["question"]
        print(f"\n[{i+1}/{total}] 正在测试：{question}")

        try:
            rewritten_question = rewrite_query({"question": question})
            print(f"  - 重写后的问题：{rewritten_question}")
            raw_answer = generate_answer_chain.invoke({"question": question, "rewritten_question": rewritten_question})
            print(f"  - 原始答案：{raw_answer}")
            final_answer = self_correction_chain.invoke({"question": question, "rewritten_question": rewritten_question, "answer": raw_answer})
            print(f"  - 最终答案：{final_answer}")

            # 记录结果
            results.append({
                #string format time = 把时间对象 → 格式化为字符串
                "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "question": question,
                "rewritten_question": rewritten_question,
                "raw_answer": raw_answer,
                "final_answer": final_answer,
                "expected_answer": case["expected_answer"],
                "test_type": case["test_type"],
                "is_pass": ""  # 留空给LLM-Judge后续自动打分
            })
            
            # 避免API调用过快
            time.sleep(0.5)
            
        except Exception as e:
            print(f"测试失败：{str(e)}")
            # 🔥 关键：已成功的值保留，没值的才给空
            results.append({
                "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "question": question,
                # 这里：如果已经算出 rewritten_question，就保留，没有才为空
                "rewritten_question": rewritten_question if 'rewritten_question' in locals() else "",
                "raw_answer": raw_answer if 'raw_answer' in locals() else "",
                "final_answer": f"测试报错：{str(e)}",
                "expected_answer": case["expected_answer"],
                "test_type": case["test_type"],
                "is_pass": "失败"
            })
    
    # 生成CSV报告
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ["test_time", "question", "rewritten_question", "raw_answer", "final_answer", "expected_answer", "test_type", "is_pass"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✅ 测试完成！报告已生成：{output_file}")
    return results

if __name__ == "__main__":
    # 运行Day10测试用例
    batch_test("standard_test_cases.csv", "test_report_day10.csv")
    