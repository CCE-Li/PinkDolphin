FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

ARG UV_INDEX_URL=https://mirrors.ustc.edu.cn/pypi/simple
ENV UV_INDEX_URL=${UV_INDEX_URL}
ENV PIP_INDEX_URL=${UV_INDEX_URL}

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev

COPY . /app

EXPOSE 8000