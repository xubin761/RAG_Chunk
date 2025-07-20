import inspect
from langchain_core.documents.base import Document

# 查看Document类的属性和方法
print("Document类的属性和方法:")
print(inspect.getmembers(Document))

# 查看模块中定义的所有名称
print("\n模块中定义的所有名称:")
import langchain_core.documents.base as base_module
print(dir(base_module))