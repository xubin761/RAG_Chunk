# 增强型RAG框架

一个功能完善的检索增强生成(RAG)框架，专注于文档加载、分块和解析功能，支持多种文件格式和高级处理选项。

## 功能特点

### 1. 文件加载 (Load File)
- 支持多种文件格式: PDF、Markdown、Word文档、纯文本等
- 丰富的加载参数: 密码保护PDF、图像提取、编码设置等
- 详细的元数据收集: 文件大小、类型、路径、加载时间等

### 2. 文档分块 (Chunk File)
- 多种分块策略:
  - 固定大小分块: 按字符数或Token数控制块大小
  - 段落分块: 基于自然段落边界的智能分块
- 可配置的块大小和重叠度
- 保留完整的元数据追踪

### 3. 文档解析 (Parse File)
- 高级PDF解析: 提取文本、表格和图像
- Markdown处理: 解析格式、表格和图像引用
- 图像OCR: 将图像内容转换为可搜索文本
- 表格转换: 将提取的表格转换为Markdown格式

## 项目结构

```
RAG_Chunk/
├── src/
│   ├── loaders/        # 文件加载模块
│   ├── chunkers/       # 文档分块模块
│   ├── parsers/        # 文档解析模块
│   └── utils/          # 工具函数和数据模型
├── output/             # 处理结果输出目录
├── main.py             # 主程序入口
├── requirements.txt    # 项目依赖
└── README.md           # 项目说明文档
```

## 安装指南

### 前提条件
- Python 3.8+ 
- Tesseract OCR (用于图像文本提取)
  - Windows: 从 [UB Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) 下载安装
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/RAG_Chunk.git
cd RAG_Chunk
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
# Windows激活
venv\Scripts\activate
# macOS/Linux激活
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量 (可选)
创建 `.env` 文件并添加以下内容:
```
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows示例
# TESSERACT_PATH=/usr/bin/tesseract  # Linux示例
# TESSERACT_PATH=/usr/local/bin/tesseract  # macOS示例
```

## 使用示例

### 基本命令

#### 1. 加载文件
```bash
python main.py load path/to/your/file.pdf --output_dir output/loaded
```

#### 2. 分块处理
```bash
python main.py chunk output/loaded/document_xxx.json --strategy fixed_size --chunk_size 1000 --chunk_overlap 200
```

#### 3. 解析文件
```bash
python main.py parse path/to/your/file.pdf --extract_tables --extract_images
```

#### 4. 完整流程处理
```bash
python main.py process path/to/your/document.pdf --chunk_size 1500 --chunk_overlap 300
```

### 高级用法

#### 加载带密码的PDF
```bash
python main.py load encrypted.pdf --params password=yourpassword
```

#### 使用段落分块策略
```bash
python main.py chunk document.json --strategy paragraph --min_paragraph_length 50
```

#### 自定义Tesseract OCR配置
```bash
python main.py parse scanned_document.pdf --extract_images --tesseract_config "--oem 3 --psm 11"
```

## 输出格式

所有处理结果均保存为统一格式的JSON文件，包含以下主要字段:

```json
{
  "document_id": "doc_xxx",
  "file_name": "example.pdf",
  "file_type": "pdf",
  "file_path": "/path/to/example.pdf",
  "chunks": [
    {
      "chunk_id": "chunk_xxx",
      "content": "块内容文本...",
      "metadata": {
        "page_number": 1,
        "chunk_method": "fixed_size_characters_1000_overlap_200",
        "file_name": "example.pdf"
      },
      "chunk_size": 1000,
      "chunk_overlap": 200,
      "chunk_method": "fixed_size_characters_1000_overlap_200",
      "file_path": "/path/to/example.pdf"
    }
  ],
  "metadata": {
    "total_pages": 10,
    "file_size": 102400,
    "loaded_at": "2023-07-01T12:00:00"
  },
  "total_chunks": 25,
  "total_size": 25000,
  "loader_used": "PDFLoader",
  "loader_params": {}
}
```

## 自定义扩展

### 添加新的文件加载器
1. 在 `src/loaders/loaders.py` 中创建新的加载器类，继承 `BaseFileLoader`
2. 实现 `load()` 方法
3. 在 `FileLoaderFactory` 中注册新的加载器

### 添加新的分块策略
1. 在 `src/chunkers/chunkers.py` 中创建新的分块器类，继承 `BaseChunker`
2. 实现 `chunk_document()` 方法
3. 在 `ChunkerFactory` 中注册新的分块器

## 故障排除

- **Tesseract未找到**: 确保Tesseract已安装并在环境变量中，或在.env文件中指定TESSERACT_PATH
- **PDF解析错误**: 尝试使用`--password`参数(如果PDF加密)或更新PyPDF2版本
- **中文乱码**: 确保文件编码正确，可尝试添加`--params encoding=utf-8`参数

## 依赖项
详见 [requirements.txt](requirements.txt) 文件

## 许可证
[MIT License](LICENSE)