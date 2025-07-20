from src.utils.models import Document, Chunk
from datetime import datetime

# 创建一个测试块
chunk = Chunk(
    page_content="测试内容",
    chunk_id="chunk_1",
    chunk_size=100,
    chunk_overlap=10,
    chunk_method="fixed_size",
    metadata={"key": "value"}
)

# 创建一个测试文档
document = Document(
    page_content="文档内容",
    document_id="doc_1",
    file_name="test.txt",
    file_type="txt",
    file_path="/path/to/test.txt",
    chunks=[chunk],
    total_chunks=1,
    total_size=100,
    metadata={"document_key": "document_value"},
    loader_used="TextLoader",
    loader_params={"encoding": "utf-8"}
)

# 测试转换为LangChain文档
langchain_doc = document.to_langchain_document()
print("成功创建Document和Chunk对象")
print(f"文档ID: {document.document_id}")
print(f"块ID: {document.chunks[0].chunk_id}")
print(f"LangChain文档元数据: {langchain_doc.metadata}")