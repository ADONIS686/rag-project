# script1_read_file.py 读取文本文件

# 定义一个函数，参数是文件路径，返回值是文件内容
def read_txt_file(file_path):
    # 使用with open语句打开文件，这是Python中最安全的文件打开方式
    # "r"表示只读模式，encoding="utf-8"表示使用UTF-8编码读取中文
    with open(file_path, "r", encoding="utf-8") as f:
        # 读取文件的全部内容
        return f.read()

# 程序入口
if __name__ == "__main__":
    # 调用函数，传入test.txt的路径
    text = read_txt_file("data/test.txt")
    # 打印文件内容
    print("文件内容：\n", text)