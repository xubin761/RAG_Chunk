import logging
import argparse
from pathlib import Path
from src.loaders.loaders import load_file
from src.chunkers.chunkers import chunk_document
from src.parsers.parsers import parse_file
from src.utils.file_utils import JSONFileHandler
from src.utils.models import Document

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='RAG框架文件处理工具')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # 加载文件命令
    load_parser = subparsers.add_parser('load', help='加载文件并保存为初始JSON格式')
    load_parser.add_argument('file_path', help='要加载的文件路径')
    load_parser.add_argument('--output_dir', default='output/loaded', help='输出目录')
    load_parser.add_argument('--params', nargs='*', help='加载参数，格式为key=value')

    # 分块文件命令
    chunk_parser = subparsers.add_parser('chunk', help='对已加载的文件进行分块处理')
    chunk_parser.add_argument('json_path', help='已加载文件的JSON路径')
    chunk_parser.add_argument('--strategy', default='fixed_size', help='分块策略: fixed_size 或 paragraph')
    chunk_parser.add_argument('--chunk_size', type=int, default=1000, help='块大小')
    chunk_parser.add_argument('--chunk_overlap', type=int, default=200, help='块重叠大小')
    chunk_parser.add_argument('--unit', default='characters', help='单位: characters 或 tokens')
    chunk_parser.add_argument('--output_dir', default='output/chunked', help='输出目录')

    # 解析文件命令
    parse_parser = subparsers.add_parser('parse', help='解析带格式的文件(如PDF/Markdown)并提取内容')
    parse_parser.add_argument('file_path', help='要解析的文件路径')
    parse_parser.add_argument('--output_dir', default='output/parsed', help='输出目录')
    parse_parser.add_argument('--extract_tables', action='store_true', help='提取表格')
    parse_parser.add_argument('--extract_images', action='store_true', help='提取图像并进行OCR')
    parse_parser.add_argument('--tesseract_config', default=r'--oem 3 --psm 6', help='Tesseract OCR配置')

    # 完整流程命令
    full_parser = subparsers.add_parser('process', help='执行完整流程: 解析->加载->分块')
    full_parser.add_argument('file_path', help='要处理的文件路径')
    full_parser.add_argument('--output_dir', default='output/full_process', help='输出目录')
    full_parser.add_argument('--chunk_strategy', default='fixed_size', help='分块策略')
    full_parser.add_argument('--chunk_size', type=int, default=1000, help='块大小')
    full_parser.add_argument('--chunk_overlap', type=int, default=200, help='块重叠大小')

    args = parser.parse_args()

    # 解析键值对参数
    def parse_params(param_list):
        params = {}
        if param_list:
            for param in param_list:
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        return params

    try:
        if args.command == 'load':
            logger.info(f"开始加载文件: {args.file_path}")
            params = parse_params(args.params)
            document = load_file(args.file_path, **params)
            output_path = JSONFileHandler.save_document(document, args.output_dir)
            logger.info(f"文件加载完成，已保存至: {output_path}")

        elif args.command == 'chunk':
            logger.info(f"开始分块处理: {args.json_path}")
            document = JSONFileHandler.load_document(args.json_path)
            chunked_doc = chunk_document(
                document,
                chunking_strategy=args.strategy,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                unit=args.unit
            )
            output_path = JSONFileHandler.save_document(chunked_doc, args.output_dir, prefix='chunked_doc')
            logger.info(f"分块处理完成，已保存至: {output_path}")
            logger.info(f"原始块数: {len(document.chunks)}, 新块数: {len(chunked_doc.chunks)}")

        elif args.command == 'parse':
            logger.info(f"开始解析文件: {args.file_path}")
            parsed_doc = parse_file(
                args.file_path,
                extract_tables=args.extract_tables,
                extract_images=args.extract_images,
                tesseract_config=args.tesseract_config
            )
            output_path = JSONFileHandler.save_document(parsed_doc, args.output_dir, prefix='parsed_doc')
            logger.info(f"文件解析完成，已保存至: {output_path}")
            logger.info(f"提取表格数量: {parsed_doc.metadata.get('extracted_tables', 0)}")
            logger.info(f"提取图像数量: {parsed_doc.metadata.get('extracted_images', 0)}")

        elif args.command == 'process':
            logger.info(f"开始完整流程处理: {args.file_path}")
            file_ext = Path(args.file_path).suffix.lower()

            # 1. 解析文件（如果是PDF或Markdown）
            if file_ext in ['.pdf', '.md', '.markdown']:
                logger.info("步骤1/3: 解析文件...")
                parsed_doc = parse_file(
                    args.file_path,
                    extract_tables=True,
                    extract_images=True
                )
                parsed_path = JSONFileHandler.save_document(parsed_doc, f"{args.output_dir}/step1_parsed")
                logger.info(f"解析结果保存至: {parsed_path}")
                current_doc = parsed_doc
            else:
                # 对于纯文本文件，直接加载
                logger.info("步骤1/3: 加载文件...")
                current_doc = load_file(args.file_path)
                loaded_path = JSONFileHandler.save_document(current_doc, f"{args.output_dir}/step1_loaded")
                logger.info(f"加载结果保存至: {loaded_path}")

            # 2. 分块处理
            logger.info("步骤2/3: 分块处理...")
            chunked_doc = chunk_document(
                current_doc,
                chunking_strategy=args.chunk_strategy,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap
            )
            chunked_path = JSONFileHandler.save_document(chunked_doc, f"{args.output_dir}/step2_chunked")
            logger.info(f"分块结果保存至: {chunked_path}")

            # 3. 最终输出
            final_path = JSONFileHandler.save_document(chunked_doc, args.output_dir, prefix='final')
            logger.info(f"完整流程完成！最终结果保存至: {final_path}")
            logger.info(f"文档ID: {chunked_doc.document_id}")
            logger.info(f"总块数: {len(chunked_doc.chunks)}")
            logger.info(f"总字符数: {chunked_doc.total_size}")

    except Exception as e:
        logger.error(f"处理过程中出错: {str(e)}", exc_info=True)

if __name__ == '__main__':
    main()