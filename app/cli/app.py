from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, RichLog, OptionList
from textual.widgets.option_list import Option
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.binding import Binding
from textual import on
from rich.table import Table
from rich.text import Text
import time

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
        self._input_history: list[str] = []
        self._history_index = -1
        self._last_sql: str = ""
        self._last_result: dict = {}
        self._pending_clear = False

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
        if "-visible" in palette.classes:
            if self._command_index > 0:
                self._command_index -= 1
                palette.highlighted = self._command_index
        else:
            input_widget = self.query_one("#user-input", Input)
            if self._input_history and self._history_index < len(self._input_history) - 1:
                self._history_index += 1
                input_widget.value = self._input_history[-(self._history_index + 1)]

    def action_next_command(self) -> None:
        palette = self.query_one("#command-palette", OptionList)
        if "-visible" in palette.classes:
            if self._command_index < len(palette.option_count) - 1:
                self._command_index += 1
                palette.highlighted = self._command_index
        else:
            input_widget = self.query_one("#user-input", Input)
            if self._history_index > 0:
                self._history_index -= 1
                input_widget.value = self._input_history[-(self._history_index + 1)]
            elif self._history_index == 0:
                self._history_index = -1
                input_widget.value = ""

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
        self._history_index = -1

        if not value:
            return

        if self._pending_clear:
            self._pending_clear = False
            if value.lower() in ("y", "yes", "是", "确认"):
                self.query_one("#message-log", RichLog).clear()
                self.query_one("#message-log", RichLog).write(
                    f"[dim]{self._i18n.t('cleared')}[/]"
                )
            return

        if value.startswith("/"):
            self.run_command(value)
        else:
            if value not in self._input_history:
                self._input_history.append(value)
            self.run_question(value)

    def run_command(self, command: str) -> None:
        import asyncio
        asyncio.ensure_future(self.handle_command(command))

    def run_question(self, question: str) -> None:
        import asyncio
        asyncio.ensure_future(self.handle_question(question))

    def _build_result_table(self, columns: list[str], rows: list[list]) -> Table:
        table = Table(show_header=True, header_style="bold cyan", show_lines=True, expand=True)
        for col in columns:
            table.add_column(str(col), overflow="ellipsis")
        for row in rows:
            table.add_row(*[str(v) if v is not None else "NULL" for v in row])
        return table

    async def handle_question(self, question: str) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)
        history_log = self.query_one("#history-log", RichLog)

        log.write(f"[bold blue]{t('you_label')}:[/] {question}")
        history_log.write(f"[dim]{question[:30]}...[/]" if len(question) > 30 else f"[dim]{question}[/]")

        log.write(f"[dim]{t('thinking')}[/]")

        start_time = time.time()
        try:
            from app.agents.sql_agent import ask
            result = await ask(question)
            elapsed = time.time() - start_time

            self._last_sql = result.get("sql", "")
            self._last_result = result

            if result.get("error"):
                log.write(f"[bold red]{t('error_label')}:[/] {result['error']}")
            else:
                log.write(f"[bold green]{t('sql_label')}:[/] {result['sql']}")

                columns = result.get("columns", [])
                rows = result.get("rows", [])

                if columns and rows:
                    table = self._build_result_table(columns, rows)
                    log.write(table)

                    if len(rows) >= 1000:
                        log.write(f"[dim yellow]... {t('results_label')}: {len(rows)} {t('rows_unit')} ({t('truncated')})[/]")
                    else:
                        log.write(f"[dim]{t('results_label')}: {len(rows)} {t('rows_unit')}[/]")
                elif columns:
                    log.write(f"[dim]{t('no_data')}[/]")
                else:
                    log.write(f"[dim]{t('results_label')}: 0 {t('rows_unit')}[/]")

                log.write(f"[dim]{t('elapsed')}: {elapsed:.2f}s[/]")
        except Exception as e:
            elapsed = time.time() - start_time
            log.write(f"[bold red]{t('error_label')}:[/] {e}")
            log.write(f"[dim]{t('elapsed')}: {elapsed:.2f}s[/]")

    async def handle_command(self, command: str) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        cmd = command.lower().strip()

        if cmd == "/help":
            log.write(t("help_text"))
        elif cmd == "/clear":
            self._pending_clear = True
            log.write(f"[bold yellow]{t('confirm_clear')}[/]")
        elif cmd == "/history":
            log.write(f"[bold yellow]{t('history_title')}:[/]")
            history = self.query_one("#history-log", RichLog)
            for line in history.lines:
                log.write(f"  {line.text}")
        elif cmd == "/export":
            await self.export_history()
        elif cmd == "/export csv":
            await self.export_csv()
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

    async def export_csv(self) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        if not self._last_result or not self._last_result.get("columns"):
            log.write(f"[yellow]{t('no_result_to_export')}[/]")
            return

        try:
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(self._last_result["columns"])
            for row in self._last_result.get("rows", []):
                writer.writerow(row)

            with open("query_result.csv", "w", encoding="utf-8", newline="") as f:
                f.write(output.getvalue())

            log.write(f"[green]{t('csv_exported')}[/]")
        except Exception as e:
            log.write(f"[bold red]{t('export_error')}:[/] {e}")

    def action_clear_messages(self) -> None:
        self.query_one("#message-log", RichLog).clear()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display
