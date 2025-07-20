$(document).ready(function() {
    // 获取DOM元素
    const uploadForm = $('#upload-form');
    const fileInput = $('#file-input');
    const uploadSection = $('.upload-section');
    const processingSection = $('.processing-section');
    const resultsSection = $('.results-section');
    const progressBar = $('#progress-bar');
    const processingLog = $('#processing-log');
    const resultsSummary = $('#results-summary');
    const resultsFiles = $('#results-files');
    const resultsContent = $('#results-content');

    // 表单提交事件
    uploadForm.on('submit', function(e) {
        e.preventDefault();

        // 检查是否选择了文件
        if (!fileInput.val()) {
            alert('请选择一个文件');
            return;
        }

        // 显示处理中部分
        uploadSection.addClass('hidden');
        processingSection.removeClass('hidden');
        resultsSection.addClass('hidden');

        // 重置进度条和日志
        progressBar.width('0%');
        processingLog.empty();
        resultsSummary.empty();
        resultsFiles.empty();
        resultsContent.empty();

        // 创建FormData对象
        const formData = new FormData(this);

        // 模拟进度更新
        let progress = 0;
        const progressInterval = setInterval(function() {
            progress += Math.random() * 10;
            if (progress > 90) progress = 90;
            progressBar.width(progress + '%');
        }, 500);

        // 发送文件上传请求
        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                clearInterval(progressInterval);
                progressBar.width('100%');

                if (response.success) {
                    addLog('文件处理成功！');
                    setTimeout(function() {
                        processingSection.addClass('hidden');
                        resultsSection.removeClass('hidden');
                        displayResults(response);
                    }, 1000);
                } else {
                    addLog('处理失败: ' + response.message);
                    addLog('错误详情: ' + response.stderr);
                    setTimeout(function() {
                        processingSection.addClass('hidden');
                        uploadSection.removeClass('hidden');
                    }, 2000);
                }
            },
            error: function(xhr, status, error) {
                clearInterval(progressInterval);
                addLog('请求失败: ' + error);
                setTimeout(function() {
                    processingSection.addClass('hidden');
                    uploadSection.removeClass('hidden');
                }, 2000);
            }
        });
    });

    // 添加日志函数
    function addLog(message) {
        const timestamp = new Date().toLocaleTimeString();
        processingLog.append(`[${timestamp}] ${message}\n`);
        processingLog.scrollTop(processingLog[0].scrollHeight);
    }

    // 显示结果函数
    function displayResults(response) {
        // 显示摘要
        resultsSummary.html(`
            <p><strong>状态:</strong> 处理成功</p>
            <p><strong>输出目录:</strong> ${response.output_dir}</p>
            <p><strong>生成文件数:</strong> ${response.json_files.length}</p>
        `);

        // 显示文件列表
        response.json_files.forEach(function(file, index) {
            const fileName = file.split('/').pop();
            resultsFiles.append(`
                <div class="result-file">
                    <h3>文件 ${index + 1}: ${fileName}</h3>
                    <button class="btn-secondary view-json" data-file="${file}">
                        <i class="fas fa-eye"></i> 查看内容
                    </button>
                </div>
            `);
        });

        // 绑定查看JSON按钮事件
        $('.view-json').on('click', function() {
            const file = $(this).data('file');
            viewJsonFile(file);
        });
    }

    // 查看JSON文件函数
    function viewJsonFile(filePath) {
        $.ajax({
            url: '/json/' + filePath,
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    // 格式化JSON
                    const formattedJson = JSON.stringify(response.data, null, 2);
                    resultsContent.html(`
                        <h3>文件内容: ${filePath.split('/').pop()}</h3>
                        <pre><code>${formattedJson}</code></pre>
                    `);
                } else {
                    resultsContent.html(`<p class="error">无法加载文件: ${response.message}</p>`);
                }
            },
            error: function(xhr, status, error) {
                resultsContent.html(`<p class="error">请求失败: ${error}</p>`);
            }
        });
    }
});