from flask import Flask, request, render_template, jsonify, send_from_directory
import os
import subprocess
import time
import json
from datetime import datetime

app = Flask(__name__, static_folder='frontend/static', template_folder='frontend/templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'md', 'docx', 'xlsx'}

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 检查文件扩展名是否允许
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# 运行处理命令
def run_process(file_path, chunk_type='paragraph', chunk_size=1000, overlap=100):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], f'web_process_{timestamp}')
    os.makedirs(output_dir, exist_ok=True)

    # 构建命令
    cmd = [
        'python', 'main.py', 'process',
        file_path,
        '--output_dir', output_dir,
        '--chunk_type', chunk_type,
        '--chunk_size', str(chunk_size),
        '--overlap', str(overlap)
    ]

    try:
        # 运行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        # 查找生成的JSON文件
        json_files = []
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))

        return {
            'success': True,
            'message': '文件处理成功',
            'output_dir': output_dir,
            'json_files': json_files,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'message': f'处理失败: {str(e)}',
            'stdout': e.stdout,
            'stderr': e.stderr
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'发生错误: {str(e)}',
            'stdout': '',
            'stderr': str(e)
        }

# 加载JSON文件内容
def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        return {'error': str(e)}

# 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # 检查是否有文件部分
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件部分'})

    file = request.files['file']

    # 如果用户没有选择文件
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})

    # 如果文件允许
    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # 获取处理选项
        chunk_type = request.form.get('chunk_type', 'paragraph')
        chunk_size = int(request.form.get('chunk_size', 1000))
        overlap = int(request.form.get('overlap', 100))

        # 运行处理
        result = run_process(file_path, chunk_type, chunk_size, overlap)
        return jsonify(result)

    return jsonify({'success': False, 'message': '不允许的文件类型'})

@app.route('/results/<path:output_dir>')
def get_results(output_dir):
    full_path = os.path.join(app.config['OUTPUT_FOLDER'], output_dir)
    if not os.path.exists(full_path):
        return jsonify({'success': False, 'message': '结果目录不存在'})

    # 查找JSON文件
    json_files = []
    for root, dirs, files in os.walk(full_path):
        for file in files:
            if file.endswith('.json'):
                relative_path = os.path.relpath(os.path.join(root, file), app.config['OUTPUT_FOLDER'])
                json_files.append(relative_path)

    return jsonify({'success': True, 'json_files': json_files})

@app.route('/json/<path:file_path>')
def get_json(file_path):
    full_path = os.path.join(app.config['OUTPUT_FOLDER'], file_path)
    if not os.path.exists(full_path):
        return jsonify({'success': False, 'message': 'JSON文件不存在'})

    data = load_json_file(full_path)
    return jsonify({'success': True, 'data': data})

@app.route('/output/<path:file_path>')
def serve_output(file_path):
    return send_from_directory(app.config['OUTPUT_FOLDER'], file_path)

if __name__ == '__main__':
    print('启动Web服务器，访问 http://localhost:5000')
    app.run(debug=True)