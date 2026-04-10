# Paper Assistant

一个面向 AI 顶会论文的工程化论文助手，覆盖 `ACL`、`NeurIPS`、`ICML`、`ICLR`，支持自动抓取、SQLite 缓存、中文总结、多页面前端，以及面向云平台的部署配置。

## 项目特性

- 搜索即自动获取，不需要先手动同步
- 支持 `ACL`、`NeurIPS`、`ICML`、`ICLR`
- 前后端分层目录，便于继续扩展
- 论文详情页支持摘要补全与中文总结
- 内置数据集状态页和后台定时刷新
- 已补齐 Docker、Render 和 GitHub Actions 配置

## 目录结构

```text
backend/
  app/
    core/            # 配置、HTTP 客户端、通用工具
    domain/          # 领域实体
    repositories/    # SQLite 仓库
    integrations/    # 顶会官方源接入
    services/        # 搜索、同步、总结业务编排
    jobs/            # 定时刷新任务
    presentation/    # 本地 HTTP 服务与生产 WSGI 入口
frontend/
  index.html
  paper.html
  datasets.html
  src/
  styles/
tests/
render.yaml
Dockerfile
```

## 本地启动

```bash
python3 -m pip install --user -r requirements.txt
python3 main.py
```

默认地址：

- `http://127.0.0.1:8765`

页面入口：

- `/`：论文检索页
- `/paper?id=<paper_id>`：论文详情页
- `/datasets`：数据状态页

## Docker 启动

构建镜像：

```bash
docker build -t paper-reading .
```

启动容器：

```bash
docker run --rm -p 8000:8000 -v "$(pwd)/data:/app/data" paper-reading
```

容器默认地址：

- `http://127.0.0.1:8000`

## 部署到公网

先说明一件事：

- GitHub 负责托管代码
- 真正让应用在公网可访问，通常要接 Render、Railway、Fly.io 或你自己的服务器

这个仓库已经准备好了两样东西：

1. `Dockerfile`
   通用容器部署入口，适合 Docker、Railway、Fly.io、自建服务器。

2. `render.yaml`
   可以直接让 Render 从 GitHub 仓库创建 Web Service，并挂载持久化磁盘保存 `SQLite` 数据。

### 推荐做法：GitHub + Render

1. 把代码推到你的 GitHub 仓库
2. 在 Render 里选择 `New +` -> `Blueprint`
3. 连接 GitHub 仓库 `YUGUUUU0920/PaperReading`
4. Render 会读取仓库里的 `render.yaml`
5. 在 Render 控制台补上 `OPENAI_API_KEY`
6. 部署完成后，访问 Render 分配的公网域名

线上部署时：

- 平台注入 `PORT` 时，服务会自动监听 `0.0.0.0`
- 数据库存放在 `/app/data`
- `render.yaml` 已配置 `/api/health` 健康检查

## GitHub Actions

仓库已包含：

- `.github/workflows/ci.yml`

每次推送或发起 PR 时会自动执行：

- 安装依赖
- 运行 `unittest`

## 手动刷新缓存

```bash
python3 scripts/sync_papers.py --conference icml --year 2024
python3 scripts/sync_papers.py --conference iclr --year 2025
```

这只是刷新缓存，不是使用前提。

## 环境变量

```bash
export PAPER_ASSISTANT_HOST=127.0.0.1
export PAPER_ASSISTANT_PORT=8765
export PAPER_ASSISTANT_DB_PATH="/absolute/path/to/papers.db"

# 网络模式：auto / env / direct
export PAPER_ASSISTANT_NETWORK_MODE=auto

# 默认打开页面后自动查询的会议年份
export PAPER_ASSISTANT_DEFAULT_CONFERENCE=icml
export PAPER_ASSISTANT_DEFAULT_YEAR=2024

# 数据集刷新 TTL 与后台调度
export PAPER_ASSISTANT_REFRESH_TTL_HOURS=168
export PAPER_ASSISTANT_SCHEDULER_ENABLED=1
export PAPER_ASSISTANT_SCHEDULER_INTERVAL_MINUTES=60

# 可选：OpenAI 兼容总结接口
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4.1"
```

## 官方数据源

- [ACL Anthology](https://aclanthology.org/)
- [NeurIPS Proceedings](https://proceedings.neurips.cc/)
- [ICLR Proceedings](https://proceedings.iclr.cc/)
- [PMLR / ICML](https://proceedings.mlr.press/)
