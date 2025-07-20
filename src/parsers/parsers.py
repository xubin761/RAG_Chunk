from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import hashlib
from langchain_core.documents import Document as LangChainDocument
from langchain_community.document_loaders import UnstructuredPDFLoader, UnstructuredMarkdownLoader
# 尝试从不同的模块导入TableTransformer
try:
    from langchain_community.document_transformers import TableTransformer
except ImportError:
    try:
        from langchain_experimental.document_transformers import TableTransformer
    except ImportError:
        # 如果都无法导入，设置为None并在代码中处理
        TableTransformer = None
from langchain_community.document_transformers import Html2TextTransformer
from src.utils.models import Document as RAGDocument, Chunk
import pytesseract
from PIL import Image
from io import BytesIO

class LangChainDocumentParser:
    def __init__(self, file_path: str, **kwargs):
        self.file_path = Path(file_path)
        self.kwargs = kwargs
        self.file_type = self._detect_file_type()
        self.metadata = self._base_metadata()
        self.loader = self._create_loader()
        self.transformers = self._create_transformers()

    def _detect_file_type(self) -> str:
        suffix = self.file_path.suffix.lower()
        return suffix[1:] if suffix else 'unknown'

    def _base_metadata(self) -> Dict[str, Any]:
        return {
            'file_name': self.file_path.name,
            'file_path': str(self.file_path.absolute()),
            'file_size': self.file_path.stat().st_size if self.file_path.exists() else 0,
            'file_type': self.file_type,
            'parsed_at': datetime.now().isoformat(),
            'parser_params': self.kwargs
        }

    def _create_loader(self):
        """创建LangChain加载器"""
        file_ext = self.file_path.suffix.lower()

        if file_ext == '.pdf':
            return UnstructuredPDFLoader(
                file_path=str(self.file_path),
                strategy=self.kwargs.get('strategy', 'hi_res'),
                extract_images_in_pdf=self.kwargs.get('extract_images', True)
            )
        elif file_ext == '.md':
            return UnstructuredMarkdownLoader(str(self.file_path))
        else:
            raise ValueError(f"Unsupported file type for parsing: {file_ext}")

    def _create_transformers(self) -> List:
        """创建文档转换器列表"""
        transformers = []

        # 添加表格转换器
        if self.kwargs.get('extract_tables', True) and TableTransformer is not None:
            transformers.append(TableTransformer(
                table_finder=self.kwargs.get('table_finder', None),
                table_parser=self.kwargs.get('table_parser', None)
            ))
        elif self.kwargs.get('extract_tables', True) and TableTransformer is None:
            print("警告: 无法导入TableTransformer，表格提取功能将被跳过。")

        # 添加HTML到文本转换器（如果需要）
        if self.file_type in ['html', 'htm']:
            transformers.append(Html2TextTransformer())

        return transformers

    def parse(self) -> RAGDocument:
        """使用LangChain解析文档并转换为RAGDocument格式"""
        # 加载文档
        langchain_docs = self.loader.load()
        if not langchain_docs:
            raise ValueError("未能加载任何文档内容")

        # 应用转换器
        transformed_docs = langchain_docs
        for transformer in self.transformers:
            transformed_docs = transformer.transform_documents(transformed_docs)

        # 处理图像（如果有）
        processed_docs = self._process_images(transformed_docs)

        # 合并所有文档内容
        full_content = "\n\n".join([doc.page_content for doc in processed_docs])
        parser_name = f"LangChain{self.loader.__class__.__name__}"

        # 收集元数据
        combined_metadata = {**self.metadata, **{
            'total_pages': len(processed_docs),
            'parser_used': parser_name,
            'extracted_tables': self._count_tables(processed_docs),
            'extracted_images': self._count_images(processed_docs)
        }}

        # 创建初始块
        initial_chunk = Chunk(
            chunk_id=self._generate_chunk_id(),
            page_content=full_content,
            metadata=combined_metadata,
            chunk_size=len(full_content),
            chunk_overlap=0,
            chunk_method='initial_parser'
        )

        # 创建RAGDocument对象
        return RAGDocument(
            document_id=self._generate_document_id(),
            file_name=self.file_path.name,
            file_type=self.file_type,
            file_path=str(self.file_path),
            chunks=[initial_chunk],
            metadata=combined_metadata,
            total_chunks=1,
            total_size=len(full_content),
            loader_used=parser_name,
            loader_params=self.kwargs,
            page_content=full_content
        )

    def _process_images(self, docs: List[LangChainDocument]) -> List[LangChainDocument]:
        """处理文档中的图像并提取文本"""
        if not self.kwargs.get('process_images', True):
            return docs

        processed_docs = []
        for doc in docs:
            # 检查文档中是否有图像数据
            if 'images' in doc.metadata and doc.metadata['images']:
                image_texts = []
                for img_idx, img_data in enumerate(doc.metadata['images']):
                    try:
                        # 尝试从图像数据中提取文本
                        img = Image.open(BytesIO(img_data))
                        custom_config = self.kwargs.get('tesseract_config', r'--oem 3 --psm 6')
                        img_text = pytesseract.image_to_string(img, config=custom_config)
                        image_texts.append(f"[IMAGE {img_idx+1} TEXT]:\n{img_text}\n")
                    except Exception as e:
                        image_texts.append(f"[IMAGE {img_idx+1} ERROR]: {str(e)}\n")

                # 将图像文本添加到文档内容
                if image_texts:
                    doc.page_content = doc.page_content + "\n\n" + "\n".join(image_texts)

            processed_docs.append(doc)

        return processed_docs

    def _count_tables(self, docs: List[LangChainDocument]) -> int:
        """计算提取的表格数量"""
        count = 0
        for doc in docs:
            if 'tables' in doc.metadata:
                count += len(doc.metadata['tables'])
        return count

    def _count_images(self, docs: List[LangChainDocument]) -> int:
        """计算提取的图像数量"""
        count = 0
        for doc in docs:
            if 'images' in doc.metadata:
                count += len(doc.metadata['images'])
        return count

    def _generate_document_id(self) -> str:
        file_hash = hashlib.md5(str(self.file_path.absolute()).encode()).hexdigest()
        return f"parsed_doc_{file_hash}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _generate_chunk_id(self) -> str:
        return f"chunk_{self._generate_document_id()}_0"

    def _convert_table_to_markdown(self, table: Optional[List[List[str]]]) -> str:
        """将表格数据转换为Markdown格式"""
        if not table or not isinstance(table, list) or len(table) == 0 or not table[0]:
            return ""

        try:
            # 计算每列最大宽度
            col_widths = [max(len(str(cell)) for cell in col) for col in zip(*table)]

            # 创建表头
            markdown_table = []
            header = table[0]
            markdown_table.append("| " + " | ".join(f"{str(cell).ljust(col_widths[i])}" for i, cell in enumerate(header)) + " |")
            # 创建分隔线
            markdown_table.append("| " + " | ".join(["-" * col_width for col_width in col_widths]) + " |")
            # 添加表格内容
            for row in table[1:]:
                markdown_table.append("| " + " | ".join(f"{str(cell).ljust(col_widths[i])}" for i, cell in enumerate(row)) + " |")

            return "\n".join(markdown_table)
        except Exception as e:
            print(f"转换表格为Markdown时出错: {e}")
            return f"[表格转换错误: {str(e)}]"

class ParserFactory:
    @staticmethod
    def get_parser(file_path: str, **kwargs) -> LangChainDocumentParser:
        """根据文件扩展名返回相应的LangChain解析器实例"""
        return LangChainDocumentParser(file_path,** kwargs)

# 主函数用于直接调用
def parse_file(file_path: str, **kwargs) -> RAGDocument:
    parser = ParserFactory.get_parser(file_path,** kwargs)
    return parser.parse()