from src.loaders.loaders import load_file
import tempfile
import os

# 创建一个临时文本文件进行测试
temp_dir = tempfile.gettempdir()
temp_file_path = os.path.join(temp_dir, "test_file.txt")

with open(temp_file_path, "w", encoding="utf-8") as f:
    f.write("这是一个测试文件内容。\n这是第二行。")

# 测试加载文件
try:
    document = load_file(temp_file_path)
    print("成功加载文件!")
    print(f"文档ID: {document.document_id}")
    print(f"文件名称: {document.file_name}")
    print(f"文件类型: {document.file_type}")
    print(f"文件路径: {document.file_path}")
    print(f"分块数量: {document.total_chunks}")
    print(f"块ID: {document.chunks[0].chunk_id}")
    print(f"块内容: {document.chunks[0].page_content}")
except Exception as e:
    print(f"加载文件时出错: {e}")
finally:
    # 清理临时文件
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)