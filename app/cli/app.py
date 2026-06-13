from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, RichLog, OptionList
from textual.widgets.option_list import Option
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.binding import Binding
from textual import on

from app.cli.i18n import I18n


class Sidebar(Static):
    """Right sidebar showing history and commands."""

    def compose(self) -> ComposeResult:
        yield Static(id="history-title")
        yield RichLog(id="history-log", auto_scroll=True)
        yield Static(id="commands-title")
        yield Static(id="commands-list")


class NL2SQLApp(App):
    """NL2SQL Agent CLI with three-panel layout."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #root {
        height: 1fr;
    }

    #content-area {
        height: 1fr;
    }

    #main-area {
        width: 1fr;
        height: 1fr;
    }

    #message-container {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #sidebar {
        dock: right;
        width: 30;
        height: 1fr;
        border: solid $secondary;
        padding: 1;
    }

    #input-container {
        dock: bottom;
        height: 7;
        border: solid $primary;
        padding: 1;
    }

    #user-input {
        width: 100%;
    }

    #history-log {
        height: 1fr;
        max-height: 15;
    }

    #commands-list {
        height: auto;
    }

    #command-palette {
        display: none;
        dock: bottom;
        max-height: 15;
        border: solid $accent;
        padding: 1;
    }

    #command-palette.visible {
        display: block;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_messages", "Clear"),
        Binding("ctrl+h", "toggle_sidebar", "Sidebar"),
        Binding("up", "prev_command", "Prev", show=False, priority=True),
        Binding("down", "next_command", "Next", show=False, priority=True),
    ]

    def __init__(self):
        super().__init__()
        self._command_index = -1
        self._i18n = I18n()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="root"):
            with Horizontal(id="content-area"):
                with Vertical(id="main-area"):
                    yield OptionList(id="command-palette")
                    with VerticalScroll(id="message-container"):
                        yield RichLog(id="message-log", auto_scroll=True, markup=True)
                yield Sidebar(id="sidebar")
            with Vertical(id="input-container"):
                yield Input(id="user-input")
        yield Footer()

    def on_mount(self) -> None:
        self._update_ui_texts()
        self.query_one("#message-log", RichLog).write(self._i18n.t("welcome"))
        palette = self.query_one("#command-palette", OptionList)
        palette.remove_class("visible")

    def _update_ui_texts(self) -> None:
        t = self._i18n.t
        self.query_one("#history-title", Static).update(t("sidebar_history"))
        self.query_one("#commands-title", Static).update(t("sidebar_commands"))
        self.query_one("#commands-list", Static).update(
            "\n".join(f"{cmd}  - {desc}" for cmd, desc in self._i18n.get_commands())
        )
        self.query_one("#user-input", Input).placeholder = t("placeholder")

        palette = self.query_one("#command-palette", OptionList)
        palette.clear_options()
        palette.add_options([f"{cmd}  - {desc}" for cmd, desc in self._i18n.get_commands()])

    @on(Input.Changed, "#user-input")
    def handle_input_changed(self, event: Input.Changed) -> None:
        palette = self.query_one("#command-palette", OptionList)
        value = event.value

        if value.startswith("/"):
            palette.add_class("visible")
            filter_text = value[1:].lower()
            options = [
                f"{cmd}  - {desc}"
                for cmd, desc in self._i18n.get_commands()
                if filter_text in cmd.lower()
            ]
            if options:
                palette.clear_options()
                palette.add_options(options)
                self._command_index = 0
                palette.highlighted = 0
            else:
                palette.remove_class("visible")
        else:
            palette.remove_class("visible")
            self._command_index = -1

    def action_prev_command(self) -> None:
        palette = self.query_one("#command-palette", OptionList)
        if "-visible" not in palette.classes:
            return
        if self._command_index > 0:
            self._command_index -= 1
            palette.highlighted = self._command_index

    def action_next_command(self) -> None:
        palette = self.query_one("#command-palette", OptionList)
        if "-visible" not in palette.classes:
            return
        if self._command_index < len(palette.option_count) - 1:
            self._command_index += 1
            palette.highlighted = self._command_index

    @on(OptionList.OptionSelected, "#command-palette")
    def handle_option_selected(self, event: OptionList.OptionSelected) -> None:
        palette = self.query_one("#command-palette", OptionList)
        option = palette.get_option_at_index(event.option_index)
        if option:
            command = str(option.prompt).split("  ")[0].strip()
            palette.remove_class("visible")
            self._command_index = -1
            self.query_one("#user-input", Input).value = ""
            self.run_command(command)

    @on(Input.Submitted, "#user-input")
    def handle_input(self, event: Input.Submitted) -> None:
        palette = self.query_one("#command-palette", OptionList)
        value = event.value.strip()
        event.input.value = ""

        palette.remove_class("visible")
        self._command_index = -1

        if value:
            if value.startswith("/"):
                self.run_command(value)
            else:
                self.run_question(value)

    def run_command(self, command: str) -> None:
        import asyncio
        asyncio.ensure_future(self.handle_command(command))

    def run_question(self, question: str) -> None:
        import asyncio
        asyncio.ensure_future(self.handle_question(question))

    async def handle_question(self, question: str) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)
        history_log = self.query_one("#history-log", RichLog)

        log.write(f"[bold blue]{t('you_label')}:[/] {question}")
        history_log.write(f"[dim]{question[:30]}...[/]" if len(question) > 30 else f"[dim]{question}[/]")

        log.write(f"[dim]{t('thinking')}[/]")

        try:
            from app.agents.sql_agent import ask
            result = await ask(question)

            if result.get("error"):
                log.write(f"[bold red]{t('error_label')}:[/] {result['error']}")
            else:
                log.write(f"[bold green]{t('sql_label')}:[/] {result['sql']}")

                columns = result.get("columns", [])
                rows = result.get("rows", [])

                if columns and rows:
                    col_widths = [len(str(c)) for c in columns]
                    for row in rows:
                        for i, val in enumerate(row):
                            if i < len(col_widths):
                                col_widths[i] = max(col_widths[i], len(str(val)))

                    header = " | ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(columns))
                    separator = "-+-".join("-" * w for w in col_widths)

                    log.write(f"[dim]{separator}[/]")
                    log.write(f"[bold]{header}[/]")
                    log.write(f"[dim]{separator}[/]")

                    for row in rows:
                        line = " | ".join(str(val).ljust(col_widths[i]) if i < len(col_widths) else str(val) for i, val in enumerate(row))
                        log.write(line)

                    log.write(f"[dim]{separator}[/]")
                    log.write(f"[dim]{t('results_label')}: {len(rows)} {t('rows_unit')}[/]")
                elif columns:
                    log.write(f"[dim]{t('no_data')}[/]")
                else:
                    log.write(f"[dim]{t('results_label')}: {len(rows)} {t('rows_unit')}[/]")
        except Exception as e:
            log.write(f"[bold red]{t('error_label')}:[/] {e}")

    async def handle_command(self, command: str) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        cmd = command.lower().strip()

        if cmd == "/help":
            log.write(t("help_text"))
        elif cmd == "/clear":
            self.query_one("#message-log", RichLog).clear()
            log.write(f"[dim]{t('cleared')}[/]")
        elif cmd == "/history":
            log.write(f"[bold yellow]{t('history_title')}:[/]")
            history = self.query_one("#history-log", RichLog)
            for line in history.lines:
                log.write(f"  {line.text}")
        elif cmd == "/export":
            await self.export_history()
        elif cmd == "/config":
            from app.core.config import DATABASE_URL, BASE_URL, MODEL_NAME
            from urllib.parse import urlparse
            parsed = urlparse(DATABASE_URL)
            masked_db = f"{parsed.scheme}://{parsed.hostname}" + (":{}".format(parsed.port) if parsed.port else "") if parsed.hostname else "(not set)"
            log.write(f"[bold yellow]{t('config_title')}:[/]\n"
                      f"  Database: {masked_db}\n"
                      f"  LLM: {MODEL_NAME}\n"
                      f"  API: {BASE_URL}")
        elif cmd == "/schema":
            from app.core.database import get_database_schema
            try:
                schema = await get_database_schema()
                log.write(f"[bold yellow]{t('schema_title')}:[/]\n{schema}")
            except Exception as e:
                log.write(f"[bold red]{t('schema_error')}:[/] {e}")
        elif cmd.startswith("/lang"):
            parts = cmd.split()
            if len(parts) >= 2 and parts[1] in ("en", "zh"):
                self._i18n.switch_lang(parts[1])
                self._update_ui_texts()
                log.write(f"[green]{t('lang_changed')}[/]")
            else:
                target = "en" if self._i18n.lang == "zh" else "zh"
                self._i18n.switch_lang(target)
                self._update_ui_texts()
                log.write(f"[green]{t('lang_changed')}[/]")
        else:
            log.write(f"[red]{t('unknown_command')}: {command}[/]")

    async def export_history(self) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)
        history = self.query_one("#history-log", RichLog)

        try:
            with open("nl2sql_history.txt", "w", encoding="utf-8") as f:
                for line in history.lines:
                    f.write(line.text + "\n")
            log.write(f"[green]{t('export_success')}[/]")
        except Exception as e:
            log.write(f"[bold red]{t('export_error')}:[/] {e}")

    def action_clear_messages(self) -> None:
        self.query_one("#message-log", RichLog).clear()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display
