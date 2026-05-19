# script3_clean_space.py 去除字符串多余空格

# 定义一个函数，参数是原始字符串，返回值是清洗后的字符串
def clean_extra_spaces(text):
    # split()会把字符串按任意空白字符（空格、换行、制表符等）分割成列表
    # " ".join()会用单个空格把列表中的元素连接起来
    return " ".join(text.split())

# 程序入口
if __name__ == "__main__":
    # 原始字符串，有很多多余的空格
    raw_text = "  我     是  多  余  空  格  "
    # 打印清洗前的字符串
    print("清洗前：", raw_text)
    # 调用函数清洗字符串
    cleaned_text = clean_extra_spaces(raw_text)
    # 打印清洗后的字符串
    print("清洗后：", cleaned_text)