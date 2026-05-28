import csv
import time
from datetime import datetime
from rag.base_rag import get_rag_chain

# 接收5个返回值：新增 rewrite_chain
qa_chain, retriever, rewrite_chain, generate_answer_chain, self_correction_chain = get_rag_chain()

def batch_test(test_cases_file: str, output_file: str):
    """
    批量运行测试用例，生成测试报告
    :param test_cases_file: 测试用例CSV文件路径
    :param output_file: 测试报告输出路径
    """
    # 读取测试用例
    test_cases = []
    with open(test_cases_file, 'r', encoding='utf-8') as f:
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
            # 分步执行独立子链（逻辑和交互式问答完全对齐）
            step1 = {"question": question}

            # 1. 执行查询重写子链
            step2 = rewrite_chain.invoke(step1)
            rewritten_question = step2["rewritten_question"]
            print(f"  - 重写后的问题：{rewritten_question}")

            # 2. 执行初步答案生成子链
            step3 = generate_answer_chain.invoke(step2)
            raw_answer = step3["answer"]

            # 3. 执行自我纠正子链
            step4 = {
                "question": question,
                "rewritten_question": rewritten_question,
                "answer": raw_answer
            }
            final_answer = self_correction_chain.invoke(step4)

            # 记录结果
            results.append({
                "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "question": question,
                "rewritten_question": rewritten_question,
                "raw_answer": raw_answer,
                "final_answer": final_answer,
                "expected_answer": case["expected_answer"],
                "test_type": case["test_type"],
                "is_pass": ""
            })
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"测试失败：{str(e)}")
            results.append({
                "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "question": question,
                "rewritten_question": "",
                "raw_answer": "",
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
    batch_test("test_cases.csv", "test_report_day10.csv")