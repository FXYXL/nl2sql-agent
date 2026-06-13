TRANSLATIONS = {
    "en": {
        "welcome": "[bold green]NL2SQL Agent[/] - Type your question or / for commands",
        "you_label": "You",
        "thinking": "Thinking...",
        "error_label": "Error",
        "sql_label": "SQL",
        "results_label": "Results",
        "rows_unit": "rows",
        "placeholder": "Ask a question...",
        "sidebar_history": "── History ──",
        "sidebar_commands": "── Commands ──",
        "history_title": "Chat History",
        "config_title": "Config",
        "schema_title": "Schema",
        "schema_error": "Error fetching schema",
        "export_success": "History exported to nl2sql_history.txt",
        "export_error": "Export failed",
        "cleared": "Messages cleared",
        "unknown_command": "Unknown command",
        "lang_changed": "Language switched to English",
        "commands": {
            "/help": "Show help",
            "/clear": "Clear messages",
            "/history": "Show chat history",
            "/export": "Export history to file",
            "/config": "Show config",
            "/schema": "Show DB schema",
            "/lang": "Switch language (en/zh)",
        },
        "help_text": (
            "[bold yellow]Commands:[/]\n"
            "  /help     - Show this help\n"
            "  /clear    - Clear message area\n"
            "  /history  - Show chat history\n"
            "  /export   - Export history to nl2sql_history.txt\n"
            "  /config   - Show current configuration\n"
            "  /schema   - Show database schema\n"
            "  /lang     - Switch language (en/zh)"
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
        "placeholder": "请输入问题...",
        "sidebar_history": "── 历史记录 ──",
        "sidebar_commands": "── 命令列表 ──",
        "history_title": "聊天历史",
        "config_title": "配置",
        "schema_title": "数据库结构",
        "schema_error": "获取数据库结构失败",
        "export_success": "历史记录已导出到 nl2sql_history.txt",
        "export_error": "导出失败",
        "cleared": "消息已清空",
        "unknown_command": "未知命令",
        "lang_changed": "语言已切换为中文",
        "commands": {
            "/help": "显示帮助",
            "/clear": "清空消息",
            "/history": "查看聊天历史",
            "/export": "导出历史到文件",
            "/config": "查看配置",
            "/schema": "查看数据库结构",
            "/lang": "切换语言 (en/zh)",
        },
        "help_text": (
            "[bold yellow]命令列表:[/]\n"
            "  /help     - 显示帮助\n"
            "  /clear    - 清空消息\n"
            "  /history  - 查看聊天历史\n"
            "  /export   - 导出历史到 nl2sql_history.txt\n"
            "  /config   - 查看当前配置\n"
            "  /schema   - 查看数据库结构\n"
            "  /lang     - 切换语言 (en/zh)"
        ),
    },
}


class I18n:
    def __init__(self, lang: str = "zh"):
        self.lang = lang

    def t(self, key: str) -> str:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["zh"]).get(key, key)

    def get_commands(self) -> list[tuple[str, str]]:
        cmds = TRANSLATIONS.get(self.lang, TRANSLATIONS["zh"])["commands"]
        return [(k, v) for k, v in cmds.items()]

    def get_command_desc(self, cmd: str) -> str:
        cmds = TRANSLATIONS.get(self.lang, TRANSLATIONS["zh"])["commands"]
        return cmds.get(cmd, cmd)

    def switch_lang(self, lang: str) -> None:
        if lang in TRANSLATIONS:
            self.lang = lang
