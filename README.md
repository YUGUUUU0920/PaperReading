# Paper Reading

一个面向 AI 顶会论文的公网级论文阅读平台，覆盖 `ACL`、`NeurIPS`、`ICML`、`ICLR`，支持中文导读、中文标签、引用与资源信号、论文推荐，以及可直接部署到云端的工程结构。

## 产品能力

- 覆盖 `ACL`、`NeurIPS`、`ICML`、`ICLR` 的官方论文源
- 支持 `2025` 年最新会议论文接入
- 提供中文导读、中文标签与研究方向提示
- 展示引用量、开放获取、代码资源等辅助信号
- 详情页支持相关论文推荐
- 多页面前端，适合公网直接访问
- 提供 Docker、Render、GitHub Actions 一体化部署能力

## AI Native 结构

项目采用面向模型协作的仓库组织方式：

- `AGENTS.md`
  仓库地图、边界说明与修改约束
- `docs/ARCHITECTURE.md`
  系统结构与扩展点
- `docs/AI_HARNESS.md`
  总结 contract、输出校验与 fallback 约束
- `docs/DATA_SOURCES.md`
  官方源与支持年份说明

## 目录结构

```text
backend/
  app/
    ai/              # Summary contract、harness 与输出校验
    core/            # 配置、HTTP 客户端、通用工具
    domain/          # 领域实体
    repositories/    # SQLite 仓库
    integrations/    # 顶会官方源接入
    services/        # 搜索、信号增强、标签、推荐、总结业务编排
    jobs/            # 定时刷新任务
    presentation/    # 本地 HTTP 服务与生产 WSGI 入口
docs/
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

- `/`：论文检索
- `/paper?id=<paper_id>`：论文导读
- `/datasets`：论文库总览

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

### 推荐做法：GitHub + Render

1. 把代码推到你的 GitHub 仓库
2. 在 Render 里选择 `New +` -> `Blueprint`
3. 连接 GitHub 仓库 `YUGUUUU0920/PaperReading`
4. Render 会读取仓库里的 `render.yaml`
5. 在 Render 控制台补上 `OPENAI_API_KEY`
6. 部署完成后，访问 Render 分配的公网域名

仓库已包含：

- `Dockerfile`
- `render.yaml`
- `.github/workflows/ci.yml`

## GitHub Actions

每次推送或发起 PR 时会自动执行：

- 安装依赖
- 运行 `unittest`

## 数据更新

```bash
python3 scripts/sync_papers.py --conference icml --year 2024
python3 scripts/sync_papers.py --conference iclr --year 2025
```

这个脚本适合预先整理某个会议年份的数据。

## 环境变量

```bash
export PAPER_ASSISTANT_HOST=127.0.0.1
export PAPER_ASSISTANT_PORT=8765
export PAPER_ASSISTANT_DB_PATH="/absolute/path/to/papers.db"

# 网络模式：auto / env / direct
export PAPER_ASSISTANT_NETWORK_MODE=auto

# 默认会议年份
export PAPER_ASSISTANT_DEFAULT_CONFERENCE=icml
export PAPER_ASSISTANT_DEFAULT_YEAR=2025

# 数据刷新 TTL 与后台调度
export PAPER_ASSISTANT_REFRESH_TTL_HOURS=168
export PAPER_ASSISTANT_SCHEDULER_ENABLED=1
export PAPER_ASSISTANT_SCHEDULER_INTERVAL_MINUTES=60

# 可选：OpenAI 兼容导读模型
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-5.4"
```

## 官方数据源

- [ACL Anthology](https://aclanthology.org/)
- [NeurIPS Virtual 2025](https://neurips.cc/virtual/2025/papers.html)
- [NeurIPS Proceedings](https://proceedings.neurips.cc/)
- [ICLR Proceedings](https://proceedings.iclr.cc/)
- [PMLR / ICML](https://proceedings.mlr.press/)

## 学术信号增强

项目会结合外部学术元数据补充：

- 引用量与影响力信号
- 开放获取状态
- 主题概念与中文标签
- 代码与资源链接
