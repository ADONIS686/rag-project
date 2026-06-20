# main.py 项目统一入口
from rag.base_rag import interactive_qa

if __name__ == "__main__":
    print("="*60)
    print("          SmartDoc RAG —— 智能文档检索增强生成系统")
    print("="*60)
    print("使用说明：")
    print("1. 输入你的问题，按回车得到答案")
    print("2. 输入'退出'或'q'，关闭程序")
    print("="*60)
    print()
    
    # 启动交互式问答
    interactive_qa()
