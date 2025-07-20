from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
from abc import ABC, abstractmethod
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownTextSplitter
from langchain_core.documents import Document as LangChainDocument
from src.utils.models import Document as RAGDocument, Chunk

class BaseChunker(ABC):
    """分块器的抽象基类"""
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.chunk_size = kwargs.get('chunk_size', 1000)
        self.chunk_overlap = kwargs.get('chunk_overlap', 200)

    @abstractmethod
    def chunk_document(self, document: RAGDocument) -> RAGDocument:
        """分块文档并返回更新后的文档"""
        pass

    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """生成唯一的块ID"""
        chunk_hash = hashlib.md5(f"{document_id}_{chunk_index}_{datetime.now().isoformat()}".encode()).hexdigest()
        return f"chunk_{chunk_hash[:12]}"

class LangChainChunker(BaseChunker):
    def __init__(self,** kwargs):
        super().__init__(**kwargs)
        self.chunking_strategy = kwargs.get('chunking_strategy', 'recursive_character')
        self.text_splitter = self._create_text_splitter()

    def _create_text_splitter(self):
        """根据分块策略创建对应的LangChain文本分割器"""
        if self.chunking_strategy == 'recursive_character':
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.kwargs.get('separators', ['\n\n', '\n', '. ', '! ', '? ', ' ', '']),
                length_function=self.kwargs.get('length_function', len)
            )
        elif self.chunking_strategy == 'markdown':
            return MarkdownTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        else:
            raise ValueError(f"Unsupported chunking strategy: {self.chunking_strategy}")

    def chunk_documents(self, documents: List[LangChainDocument]) -> List[LangChainDocument]:
        """使用LangChain文本分割器分块文档"""
        return self.text_splitter.split_documents(documents)

    def chunk_document(self, rag_document: RAGDocument) -> RAGDocument:
        """分块RAGDocument对象并返回更新后的文档"""
        # 将RAGDocument转换为LangChain文档列表
        langchain_docs = [LangChainDocument(
            page_content=rag_document.page_content,
            metadata=rag_document.metadata
        )]

        # 分块文档
        split_docs = self.chunk_documents(langchain_docs)
        chunk_method = f"langchain_{self.chunking_strategy}_size_{self.chunk_size}_overlap_{self.chunk_overlap}"

        # 创建新的块列表
        new_chunks = []
        for i, split_doc in enumerate(split_docs):
            chunk_metadata = {
                **rag_document.metadata,
                'chunk_index': i,
                'chunk_method': chunk_method,
                'original_document_id': rag_document.document_id,
                'chunk_size': len(split_doc.page_content),
                'chunk_overlap': self.chunk_overlap,
                'langchain_splitter': self.text_splitter.__class__.__name__
            }

            # 添加分块器参数
            chunk_metadata['chunking_params'] = {
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'strategy': self.chunking_strategy
            }

            new_chunks.append(Chunk(
                page_content=split_doc.page_content,
                chunk_id=self._generate_chunk_id(rag_document.document_id, i),
                chunk_size=len(split_doc.page_content),
                chunk_overlap=self.chunk_overlap,
                chunk_method=chunk_method,
                metadata=chunk_metadata,
                file_path=rag_document.file_path
            ))

        # 更新RAGDocument
        return RAGDocument(
            page_content=rag_document.page_content,
            document_id=rag_document.document_id,
            file_name=rag_document.file_name,
            file_type=rag_document.file_type,
            file_path=rag_document.file_path,
            chunks=new_chunks,
            total_chunks=len(new_chunks),
            total_size=sum(len(chunk.page_content) for chunk in new_chunks),
            loader_used=rag_document.loader_used,
            loader_params=rag_document.loader_params,
            metadata={**rag_document.metadata, 'chunking_strategy': self.chunking_strategy}
        )

    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """生成唯一的块ID"""
        chunk_hash = hashlib.md5(f"{document_id}_{chunk_index}_{datetime.now().isoformat()}".encode()).hexdigest()
        return f"chunk_{chunk_hash[:12]}"

    def _split_by_characters(self, content: str) -> List[str]:
        """按字符数拆分文本"""
        chunks = []
        start = 0
        content_length = len(content)

        while start < content_length:
            end = start + self.chunk_size
            # 如果不是最后一块，尝试找到合适的分隔符
            if end < content_length:
                # 从分隔符列表中查找最合适的拆分位置
                for separator in self.separators:
                    pos = content.rfind(separator, start, end + 1)
                    if pos != -1:
                        end = pos + len(separator)
                        break

            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - self.chunk_overlap

        return chunks

    def _split_by_tokens(self, content: str) -> List[str]:
        """按token数拆分文本（简单空格分割模拟）"""
        # 实际应用中应使用tiktoken或其他tokenizer
        tokens = content.split()
        chunks = []
        start = 0

        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            chunk = ' '.join(chunk_tokens)
            chunks.append(chunk)
            start = end - self.chunk_overlap

        return chunks

class ParagraphChunker(BaseChunker):
    """按段落拆分文本的分块器"""
    def __init__(self,** kwargs):
        super().__init__(**kwargs)
        self.paragraph_separators = kwargs.get('paragraph_separators', ['\n\n', '\r\n\r\n', '\n\r\n'])

    def chunk_document(self, document: RAGDocument) -> RAGDocument:
        content = "\n\n".join([chunk.page_content for chunk in document.chunks])
        chunks = self._split_into_paragraphs(content)
        chunk_method = "paragraph_based"

        new_chunks = []
        for i, chunk_content in enumerate(chunks):
            # 过滤掉过短的段落
            if len(chunk_content) < self.kwargs.get('min_paragraph_length', 10):
                continue

            chunk_metadata = {
                **document.metadata,
                'chunk_index': i,
                'chunk_method': chunk_method,
                'original_document_id': document.document_id,
                'chunk_size': len(chunk_content)
            }

            new_chunks.append(Chunk(
                chunk_id=self._generate_chunk_id(document.document_id, i),
                page_content=chunk_content,
                metadata=chunk_metadata,
                chunk_size=len(chunk_content),
                chunk_overlap=0,
                chunk_method=chunk_method
            ))

        return RAGDocument(
            page_content=document.page_content,
            document_id=document.document_id,
            file_name=document.file_name,
            file_type=document.file_type,
            file_path=document.file_path,
            chunks=new_chunks,
            metadata={**document.metadata, 'chunking_params': self.kwargs},
            total_chunks=len(new_chunks),
            total_size=sum(len(chunk.page_content) for chunk in new_chunks),
            loader_used=document.loader_used,
            loader_params=document.loader_params
        )

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """将文本拆分为段落"""
        # 首先使用最常见的段落分隔符拆分
        paragraphs = [content]
        for separator in self.paragraph_separators:
            new_paragraphs = []
            for para in paragraphs:
                new_paragraphs.extend(para.split(separator))
            paragraphs = new_paragraphs

        # 过滤空段落
        return [para.strip() for para in paragraphs if para.strip()]

class ChunkerFactory:
    @staticmethod
    def get_chunker(chunking_strategy: str,** kwargs) -> BaseChunker:
        """根据分块策略返回相应的分块器实例"""
        if chunking_strategy == 'fixed_size':
            return LangChainChunker(**kwargs)
        elif chunking_strategy == 'paragraph':
            return ParagraphChunker(**kwargs)
        else:
            raise ValueError(f"Unsupported chunking strategy: {chunking_strategy}")

# 主函数用于直接调用
def chunk_document(document: RAGDocument, chunking_strategy: str,** kwargs) -> RAGDocument:
    chunker = ChunkerFactory.get_chunker(chunking_strategy, **kwargs)
    return chunker.chunk_document(document)