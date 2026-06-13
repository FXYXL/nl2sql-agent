# NL2SQL Agent

基于 AI 的自然语言转 SQL 查询工具，支持 API 和终端 CLI 两种访问方式。

## 功能特性

### 核心功能
- **自然语言查询** — 用中文/英文提问，自动生成 SQL 并执行
- **写入模式** — 支持 INSERT/UPDATE/DELETE 操作（需开启并确认）
- **多语言支持** — 中英文切换

### CLI 终端界面
- **三栏布局** — 消息区、输入框、侧栏
- **命令补全** — 输入 `/` 显示命令列表，支持过滤
- **SQL 自动补全** — 输入时提示表名、列名
- **Rich 表格** — 查询结果美观渲染
- **结果分页** — 大结果集分页显示

### 命令列表

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/clear` | 清空消息区（需确认） |
| `/history` | 查看聊天历史 |
| `/export` | 导出历史到文件 |
| `/export csv` | 导出上次结果到 CSV |
| `/config` | 查看当前配置 |
| `/schema` | 查看数据库结构 |
| `/write` | 切换写入模式 |
| `/db <url>` | 切换数据库连接 |
| `/copy` | 复制上次 SQL 到剪贴板 |
| `/ping` | 检测数据库健康状态 |
| `/explain` | 查看查询执行计划 |
| `/page N` | 查看结果第 N 页 |
| `/fav save [name]` | 保存查询到收藏 |
| `/fav list` | 列出收藏 |
| `/fav run N` | 执行收藏 N |
| `/fav del N` | 删除收藏 N |
| `/lang` | 切换语言 |
| `/quit` | 退出应用 |

### 快捷键

| 快捷键 | 说明 |
|--------|------|
| `Up/Down` | 翻看输入历史 |
| `Tab` | 接受自动补全建议 |
| `Ctrl+L` | 清空消息 |
| `Ctrl+H` | 切换侧栏 |
| `Ctrl+C` | 退出 |

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/FXYXL/nl2sql-agent.git
cd nl2sql-agent

# 安装依赖
uv sync
```

### 配置

编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=mysql+aiomysql://用户名:密码@主机:端口/数据库名

# LLM 配置（OpenAI 兼容格式）
API_KEY=your_api_key
BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-v4-flash
```

### 启动

**CLI 模式：**
```bash
# 方式 1：使用 uv
uv run nl2sql-cli

# 方式 2：直接运行
.\.venv\Scripts\python.exe -m app.cli
```

**API 模式：**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API 使用

### 查询接口

```bash
POST http://localhost:8000/query
Content-Type: application/json

{
  "question": "查询用户表的前10条记录"
}
```

### 响应示例

```json
{
  "question": "查询用户表的前10条记录",
  "sql": "SELECT * FROM users LIMIT 10",
  "columns": ["id", "name", "email"],
  "rows": [[1, "Alice", "alice@example.com"], ...],
  "error": null
}
```

### 健康检查

```bash
GET http://localhost:8000/health
```

## 项目结构

```
nl2sql-agent/
├── app/
│   ├── agents/          # AI Agent 核心逻辑
│   │   └── sql_agent.py
│   ├── api/             # FastAPI 接口
│   │   └── query.py
│   ├── cli/             # 终端 CLI 界面
│   │   ├── app.py       # Textual TUI 应用
│   │   ├── i18n.py      # 国际化翻译
│   │   ├── history.py   # 历史记录持久化
│   │   └── favorites.py # 查询收藏
│   ├── core/            # 核心配置
│   │   ├── config.py    # 环境变量配置
│   │   └── database.py  # 数据库连接
│   ├── schemas/         # Pydantic 数据模型
│   ├── services/        # 外部服务
│   │   └── llm.py       # LLM API 调用
│   └── main.py          # FastAPI 入口
├── .env                 # 环境变量（不提交）
├── pyproject.toml       # 项目配置
└── README.md
```

## 数据持久化

所有用户数据保存在 `.nl2sql/` 目录：

| 文件 | 说明 |
|------|------|
| `chat_history.json` | 聊天记录 |
| `input_history.json` | 输入历史 |
| `db_config.json` | 数据库配置 |
| `favorites.json` | 查询收藏 |

## 安全特性

- **只读模式** — 默认禁止写入操作
- **写入确认** — 执行写入前需二次确认
- **危险操作拦截** — DROP/ALTER/TRUNCATE 等始终禁止
- **SQL 注入防护** — 参数化查询
- **凭据脱敏** — 配置显示时隐藏密码

## 技术栈

- **后端**: FastAPI + SQLAlchemy (async)
- **CLI**: Textual (Python TUI 框架)
- **数据库**: MySQL (aiomysql)
- **LLM**: OpenAI 兼容 API
- **包管理**: uv

## 运行测试

```bash
uv run pytest test_cli_integration.py -v
```

## License

MIT
