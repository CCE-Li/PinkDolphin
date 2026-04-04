# Pink Dolphin

Pink Dolphin 是一个面向个人邮箱场景的钓鱼邮件识别与处置系统，当前项目包含：

- `backend`：FastAPI 后端、分析引擎、IMAP 增量同步、数据库与异步任务
- `frontend`：Vue 3 管理台
- `docker-compose.yml`：本地或单机服务器部署入口

项目目标不是做纯规则演示，而是围绕“真实邮箱接入 + 多层分析 + 人工处置 + 配置可视化”提供一套可落地的单机部署方案。

## 项目特点

- 支持 IMAP 邮箱接入，按“每个邮箱 + 文件夹”维护独立 UID 增量同步进度
- 支持邮件上传、原始邮件分析、监听邮箱实时同步、手动立即同步
- 六层分析器可组合运行：`header_auth`、`content_rule`、`url`、`attachment`、`behavior`、`llm`
- 支持 URL 与附件的真实外部能力接入，同时保留 mock 模式便于本地开发
- 支持问题日志、审计日志、规则管理、隐私白名单、配置管理
- 隐私白名单支持按条目配置 `url / attachment / llm` 三个扫描开关
- 管理员账号密码可在前端直接修改
- 前后端都可单机部署，适合 Docker 场景

## 技术栈

- Backend: Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic, Celery, Redis, PostgreSQL
- Frontend: Vue 3, TypeScript, Pinia, Vite, Tailwind CSS
- Deploy: Docker Compose, Nginx

## 目录结构

```text
PinkDolphin/
├─ backend/
│  ├─ app/
│  ├─ alembic/
│  ├─ scripts/
│  ├─ .env.example
│  └─ Dockerfile
├─ frontend/
│  ├─ src/
│  ├─ public/
│  ├─ .env.example
│  └─ Dockerfile
├─ docker-compose.yml
└─ README.md
```

## 核心能力

### 邮件接入

- 上传 `.eml` 文件分析
- 提交原始邮件或结构化 JSON 分析
- 绑定 IMAP 邮箱并长期监听
- 手动触发一次立即同步
- 本地目录轮询导入 `.eml`

### 分析能力

- `header_auth`：解析 `SPF / DKIM / DMARC`
- `content_rule`：关键词与自定义规则引擎
- `url`：URL 提取与威胁情报分析
- `attachment`：附件元数据、哈希、外部扫描结果
- `behavior`：联系人历史与行为信号
- `llm`：模型语义分析

### 管理能力

- 邮件列表、详情、重分析、处置
- 事件列表与风险摘要
- 规则管理
- 审计日志
- 问题日志
- 隐私白名单
- 配置管理
- 管理员账号密码修改

## 当前分析链说明

项目目前支持六层分析器，但在真实部署中建议按实际能力启用：

- 高价值：`header_auth`、`content_rule`
- 有真实外部能力时建议启用：`url`、`attachment`、`llm`
- 可按需启用：`behavior`

对应动态配置项：

- `ENABLED_ANALYZERS`
- `ANALYZER_WEIGHTS`

## 本地开发

### 1. 准备依赖

- Python 3.11
- Node.js 20+
- PostgreSQL
- Redis
- `uv`

### 2. 启动后端

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动 Celery Worker

```bash
cd backend
uv run celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```

### 4. 启动前端

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

本地开发默认访问：

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`

## 单机 Docker 部署

适用场景：

- 前后端在同一台服务器
- 使用 Docker 部署 PostgreSQL、Redis、Backend、Worker
- 前端使用静态构建结果，由 Nginx 托管

### 1. 上传项目

```bash
scp -r PinkDolphin user@your-server:/opt/
ssh user@your-server
cd /opt/PinkDolphin
```

### 2. 准备后端配置

```bash
cp backend/.env.example backend/.env
```

建议至少配置这些项：

```env
APP_ENV=docker
ADMIN_BEARER_TOKEN=change-me

DATABASE_URL=postgresql+psycopg://phishing:phishing@postgres:5432/phishing_mail
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

CORS_ALLOW_ORIGINS=http://localhost,http://127.0.0.1,http://localhost:80,http://127.0.0.1:80

URL_SCAN_PROVIDER=mock
ATTACHMENT_SCAN_PROVIDER=mock
LLM_PROVIDER_MODE=mock
LLM_ANALYZER_ENABLED=false
```

如果前后端同机部署，前端建议直接走同源 `/api`，不需要写死服务器 IP。

### 3. 修改 `docker-compose.yml`

将：

```yaml
env_file:
  - ./backend/.env.example
```

改成：

```yaml
env_file:
  - ./backend/.env
```

### 4. 启动基础服务

```bash
docker compose up -d postgres redis
```

### 5. 导入现有数据

如果你已经有本地数据，先从本地导出数据库，再导入服务器容器。

本地导出示例：

```bash
pg_dump -h <db_host> -p 5432 -U <db_user> -d <db_name> -Fc -f pinkdolphin.dump
```

复制到服务器后导入：

```bash
docker cp pinkdolphin.dump phishing_postgres:/tmp/pinkdolphin.dump
docker exec -it phishing_postgres pg_restore -U phishing -d phishing_mail --clean --if-exists /tmp/pinkdolphin.dump
```

### 6. Alembic 基线处理

当前项目已经将历史迁移合并为一个 baseline：

- Revision: `20260404_0010`

如果你恢复的是一个已经存在数据的旧库，执行：

```bash
docker compose run --rm backend alembic stamp 20260404_0010
```

如果你部署的是空库，执行：

```bash
docker compose run --rm backend alembic upgrade head
```

### 7. 启动后端与 Worker

```bash
docker compose up -d backend worker
```

查看日志：

```bash
docker compose logs -f backend
docker compose logs -f worker
```

默认后端地址：

- `http://<server-ip>:8000`

## 前端生产部署

当前前端最适合静态构建后交给 Nginx 托管。

### 1. 配置前端

```bash
cd frontend
cp .env.example .env
```

推荐使用：

```env
VITE_API_BASE_URL=/api
```

### 2. 构建前端

```bash
npm install
npm run build
```

构建产物位于：

- `frontend/dist`

### 3. Nginx 反向代理示例

```nginx
server {
    listen 80;
    server_name _;

    root /opt/PinkDolphin/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }
}
```

这样前端和后端在同域名下工作：

- 前端页面：`http://<server-ip>/`
- 后端接口：`http://<server-ip>/api`

## 邮箱监听与同步机制

### 当前实现

- 每个监听邮箱维护独立同步状态
- 同步维度细化到“邮箱账号 + 文件夹”
- 手动“立即同步”会尽量同步处理当前新邮件
- 邮件去重按 `mailbox_account_id + remote_folder + remote_uid`

### 为什么这么做

不同邮箱平台、不同账号、不同文件夹的 UID 都不能共用一个全局游标。  
如果共用同步进度，会导致漏拉、重复拉或跨文件夹串数据。

## 常见问题

### 1. 修改 `.env` 后要不要重启？

分情况：

- 配置管理页支持的动态项：后续新的后端请求会使用新值
- `DATABASE_URL / REDIS_URL / CELERY_*` 这类部署配置：仍然需要重启相关服务
- Celery Worker 是独立进程，后端清理配置缓存并不会自动让 Worker 热更新

### 2. 停机期间收到的邮件还能补同步吗？

一般可以，只要：

- 邮件仍在当前监听的文件夹里
- UID 游标没有异常
- IMAP 账号可正常连接

如果邮件被移动、删除，或 Worker 未运行，就可能出现“已发现但未同步完成”的现象。

## 安全建议

- 上线前必须修改数据库默认密码
- `ADMIN_BEARER_TOKEN` 不要使用默认值
- 如果使用真实 LLM、URL、附件扫描能力，相关 API Key 只放在服务器 `.env`
- 生产环境不要把 `postgres` 和 `redis` 直接暴露到公网
- 建议为 PostgreSQL 数据目录挂载持久化卷

## 当前迁移说明

当前 Alembic 已压缩为单一 baseline：

- [20260404_0010_baseline.py](C:/Users/wkx32/Desktop/JSG/PinkDolphin/backend/alembic/versions/20260404_0010_baseline.py)

对现有数据库：

```bash
alembic stamp 20260404_0010
```

对空数据库：

```bash
alembic upgrade head
```

