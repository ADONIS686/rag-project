# test_api.py 通义千问API连通性测试

# 导入需要的库
# 从langchain_community导入通义千问的聊天模型
from langchain_community.chat_models import ChatTongyi
# 导入os模块，用来读取环境变量
import os

# 导入dotenv库，用来加载.env文件中的环境变量
from dotenv import load_dotenv

# 加载config/.env文件中的环境变量
load_dotenv("config/.env")

# 初始化通义千问大模型
# model="qwen-turbo"：使用通义千问的turbo模型，速度快，成本低
# temperature=0：设置温度为0，让模型的回答尽可能确定、准确，没有随机性
llm = ChatTongyi(model="qwen-plus", temperature=0)

# 程序入口qwen-max
if __name__ == "__main__":
    # 调用大模型，传入问题"你好"
    response = llm.invoke("你好")
    # 打印大模型的回答
    print("API调用成功：", response.content)