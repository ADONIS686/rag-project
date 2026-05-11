# script2_scan_folder.py 遍历文件夹获取文件信息

# 导入os模块，用来操作文件和文件夹
import os

# 定义一个函数，参数是文件夹路径
def scan_folder(folder_path):
    # 遍历文件夹中的所有文件和子文件夹
    for file_name in os.listdir(folder_path):
        # 拼接文件的完整路径
        file_path = os.path.join(folder_path, file_name)
        # 判断是否是文件（不是文件夹）
        if os.path.isfile(file_path):
            # 获取文件大小（单位：字节）
            file_size = os.path.getsize(file_path)
            # 打印文件名和大小
            print(f"文件名：{file_name} | 大小：{file_size} 字节")

# 程序入口
if __name__ == "__main__":
    # 调用函数，传入data文件夹的路径
    scan_folder("data")