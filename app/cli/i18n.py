TRANSLATIONS = {
    "en": {
        "welcome": "[bold green]NL2SQL Agent[/] - Type your question or / for commands",
        "you_label": "You",
        "thinking": "Thinking...",
        "error_label": "Error",
        "sql_label": "SQL",
        "results_label": "Results",
        "rows_unit": "rows",
        "no_data": "No data",
        "elapsed": "Elapsed",
        "truncated": "showing first 1000 rows",
        "placeholder": "Ask a question...",
        "sidebar_history": "── History ──",
        "sidebar_commands": "── Commands ──",
        "history_title": "Chat History",
        "config_title": "Config",
        "schema_title": "Schema",
        "schema_error": "Error fetching schema",
        "export_success": "History exported to nl2sql_history.txt",
        "csv_exported": "Results exported to query_result.csv",
        "no_result_to_export": "No query result to export",
        "export_error": "Export failed",
        "cleared": "Messages cleared",
        "confirm_clear": "Are you sure? Type y to confirm",
        "unknown_command": "Unknown command",
        "lang_changed": "Language switched to English",
        "lang_switch": "Switch to Chinese",
        "write_mode_on": "Write mode ON - SQL writes allowed",
        "write_mode_off": "Write mode OFF - read only",
        "confirm_write": "This will execute a write operation. Type y to confirm",
        "write_executed": "Write operation executed",
        "write_cancelled": "Write operation cancelled",
        "db_connected": "Database connected",
        "db_connect_error": "Database connection failed",
        "db_usage": "Usage: /db <mysql+aiomysql://user:pass@host:port/db>",
        "history_loaded": "History loaded from disk",
        "copied_to_clipboard": "SQL copied to clipboard",
        "no_sql_to_copy": "No SQL to copy",
        "ping_ok": "Database connection OK",
        "ping_fail": "Database connection failed",
        "ping_latency": "Latency",
        "explain_title": "Query Execution Plan",
        "page_info": "Page {current}/{total} ({count} rows)",
        "no_pages": "No more pages",
        "fav_saved": "Favorite saved",
        "fav_deleted": "Favorite deleted",
        "fav_not_found": "Favorite not found",
        "fav_usage": "Usage: /fav [save|list|run|del] [name|index]",
        "fav_list_title": "Saved Favorites",
        "fav_empty": "No saved favorites",
        "autocomplete_hint": "Type to filter, Tab to accept",
        "commands": {
            "/help": "Show help",
            "/clear": "Clear messages",
            "/history": "Show chat history",
            "/export": "Export history to file",
            "/export csv": "Export last result to CSV",
            "/config": "Show config",
            "/schema": "Show DB schema",
            "/write": "Toggle write mode",
            "/db": "Switch database",
            "/copy": "Copy last SQL to clipboard",
            "/ping": "Check database health",
            "/explain": "Show query execution plan",
            "/page": "Show result page (page N)",
            "/fav": "Manage query favorites",
            "/quit": "Quit application",
        },
        "help_text": (
            "[bold yellow]Commands:[/]\n"
            "  /help       - Show this help\n"
            "  /clear      - Clear message area\n"
            "  /history    - Show chat history\n"
            "  /export     - Export history to nl2sql_history.txt\n"
            "  /export csv - Export last result to CSV\n"
            "  /config     - Show current configuration\n"
            "  /schema     - Show database schema\n"
            "  /write      - Toggle write mode (INSERT/UPDATE/DELETE)\n"
            "  /db         - Switch database connection\n"
            "  /copy       - Copy last SQL to clipboard\n"
            "  /ping       - Check database health\n"
            "  /explain    - Show last query execution plan\n"
            "  /page N     - Show result page N\n"
            "  /fav save   - Save last query as favorite\n"
            "  /fav list   - List saved favorites\n"
            "  /fav run N  - Execute favorite N\n"
            "  /fav del N  - Delete favorite N\n"
            "  /quit       - Quit application\n"
            "  /lang       - Switch to Chinese\n\n"
            "[dim]Keyboard shortcuts:[/]\n"
            "  Up/Down     - Browse input history\n"
            "  Tab         - Accept autocomplete suggestion\n"
            "  Ctrl+L      - Clear messages\n"
            "  Ctrl+H      - Toggle sidebar\n"
            "  Ctrl+C      - Quit"
        ),
    },
    "zh": {
        "welcome": "[bold green]NL2SQL 助手[/] - 输入问题或 / 查看命令",
        "you_label": "你",
        "thinking": "思考中...",
        "error_label": "错误",
        "sql_label": "SQL",
        "results_label": "结果",
        "rows_unit": "行",
        "no_data": "无数据",
        "elapsed": "耗时",
        "truncated": "显示前 1000 行",
        "placeholder": "请输入问题...",
        "sidebar_history": "── 历史记录 ──",
        "sidebar_commands": "── 命令列表 ──",
        "history_title": "聊天历史",
        "config_title": "配置",
        "schema_title": "数据库结构",
        "schema_error": "获取数据库结构失败",
        "export_success": "历史记录已导出到 nl2sql_history.txt",
        "csv_exported": "查询结果已导出到 query_result.csv",
        "no_result_to_export": "没有可导出的查询结果",
        "export_error": "导出失败",
        "cleared": "消息已清空",
        "confirm_clear": "确认清空？输入 y 确认",
        "unknown_command": "未知命令",
        "lang_changed": "语言已切换为中文",
        "lang_switch": "切换到英文",
        "write_mode_on": "写入模式已开启 - 允许 SQL 写入操作",
        "write_mode_off": "写入模式已关闭 - 只读模式",
        "confirm_write": "即将执行写入操作，输入 y 确认",
        "write_executed": "写入操作已执行",
        "write_cancelled": "写入操作已取消",
        "db_connected": "数据库已连接",
        "db_connect_error": "数据库连接失败",
        "db_usage": "用法: /db <mysql+aiomysql://用户名:密码@主机:端口/数据库>",
        "history_loaded": "历史记录已从磁盘加载",
        "copied_to_clipboard": "SQL 已复制到剪贴板",
        "no_sql_to_copy": "没有可复制的 SQL",
        "ping_ok": "数据库连接正常",
        "ping_fail": "数据库连接失败",
        "ping_latency": "延迟",
        "explain_title": "查询执行计划",
        "page_info": "第 {current}/{total} 页（共 {count} 行）",
        "no_pages": "没有更多页了",
        "fav_saved": "收藏已保存",
        "fav_deleted": "收藏已删除",
        "fav_not_found": "收藏不存在",
        "fav_usage": "用法: /fav [save|list|run|del] [名称|序号]",
        "fav_list_title": "收藏列表",
        "fav_empty": "没有收藏",
        "autocomplete_hint": "输入过滤，Tab 接受建议",
        "commands": {
            "/help": "显示帮助",
            "/clear": "清空消息",
            "/history": "查看聊天历史",
            "/export": "导出历史到文件",
            "/export csv": "导出上次结果到 CSV",
            "/config": "查看配置",
            "/schema": "查看数据库结构",
            "/write": "切换写入模式",
            "/db": "切换数据库",
            "/copy": "复制上次 SQL 到剪贴板",
            "/ping": "检测数据库健康",
            "/explain": "查看查询执行计划",
            "/page": "查看结果分页 (page N)",
            "/fav": "管理查询收藏",
            "/quit": "退出应用",
        },
        "help_text": (
            "[bold yellow]命令列表:[/]\n"
            "  /help       - 显示帮助\n"
            "  /clear      - 清空消息\n"
            "  /history    - 查看聊天历史\n"
            "  /export     - 导出历史到 nl2sql_history.txt\n"
            "  /export csv - 导出上次结果到 CSV\n"
            "  /config     - 查看当前配置\n"
            "  /schema     - 查看数据库结构\n"
            "  /write      - 切换写入模式 (INSERT/UPDATE/DELETE)\n"
            "  /db         - 切换数据库连接\n"
            "  /copy       - 复制上次 SQL 到剪贴板\n"
            "  /ping       - 检测数据库健康\n"
            "  /explain    - 查看上次查询执行计划\n"
            "  /page N     - 查看第 N 页结果\n"
            "  /fav save   - 保存上次查询到收藏\n"
            "  /fav list   - 列出收藏\n"
            "  /fav run N  - 执行收藏 N\n"
            "  /fav del N  - 删除收藏 N\n"
            "  /quit       - 退出应用\n"
            "  /lang       - 切换到英文\n\n"
            "[dim]快捷键:[/]\n"
            "  上/下        - 翻看输入历史\n"
            "  Tab         - 接受自动补全建议\n"
            "  Ctrl+L      - 清空消息\n"
            "  Ctrl+H      - 切换侧栏\n"
            "  Ctrl+C      - 退出"
        ),
    },
}


class I18n:
    def __init__(self, lang: str = "zh"):
        self.lang = lang

    def t(self, key: str) -> str:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["zh"]).get(key, key)

    def get_commands(self) -> list[tuple[str, str]]:
        t = TRANSLATIONS.get(self.lang, TRANSLATIONS["zh"])
        cmds = [(k, v) for k, v in t["commands"].items()]
        if self.lang == "zh":
            cmds.append(("/lang en", t["lang_switch"]))
        else:
            cmds.append(("/lang zh", t["lang_switch"]))
        return cmds

    def switch_lang(self, lang: str) -> None:
        if lang in TRANSLATIONS:
            self.lang = lang
