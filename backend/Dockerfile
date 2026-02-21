FROM python:3.11-slim

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 复制依赖文件（pyproject.toml 和 uv.lock 现在就在 backend/ 内）
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --frozen --no-install-project

# 将 .venv 加入 PATH
ENV PATH="/app/.venv/bin:$PATH"

# 复制后端代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
