from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, RichLog, OptionList
from textual.widgets.option_list import Option
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.binding import Binding
from textual import on
from rich.table import Table
from rich.panel import Panel
import time
import re

from app.cli.i18n import I18n
from app.cli.history import (
    save_input_history, load_input_history,
    save_chat_message, load_chat_history, clear_chat_history,
    save_db_config, load_db_config,
)
from app.cli.favorites import (
    load_favorites, save_favorite, remove_favorite, get_favorite,
)


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

    #message-container:focus-within {
        border: solid $accent;
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

    #autocomplete-popup {
        display: none;
        dock: bottom;
        max-height: 10;
        border: solid $accent;
        padding: 1;
    }

    #autocomplete-popup.visible {
        display: block;
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

    #status-bar {
        height: 1;
        background: $primary-background-lighten-2;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_messages", "Clear"),
        Binding("ctrl+h", "toggle_sidebar", "Sidebar"),
        Binding("up", "prev_command", "Prev", show=False, priority=True),
        Binding("down", "next_command", "Next", show=False, priority=True),
        Binding("tab", "accept_autocomplete", "Accept", show=False, priority=True),
    ]

    def __init__(self):
        super().__init__()
        self._command_index = -1
        self._i18n = I18n()
        self._input_history: list[str] = load_input_history()
        self._history_index = -1
        self._last_sql: str = ""
        self._last_result: dict = {}
        self._all_results: list[dict] = []
        self._current_page = 0
        self._rows_per_page = 50
        self._pending_clear = False
        self._pending_write: str = ""
        self._write_mode = False
        self._autocomplete_items: list[str] = []
        self._autocomplete_index = -1
        self._schema_cache: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="root"):
            with Horizontal(id="content-area"):
                with Vertical(id="main-area"):
                    yield OptionList(id="command-palette")
                    yield OptionList(id="autocomplete-popup")
                    with VerticalScroll(id="message-container"):
                        yield RichLog(id="message-log", auto_scroll=True, markup=True)
                yield Sidebar(id="sidebar")
            yield Static(id="status-bar")
            with Vertical(id="input-container"):
                yield Input(id="user-input")
        yield Footer()

    def on_mount(self) -> None:
        self._update_ui_texts()
        self._load_persisted_db_config()
        self._load_persisted_history()
        self._update_status_bar()
        palette = self.query_one("#command-palette", OptionList)
        palette.remove_class("visible")
        popup = self.query_one("#autocomplete-popup", OptionList)
        popup.remove_class("visible")

    def _load_persisted_db_config(self) -> None:
        saved_url = load_db_config()
        if saved_url:
            import os
            current_url = os.environ.get("DATABASE_URL", "")
            if saved_url != current_url:
                import asyncio
                asyncio.ensure_future(self._apply_db_config(saved_url))

    async def _apply_db_config(self, url: str) -> None:
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            from app.core import database

            new_engine = create_async_engine(url, echo=False)
            async with new_engine.begin() as conn:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )

            database.engine.dispose()
            database.engine = new_engine
            database.invalidate_schema_cache()

            import os
            os.environ["DATABASE_URL"] = url
        except Exception:
            pass

    def _load_persisted_history(self) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)
        history_log = self.query_one("#history-log", RichLog)

        chat_messages = load_chat_history()
        if chat_messages:
            for msg in chat_messages[-20:]:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    log.write(f"[bold blue]{t('you_label')}:[/] {content}")
                    truncated = content[:30] + "..." if len(content) > 30 else content
                    history_log.write(f"[dim]{truncated}[/]")
                elif role == "assistant":
                    log.write(content)
            log.write(f"[dim]{t('history_loaded')}[/]")
        else:
            log.write(t("welcome"))

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

    def _update_status_bar(self) -> None:
        t = self._i18n.t
        from app.core.config import MODEL_NAME
        write_status = "[bold green]W[/]" if self._write_mode else "[dim]R[/]"
        status = f" LLM:{MODEL_NAME} | {write_status}"
        self.query_one("#status-bar", Static).update(status)

    async def _load_schema_for_autocomplete(self) -> None:
        if not self._schema_cache:
            try:
                from app.core.database import get_database_schema
                schema = await get_database_schema()
                tables = re.findall(r'表名: (\w+)', schema)
                cols = re.findall(r'- (\w+) \(', schema)
                self._schema_cache = tables + cols
            except Exception:
                self._schema_cache = []

    @on(Input.Changed, "#user-input")
    def handle_input_changed(self, event: Input.Changed) -> None:
        palette = self.query_one("#command-palette", OptionList)
        popup = self.query_one("#autocomplete-popup", OptionList)
        value = event.value

        if value.startswith("/"):
            popup.remove_class("visible")
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

            if len(value) >= 2 and not value.startswith("/"):
                import asyncio
                asyncio.ensure_future(self._show_autocomplete(value))
            else:
                popup.remove_class("visible")

    async def _show_autocomplete(self, typed: str) -> None:
        await self._load_schema_for_autocomplete()
        popup = self.query_one("#autocomplete-popup", OptionList)
        typed_lower = typed.lower()

        matches = [item for item in self._schema_cache if typed_lower in item.lower()]

        if matches:
            popup.clear_options()
            popup.add_options(matches[:10])
            popup.add_class("visible")
            self._autocomplete_items = matches[:10]
            self._autocomplete_index = 0
            popup.highlighted = 0
        else:
            popup.remove_class("visible")

    def action_accept_autocomplete(self) -> None:
        popup = self.query_one("#autocomplete-popup", OptionList)
        if "-visible" in popup.classes and self._autocomplete_items:
            input_widget = self.query_one("#user-input", Input)
            current = input_widget.value
            parts = current.rsplit(" ", 1)
            if len(parts) > 1:
                input_widget.value = parts[0] + " " + self._autocomplete_items[self._autocomplete_index] + " "
            else:
                input_widget.value = self._autocomplete_items[self._autocomplete_index] + " "
            popup.remove_class("visible")

    def action_prev_command(self) -> None:
        palette = self.query_one("#command-palette", OptionList)
        popup = self.query_one("#autocomplete-popup", OptionList)

        if "-visible" in popup.classes:
            if self._autocomplete_index > 0:
                self._autocomplete_index -= 1
                popup.highlighted = self._autocomplete_index
        elif "-visible" in palette.classes:
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
        popup = self.query_one("#autocomplete-popup", OptionList)

        if "-visible" in popup.classes:
            if self._autocomplete_index < len(self._autocomplete_items) - 1:
                self._autocomplete_index += 1
                popup.highlighted = self._autocomplete_index
        elif "-visible" in palette.classes:
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
        popup = self.query_one("#autocomplete-popup", OptionList)
        value = event.value.strip()
        event.input.value = ""

        palette.remove_class("visible")
        popup.remove_class("visible")
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

        if self._pending_write:
            sql = self._pending_write
            self._pending_write = ""
            if value.lower() in ("y", "yes", "是", "确认"):
                self.run_write(sql)
            else:
                self.query_one("#message-log", RichLog).write(
                    f"[dim]{self._i18n.t('write_cancelled')}[/]"
                )
            return

        if value.startswith("/"):
            self.run_command(value)
        else:
            if value not in self._input_history:
                self._input_history.append(value)
                save_input_history(self._input_history)
            self.run_question(value)

    def run_command(self, command: str) -> None:
        import asyncio
        asyncio.ensure_future(self.handle_command(command))

    def run_question(self, question: str) -> None:
        import asyncio
        asyncio.ensure_future(self.handle_question(question))

    def run_write(self, sql: str) -> None:
        import asyncio
        asyncio.ensure_future(self.execute_write(sql))

    def _build_result_table(self, columns: list[str], rows: list[list]) -> Table:
        table = Table(show_header=True, header_style="bold cyan", show_lines=True, expand=True)
        for col in columns:
            table.add_column(str(col), overflow="ellipsis")
        for row in rows:
            table.add_row(*[str(v) if v is not None else "NULL" for v in row])
        return table

    def _show_paginated_results(self, columns: list[str], rows: list[list]) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        self._all_results = [{"columns": columns, "rows": rows}]
        self._current_page = 0

        total_rows = len(rows)
        total_pages = max(1, (total_rows + self._rows_per_page - 1) // self._rows_per_page)

        start = 0
        end = min(self._rows_per_page, total_rows)
        page_rows = rows[start:end]

        table = self._build_result_table(columns, page_rows)
        log.write(table)

        if total_pages > 1:
            log.write(f"[dim]{t('page_info').format(current=1, total=total_pages, count=total_rows)}[/]")

    async def handle_question(self, question: str) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)
        history_log = self.query_one("#history-log", RichLog)

        log.write(f"[bold blue]{t('you_label')}:[/] {question}")
        history_log.write(f"[dim]{question[:30]}...[/]" if len(question) > 30 else f"[dim]{question}[/]")
        save_chat_message("user", question)

        log.write(f"[dim]{t('thinking')}[/]")

        start_time = time.time()
        try:
            from app.agents.sql_agent import ask
            result = await ask(question, allow_writes=self._write_mode)
            elapsed = time.time() - start_time

            self._last_sql = result.get("sql", "")
            self._last_result = result

            if result.get("error"):
                log.write(f"[bold red]{t('error_label')}:[/] {result['error']}")
            elif result.get("is_write"):
                if result.get("affected_rows") is not None:
                    log.write(f"[bold green]{t('write_executed')}[/] ({result['affected_rows']} rows affected)")
                else:
                    log.write(f"[bold green]{t('write_executed')}[/]")
            else:
                log.write(f"[bold green]{t('sql_label')}:[/] {result['sql']}")

                columns = result.get("columns", [])
                rows = result.get("rows", [])

                if columns and rows:
                    self._show_paginated_results(columns, rows)
                elif columns:
                    log.write(f"[dim]{t('no_data')}[/]")
                else:
                    log.write(f"[dim]{t('results_label')}: 0 {t('rows_unit')}[/]")

                log.write(f"[dim]{t('elapsed')}: {elapsed:.2f}s[/]")

            if result.get("sql"):
                save_chat_message("assistant", f"SQL: {result['sql']}")
        except Exception as e:
            elapsed = time.time() - start_time
            log.write(f"[bold red]{t('error_label')}:[/] {e}")
            log.write(f"[dim]{t('elapsed')}: {elapsed:.2f}s[/]")

    async def execute_write(self, sql: str) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        log.write(f"[bold green]{t('sql_label')}:[/] {sql}")
        log.write(f"[dim]{t('thinking')}[/]")

        start_time = time.time()
        try:
            from app.core.database import execute_sql
            columns, rows = await execute_sql(sql)
            elapsed = time.time() - start_time

            if rows:
                log.write(f"[bold green]{t('write_executed')}[/] ({rows[0][0]} rows affected)")
            else:
                log.write(f"[bold green]{t('write_executed')}[/]")

            log.write(f"[dim]{t('elapsed')}: {elapsed:.2f}s[/]")
            save_chat_message("assistant", f"Write: {sql}")
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
            write_status = "ON" if self._write_mode else "OFF"
            log.write(f"[bold yellow]{t('config_title')}:[/]\n"
                      f"  Database: {masked_db}\n"
                      f"  LLM: {MODEL_NAME}\n"
                      f"  API: {BASE_URL}\n"
                      f"  Write mode: {write_status}")
        elif cmd == "/schema":
            from app.core.database import get_database_schema
            try:
                schema = await get_database_schema()
                log.write(f"[bold yellow]{t('schema_title')}:[/]\n{schema}")
            except Exception as e:
                log.write(f"[bold red]{t('schema_error')}:[/] {e}")
        elif cmd == "/write":
            self._write_mode = not self._write_mode
            self._update_status_bar()
            if self._write_mode:
                log.write(f"[bold yellow]{t('write_mode_on')}[/]")
            else:
                log.write(f"[dim]{t('write_mode_off')}[/]")
        elif cmd.startswith("/db"):
            parts = command.split(maxsplit=1)
            if len(parts) >= 2:
                await self.switch_database(parts[1])
            else:
                log.write(f"[dim]{t('db_usage')}[/]")
        elif cmd == "/copy":
            if self._last_sql:
                import subprocess
                import platform
                try:
                    if platform.system() == "Windows":
                        process = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
                        process.communicate(self._last_sql.encode("utf-16le"))
                    else:
                        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                        process.communicate(self._last_sql.encode("utf-8"))
                    log.write(f"[green]{t('copied_to_clipboard')}[/]")
                except Exception:
                    log.write(f"[yellow]{self._last_sql}[/]")
            else:
                log.write(f"[yellow]{t('no_sql_to_copy')}[/]")
        elif cmd == "/ping":
            await self.ping_database()
        elif cmd == "/explain":
            await self.explain_query()
        elif cmd.startswith("/page"):
            parts = cmd.split()
            if len(parts) >= 2:
                self.show_page(int(parts[1]))
            else:
                self.show_page(1)
        elif cmd.startswith("/fav"):
            await self.handle_fav_command(command)
        elif cmd == "/quit":
            self.exit()
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

    async def ping_database(self) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        start_time = time.time()
        try:
            from app.core.database import engine
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            elapsed = time.time() - start_time
            log.write(f"[green]{t('ping_ok')}[/] ({t('ping_latency')}: {elapsed:.3f}s)")
        except Exception as e:
            elapsed = time.time() - start_time
            log.write(f"[bold red]{t('ping_fail')}:[/] {e}")

    async def explain_query(self) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        if not self._last_sql:
            log.write(f"[yellow]{t('no_sql_to_copy')}[/]")
            return

        sql = self._last_sql.strip()
        if sql.upper().startswith("SELECT"):
            explain_sql = f"EXPLAIN {sql}"
        else:
            log.write(f"[yellow]EXPLAIN only supports SELECT queries[/]")
            return

        try:
            from app.core.database import engine
            from sqlalchemy import text
            async with engine.connect() as conn:
                result = await conn.execute(text(explain_sql))
                columns = list(result.keys())
                rows = [list(row) for row in result.fetchall()]

            log.write(f"[bold yellow]{t('explain_title')}:[/]")
            table = self._build_result_table(columns, rows)
            log.write(table)
        except Exception as e:
            log.write(f"[bold red]{t('error_label')}:[/] {e}")

    def show_page(self, page_num: int) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        if not self._all_results:
            log.write(f"[yellow]{t('no_pages')}[/]")
            return

        result = self._all_results[0]
        columns = result["columns"]
        rows = result["rows"]

        total_rows = len(rows)
        total_pages = max(1, (total_rows + self._rows_per_page - 1) // self._rows_per_page)

        if page_num < 1 or page_num > total_pages:
            log.write(f"[yellow]{t('no_pages')}[/]")
            return

        self._current_page = page_num - 1
        start = self._current_page * self._rows_per_page
        end = min(start + self._rows_per_page, total_rows)
        page_rows = rows[start:end]

        table = self._build_result_table(columns, page_rows)
        log.write(table)
        log.write(f"[dim]{t('page_info').format(current=page_num, total=total_pages, count=total_rows)}[/]")

    async def handle_fav_command(self, command: str) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        parts = command.split(maxsplit=2)
        if len(parts) < 2:
            log.write(f"[bold yellow]{t('fav_list_title')}:[/]\n"
                      "  /fav save [name] - Save last SQL\n"
                      "  /fav list        - List all favorites\n"
                      "  /fav run N       - Execute favorite N\n"
                      "  /fav del N       - Delete favorite N")
            return

        action = parts[1].lower()

        if action == "save":
            if self._last_sql:
                name = parts[2] if len(parts) >= 3 else f"fav_{len(load_favorites()) + 1}"
                save_favorite(name, self._last_sql)
                log.write(f"[green]{t('fav_saved')}: {name}[/]")
            else:
                log.write(f"[yellow]{t('no_sql_to_copy')}[/]")

        elif action == "list":
            favorites = load_favorites()
            if not favorites:
                log.write(f"[dim]{t('fav_empty')}[/]")
                return

            log.write(f"[bold yellow]{t('fav_list_title')}:[/]")
            table = Table(show_header=True, header_style="bold cyan", show_lines=True)
            table.add_column("#", style="dim")
            table.add_column("Name")
            table.add_column("SQL", overflow="ellipsis")
            for i, fav in enumerate(favorites):
                table.add_row(str(i + 1), fav["name"], fav["sql"][:50])
            log.write(table)

        elif action == "run":
            if len(parts) >= 3:
                try:
                    idx = int(parts[2]) - 1
                    fav = get_favorite(idx)
                    if fav:
                        sql = fav["sql"]
                        log.write(f"[bold blue]SQL:[/] {sql}")
                        import asyncio
                        asyncio.ensure_future(self._execute_direct_sql(sql))
                    else:
                        log.write(f"[yellow]{t('fav_not_found')}[/]")
                except ValueError:
                    log.write(f"[dim]{t('fav_usage')}[/]")
            else:
                log.write(f"[dim]{t('fav_usage')}[/]")

        elif action == "del":
            if len(parts) >= 3:
                try:
                    idx = int(parts[2]) - 1
                    if remove_favorite(idx):
                        log.write(f"[green]{t('fav_deleted')}[/]")
                    else:
                        log.write(f"[yellow]{t('fav_not_found')}[/]")
                except ValueError:
                    log.write(f"[dim]{t('fav_usage')}[/]")
            else:
                log.write(f"[dim]{t('fav_usage')}[/]")
        else:
            log.write(f"[dim]{t('fav_usage')}[/]")

    async def _execute_direct_sql(self, sql: str) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        start_time = time.time()
        try:
            from app.core.database import execute_sql
            columns, rows = await execute_sql(sql)
            elapsed = time.time() - start_time

            if columns and rows:
                self._show_paginated_results(columns, rows)
            elif columns:
                log.write(f"[dim]{t('no_data')}[/]")
            else:
                log.write(f"[dim]{t('results_label')}: 0 {t('rows_unit')}[/]")

            log.write(f"[dim]{t('elapsed')}: {elapsed:.2f}s[/]")
        except Exception as e:
            elapsed = time.time() - start_time
            log.write(f"[bold red]{t('error_label')}:[/] {e}")
            log.write(f"[dim]{t('elapsed')}: {elapsed:.2f}s[/]")

    async def switch_database(self, url: str) -> None:
        t = self._i18n.t
        log = self.query_one("#message-log", RichLog)

        try:
            from app.core.database import engine
            from sqlalchemy.ext.asyncio import create_async_engine
            from app.core import database

            new_engine = create_async_engine(url, echo=False)

            async with new_engine.begin() as conn:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )

            database.engine.dispose()
            database.engine = new_engine
            database.invalidate_schema_cache()

            import os
            os.environ["DATABASE_URL"] = url
            save_db_config(url)

            log.write(f"[green]{t('db_connected')}[/]")
        except Exception as e:
            log.write(f"[bold red]{t('db_connect_error')}:[/] {e}")

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
