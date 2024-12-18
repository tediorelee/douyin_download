# 使用官方 Python 运行时作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制必要的文件到工作目录
COPY requirements.txt /app/requirements.txt
COPY app.py /app/app.py

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量（directory 由运行时的挂载路径决定）
ENV DOUYIN_API="http://localhost:16252"

# 暴露应用运行的端口
EXPOSE 7818

# 启动应用
CMD ["python", "app.py"]