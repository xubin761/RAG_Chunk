from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import hashlib
from typing import Dict, List, Any
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document as LangChainDocument
from langchain_community.document_loaders import (PyPDFLoader, Docx2txtLoader,
                                               UnstructuredMarkdownLoader, UnstructuredExcelLoader,
                                               UnstructuredPowerPointLoader, TextLoader as LangChainTextLoader)
from src.utils.models import Document as RAGDocument, Chunk

class LangChainFileLoader(BaseLoader):
    def __init__(self, file_path: str, **kwargs):
        self.file_path = Path(file_path)
        self.kwargs = kwargs
        self.file_type = self._detect_file_type()
        self.metadata = self._base_metadata()
        self.loader = self._create_loader()

    def _generate_document_id(self) -> str:
        """生成文档唯一ID"""
        file_hash = hashlib.md5(str(self.file_path).encode()).hexdigest()
        timestamp = datetime.now().isoformat()
        return f"doc_{file_hash}_{timestamp[:10]}"

    def _detect_file_type(self) -> str:
        suffix = self.file_path.suffix.lower()
        return suffix[1:] if suffix else 'unknown'

    def _base_metadata(self) -> Dict[str, Any]:
        return {
            'file_name': self.file_path.name,
            'file_path': str(self.file_path.absolute()),
            'file_size': self.file_path.stat().st_size if self.file_path.exists() else 0,
            'file_type': self.file_type,
            'loaded_at': datetime.now().isoformat(),
            'loader_params': self.kwargs
        }

    def _create_loader(self) -> BaseLoader:
        """根据文件类型创建对应的LangChain加载器"""
        file_ext = self.file_path.suffix.lower()

        if file_ext == '.pdf':
            return PyPDFLoader(
                file_path=str(self.file_path),
                password=self.kwargs.get('password', ''),
                extract_images=self.kwargs.get('extract_images', False)
            )
        elif file_ext == '.md':
            return UnstructuredMarkdownLoader(
                file_path=str(self.file_path),
                mode=self.kwargs.get('mode', 'single'),
                encoding=self.kwargs.get('encoding', 'utf-8')
            )
        elif file_ext in ['.docx', '.doc']:
            return Docx2txtLoader(str(self.file_path))
        elif file_ext in ['.txt', '.csv', '.json']:
            return LangChainTextLoader(
                file_path=str(self.file_path),
                encoding=self.kwargs.get('encoding', 'utf-8'),
                autodetect_encoding=self.kwargs.get('autodetect_encoding', False)
            )
        elif file_ext in ['.xlsx', '.xls']:
            return UnstructuredExcelLoader(str(self.file_path))
        elif file_ext in ['.pptx', '.ppt']:
            return UnstructuredPowerPointLoader(str(self.file_path))
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    def load(self) -> List[LangChainDocument]:
        """使用LangChain加载器加载文档并返回标准Document对象列表"""
        return self.loader.load()

class PDFLoader(LangChainFileLoader):
    def load(self) -> RAGDocument:
        """加载PDF文件，支持页码范围、密码保护和提取模式等参数"""
        loader = PyPDFLoader(
            file_path=str(self.file_path),
            password=self.kwargs.get('password', ''),
            extract_images=self.kwargs.get('extract_images', False)
        )
        documents = loader.load()

        content = "\n\n".join([doc.page_content for doc in documents])
        metadata = {**self.metadata, **{'loader_used': 'PDFLoader'}}

        # 添加PDF特定元数据
        if documents and hasattr(documents[0], 'metadata'):
            metadata['total_pages'] = len(documents)
            metadata['pdf_version'] = documents[0].metadata.get('pdf_version', 'unknown')

        return RAGDocument(
            page_content=content,
            document_id=self._generate_document_id(),
            file_name=self.file_path.name,
            file_type=self.file_type,
            file_path=str(self.file_path),
            chunks=[Chunk(
                chunk_id=f"chunk_{self._generate_document_id()}_0",
                page_content=content,
                metadata=metadata,
                chunk_size=len(content),
                chunk_overlap=0,
                chunk_method='whole_document'
            )],
            metadata=metadata,
            total_chunks=1,
            total_size=len(content),
            loader_used='PDFLoader',
            loader_params=self.kwargs
        )

class MarkdownLoader(LangChainFileLoader):
    def load(self) -> RAGDocument:
        """加载Markdown文件，支持表格解析和元数据提取"""
        loader = UnstructuredMarkdownLoader(
            file_path=str(self.file_path),
            mode=self.kwargs.get('mode', 'single'),
            encoding=self.kwargs.get('encoding', 'utf-8')
        )
        documents = loader.load()

        content = "\n\n".join([doc.page_content for doc in documents])
        metadata = {**self.metadata, **{'loader_used': 'MarkdownLoader'}}

        return RAGDocument(
            page_content=content,
            document_id=self._generate_document_id(),
            file_name=self.file_path.name,
            file_type=self.file_type,
            file_path=str(self.file_path),
            chunks=[Chunk(
                chunk_id=f"chunk_{self._generate_document_id()}_0",
                page_content=content,
                metadata=metadata,
                chunk_size=len(content),
                chunk_overlap=0,
                chunk_method='whole_document'
            )],
            metadata=metadata,
            total_chunks=1,
            total_size=len(content),
            loader_used='MarkdownLoader',
            loader_params=self.kwargs
        )

class DocxLoader(LangChainFileLoader):
    def load(self) -> RAGDocument:
        """加载Word文档，支持段落提取和表格处理"""
        loader = Docx2txtLoader(
            file_path=str(self.file_path),
            encoding=self.kwargs.get('encoding', 'utf-8')
        )
        documents = loader.load()

        content = "\n\n".join([doc.page_content for doc in documents])
        metadata = {**self.metadata, **{'loader_used': 'DocxLoader'}}

        return RAGDocument(
            page_content=content,
            document_id=self._generate_document_id(),
            file_name=self.file_path.name,
            file_type=self.file_type,
            file_path=str(self.file_path),
            chunks=[Chunk(
                chunk_id=f"chunk_{self._generate_document_id()}_0",
                page_content=content,
                metadata=metadata,
                chunk_size=len(content),
                chunk_overlap=0,
                chunk_method='whole_document'
            )],
            metadata=metadata,
            total_chunks=1,
            total_size=len(content),
            loader_used='DocxLoader',
            loader_params=self.kwargs
        )

class CustomTextLoader(LangChainFileLoader):
    def load(self) -> RAGDocument:
        """加载文本文件，支持多种编码和行处理模式"""
        loader = LangChainTextLoader(
            file_path=str(self.file_path),
            encoding=self.kwargs.get('encoding', 'utf-8'),
            autodetect_encoding=self.kwargs.get('autodetect_encoding', False)
        )
        documents = loader.load()

        content = "\n\n".join([doc.page_content for doc in documents])
        metadata = {**self.metadata, **{'loader_used': 'TextLoader'}}

        return RAGDocument(
            page_content=content,
            document_id=self._generate_document_id(),
            file_name=self.file_path.name,
            file_type=self.file_type,
            file_path=str(self.file_path),
            chunks=[Chunk(
                chunk_id=f"chunk_{self._generate_document_id()}_0",
                page_content=content,
                metadata=metadata,
                chunk_size=len(content),
                chunk_overlap=0,
                chunk_method='whole_document'
            )],
            metadata=metadata,
            total_chunks=1,
            total_size=len(content),
            loader_used='TextLoader',
            loader_params=self.kwargs
        )

class FileLoaderFactory:
    @staticmethod
    def get_loader(file_path: str,** kwargs) -> LangChainFileLoader:
        """根据文件扩展名返回相应的加载器实例"""
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.pdf':
            return PDFLoader(file_path, **kwargs)
        elif file_ext == '.md':
            return MarkdownLoader(file_path,** kwargs)
        elif file_ext in ['.docx', '.doc']:
            return DocxLoader(file_path, **kwargs)
        elif file_ext in ['.txt', '.md', '.csv', '.json']:
            return CustomTextLoader(file_path,**kwargs)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

# 主函数用于直接调用
def load_file(file_path: str, **kwargs) -> RAGDocument:
    loader = FileLoaderFactory.get_loader(file_path,** kwargs)
    return loader.load()