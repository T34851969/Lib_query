"""查找Excel文件"""
from pathlib import Path

def find_excel():
    """在当前目录中查找Excel文件，返回路径或 None"""
    current_dir = Path.cwd()
    excel_files = []
    # 查找所有Excel文件
    for file in current_dir.glob("*.xlsx"):
        excel_files.append(file)
    for file in current_dir.glob("*.xls"):
        excel_files.append(file)

    if len(excel_files) == 0:
        print("错误：当前目录中无Excel文件")
        return None
    elif len(excel_files) == 1:
        print(f"找到Excel文件: {excel_files[0].name}")
        return str(excel_files[0])
    else:
        print("找到多个Excel文件，请选择:")
        for i, file in enumerate(excel_files, start=1):
            print(f"{i}: {file.name}")
        while True:
            try:
                choice = int(input("请输入文件编号: "))
                if 1 <= choice <= len(excel_files):
                    print(f"选择的文件: {excel_files[choice-1].name}")
                    return str(excel_files[choice-1])
                else:
                    print(f"错误：编号 {choice} 不在范围内，请重新输入。")
            except ValueError:
                print("错误：请输入整数。")
