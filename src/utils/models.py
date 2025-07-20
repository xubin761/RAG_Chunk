from typing import List, Dict, Optional, Any
from datetime import datetime
from langchain_core.documents import Document as LangChainDocument
from pydantic import BaseModel

class Chunk(BaseModel):
    page_content: str
    chunk_id: str
    chunk_size: int
    chunk_overlap: int
    chunk_method: str
    metadata: Dict[str, Any]
    created_at: datetime = datetime.now()

class Document(BaseModel):
    page_content: str
    document_id: str
    file_name: str
    file_type: str
    file_path: str
    chunks: List[Chunk]
    total_chunks: int
    total_size: int
    metadata: Dict[str, Any]
    created_at: datetime = datetime.now()
    loader_used: str
    loader_params: Dict[str, Any]

    def to_langchain_document(self) -> LangChainDocument:
        """转换为LangChain的Document对象"""
        return LangChainDocument(
            page_content=self.page_content,
            metadata={
                "document_id": self.document_id,
                "file_name": self.file_name,
                "file_type": self.file_type,
                "file_path": self.file_path,
                "total_chunks": self.total_chunks,
                "total_size": self.total_size,
                "created_at": self.created_at,
                "loader_used": self.loader_used,
                "loader_params": self.loader_params,
                **self.metadata
            }
        )

    @classmethod
    def from_langchain_document(
        cls, doc: LangChainDocument,
        document_id: str,
        file_name: str,
        file_type: str,
        file_path: str,
        chunks: List[Chunk],
        total_chunks: int,
        total_size: int,
        loader_used: str,
        loader_params: Dict[str, Any]
    ) -> 'Document':
        """从LangChain的Document对象创建自定义Document对象"""
        return cls(
            page_content=doc.page_content,
            document_id=document_id,
            file_name=file_name,
            file_type=file_type,
            file_path=file_path,
            chunks=chunks,
            total_chunks=total_chunks,
            total_size=total_size,
            metadata=doc.metadata,
            loader_used=loader_used,
            loader_params=loader_params
        )

    def to_json(self) -> Dict[str, Any]:
        result = self.dict()
        result["chunks"] = [chunk.dict() for chunk in self.chunks]
        return result