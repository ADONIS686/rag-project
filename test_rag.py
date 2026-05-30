import csv
import time
from datetime import datetime
from rag.base_rag import get_rag_chain, rewrite_query
# 新增：导入LLM-Judge需要的模块
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from rag.base_rag import get_llm  # 复用项目已有的大模型实例

# 初始化RAG链
qa_chain, retriever, generate_answer_chain, self_correction_chain = get_rag_chain()

# ====================== LLM-Judge 语义评测配置 ======================
LLM_JUDGE_PROMPT = """
你是一个严格、客观的答案评测专家，请根据【预期答案】和【实际答案】的语义相似度进行评分。

【评分标准】
- 1分：实际答案完全正确，语义与预期答案完全一致
- 1分：实际答案包含预期答案全部核心信息，仅表述形式略有差异，同时补充了部分额外内容，但不影响核心信息的正确性
- 0.5分：实际答案部分正确，包含预期答案的核心信息，但有少量遗漏或多余内容
- 0分：实际答案完全错误，与预期答案语义不符，或编造了不存在的信息

【输出要求】
1. 必须严格输出JSON格式，不能有任何其他内容
2. JSON必须包含两个字段：
   - "score": 浮点数，只能是0、0.5或1
   - "reason": 字符串，简要说明评分原因
3. 禁止输出任何解释、说明、标点或多余内容

【输入】
预期答案：{expected_answer}
实际答案：{final_answer}

【输出JSON】
"""

def llm_judge(expected_answer: str, final_answer: str) -> tuple[float, str]:
    """
    【新手解释】
    调用大模型作为评委，从语义层面判断答案是否正确
    :param expected_answer: 测试用例中的预期答案
    :param final_answer: RAG系统生成的最终答案
    :return: (评分: 0/0.5/1, 评分原因)
    """
    # 初始化大模型（温度设为0，保证输出稳定）
    llm = get_llm(temperature=0)
    
    # 创建Prompt模板和JSON解析器
    prompt = PromptTemplate.from_template(LLM_JUDGE_PROMPT)
    parser = JsonOutputParser()
    
    # 构建LLM-Judge链
    judge_chain = prompt | llm | parser
    
    try:
        # 调用大模型进行评分
        result = judge_chain.invoke({
            "expected_answer": expected_answer,
            "final_answer": final_answer
        })
        return float(result["score"]), result["reason"]
    except Exception as e:
        print(f"LLM-Judge调用失败：{str(e)}")
        # 调用失败时默认返回0分，避免脚本崩溃
        return 0.0, f"LLM-Judge调用失败：{str(e)}"

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
    total_score = 0.0  # 总得分
    type_stats = {}    # 按类型统计得分
    
    # 运行测试
    results = []
    total = len(test_cases)
    for i, case in enumerate(test_cases):
        question = case["question"]
        expected_answer = case["expected_answer"]
        test_type = case["test_type"]
        print(f"\n[{i+1}/{total}] 正在测试：{question}")
        try:
            rewritten_question = rewrite_query({"question": question})
            print(f"  - 重写后的问题：{rewritten_question}")
            generate_chain= generate_answer_chain.invoke({"question": question, "rewritten_question": rewritten_question})
            raw_answer = generate_chain["answer"]
            print(f"  - 原始答案：{raw_answer}")
            final_answer = self_correction_chain.invoke(generate_chain)
            print(f"  - 最终答案：{final_answer}")

            # 新增：调用LLM-Judge自动评分
            score, reason = llm_judge(expected_answer, final_answer)
            print(f"  - LLM-Judge评分：{score}分")
            print(f"  - 评分原因：{reason}")
            # 统计总得分
            total_score += score

            # 按类型统计得分
            if test_type not in type_stats:
                type_stats[test_type] = {"total": 0, "score": 0.0}
            type_stats[test_type]["total"] += 1
            type_stats[test_type]["score"] += score

            # 记录结果
            results.append({
                #string format time = 把时间对象 → 格式化为字符串
                "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "question": question,
                "rewritten_question": rewritten_question,
                "raw_answer": raw_answer,
                "final_answer": final_answer,
                "expected_answer": expected_answer,
                "test_type": test_type,
                "score": score,
                "reason": reason,
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
                "expected_answer": expected_answer,
                "test_type": test_type,
                "score": 0.0,
                "reason": f"测试报错：{str(e)}",
                "is_pass": "失败"
            })
    # 计算整体准确率
    overall_accuracy = total_score / total * 100
    print(f"\n✅ 测试完成！")
    print(f"📊 整体准确率：{overall_accuracy:.2f}%")
    print(f"📈 各类型准确率：")
    for test_type, stats in type_stats.items():
        type_accuracy = stats["score"] / stats["total"] * 100
        print(f"  - {test_type}：{type_accuracy:.2f}% ({stats['score']:.1f}/{stats['total']})")    
    
    # 生成CSV报告
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ["test_time", "question", "rewritten_question", "raw_answer", "final_answer", "expected_answer", "test_type", "score", "reason", "is_pass"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✅ 测试完成！报告已生成：{output_file}")
    return results, overall_accuracy, type_stats

if __name__ == "__main__":
    # 运行Day10测试用例
    batch_test("standard_test_cases.csv", "test_report_day12.csv")
    