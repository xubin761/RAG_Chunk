import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.utils.models import Document

class JSONFileHandler:
    @staticmethod
    def save_document(document: Document, output_dir: str = 'output', prefix: str = 'document', indent: int = 2) -> str:
        """
        将Document对象保存为JSON文件
        :param document: 要保存的Document对象
        :param output_dir: 输出目录
        :param prefix: 文件名前缀
        :param indent: JSON缩进空格数
        :return: 保存的文件路径
        """
        # 创建输出目录（如果不存在）
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{prefix}_{document.document_id[:8]}_{timestamp}.json"
        file_path = output_path / file_name

        # 转换Document对象为字典
        doc_dict = document.to_json()

        # 自定义JSON编码器，处理datetime对象
        def datetime_encoder(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

        # 保存为JSON文件
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            json.dump(doc_dict, f, ensure_ascii=False, indent=indent, default=datetime_encoder)

        return str(file_path)

    @staticmethod
    def load_document(file_path: str) -> Document:
        """
        从JSON文件加载Document对象
        :param file_path: JSON文件路径
        :return: 加载的Document对象
        """
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            doc_dict = json.load(f)

        # 转换字典为Document对象
        return Document(**doc_dict)

    @staticmethod
    def save_multiple_documents(documents: List[Document], output_dir: str = 'output', prefix: str = 'batch', indent: int = 2) -> str:
        """
        保存多个Document对象到单个JSON文件
        :param documents: Document对象列表
        :param output_dir: 输出目录
        :param prefix: 文件名前缀
        :param indent: JSON缩进空格数
        :return: 保存的文件路径
        """
        # 创建输出目录（如果不存在）
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{prefix}_{len(documents)}_docs_{timestamp}.json"
        file_path = output_path / file_name

        # 转换Document对象列表为字典列表
        docs_dict = [doc.to_json() for doc in documents]

        # 保存为JSON文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(docs_dict, f, ensure_ascii=False, indent=indent)

        return str(file_path)

    @staticmethod
    def get_document_metadata(file_path: str) -> Dict[str, Any]:
        """
        获取JSON文档的元数据，而不加载整个文档
        :param file_path: JSON文件路径
        :return: 文档元数据
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            doc_dict = json.load(f)

        # 提取元数据字段
        metadata_fields = ['document_id', 'file_name', 'file_type', 'total_chunks', 'total_size', 'created_at', 'loader_used']
        return {field: doc_dict.get(field) for field in metadata_fields}

    @staticmethod
    def merge_documents(documents: List[Document], new_document_id: Optional[str] = None) -> Document:
        """
        合并多个Document对象为一个
        :param documents: 要合并的Document对象列表
        :param new_document_id: 新文档ID，如果为None则自动生成
        :return: 合并后的Document对象
        """
        if not documents:
            raise ValueError("至少需要一个文档进行合并")

        # 合并所有块
        all_chunks = []
        for doc in documents:
            all_chunks.extend(doc.chunks)

        # 使用第一个文档的元数据作为基础
        base_doc = documents[0]
        merged_metadata = {
            **base_doc.metadata,
            'merged_from': [doc.document_id for doc in documents],
            'merged_at': datetime.now().isoformat(),
            'total_original_documents': len(documents)
        }

        # 创建合并后的文档
        return Document(
            document_id=new_document_id or f"merged_{'_'.join([doc.document_id[:4] for doc in documents])}",
            file_name=f"merged_{base_doc.file_name}",
            file_type=base_doc.file_type,
            file_path=str(Path(base_doc.file_path).parent),
            chunks=all_chunks,
            metadata=merged_metadata,
            total_chunks=len(all_chunks),
            total_size=sum(len(chunk.content) for chunk in all_chunks),
            loader_used=base_doc.loader_used,
            loader_params=base_doc.loader_params
        )