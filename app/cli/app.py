from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, RichLog, OptionList
from textual.widgets.option_list import Option
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.binding import Binding
from textual import on


class Sidebar(Static):
    """Right sidebar showing history and commands."""

    def compose(self) -> ComposeResult:
        yield Static("── History ──", id="history-title")
        yield RichLog(id="history-log", auto_scroll=True)
        yield Static("── Commands ──", id="commands-title")
        yield Static(
            "/help     - Show help\n"
            "/clear    - Clear messages\n"
            "/history  - Show chat history\n"
            "/export   - Export history to file\n"
            "/config   - Show config\n"
            "/schema   - Show DB schema",
            id="commands-list"
        )


COMMANDS = [
    ("/help", "Show help"),
    ("/clear", "Clear messages"),
    ("/history", "Show chat history"),
    ("/export", "Export history to file"),
    ("/config", "Show config"),
    ("/schema", "Show DB schema"),
]


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

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="root"):
            with Horizontal(id="content-area"):
                with Vertical(id="main-area"):
                    yield OptionList(
                        *[
                            Option(f"{cmd}  - {desc}")
                            for cmd, desc in COMMANDS
                        ],
                        id="command-palette",
                    )
                    with VerticalScroll(id="message-container"):
                        yield RichLog(id="message-log", auto_scroll=True, markup=True)
                yield Sidebar(id="sidebar")
            with Vertical(id="input-container"):
                yield Input(placeholder="Ask a question...", id="user-input")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#message-log", RichLog).write(
            "[bold green]NL2SQL Agent[/] - Type your question or / for commands"
        )
        palette = self.query_one("#command-palette", OptionList)
        palette.visible = False

    @on(Input.Changed, "#user-input")
    def handle_input_changed(self, event: Input.Changed) -> None:
        palette = self.query_one("#command-palette", OptionList)
        value = event.value

        if value.startswith("/"):
            palette.visible = True
            filter_text = value[1:].lower()
            options = [
                f"{cmd}  - {desc}"
                for cmd, desc in COMMANDS
                if filter_text in cmd.lower()
            ]
            if options:
                palette.clear_options()
                palette.add_options(options)
                self._command_index = 0
                palette.highlighted = 0
            else:
                palette.visible = False
        else:
            palette.visible = False
            self._command_index = -1

    def action_prev_command(self) -> None:
        palette = self.query_one("#command-palette", OptionList)
        if not palette.visible:
            return
        if self._command_index > 0:
            self._command_index -= 1
            palette.highlighted = self._command_index

    def action_next_command(self) -> None:
        palette = self.query_one("#command-palette", OptionList)
        if not palette.visible:
            return
        if self._command_index < len(palette.option_count) - 1:
            self._command_index += 1
            palette.highlighted = self._command_index

    @on(OptionList.OptionSelected, "#command-palette")
    def handle_option_selected(self, event: OptionList.OptionSelected) -> None:
        palette = self.query_one("#command-palette", OptionList)
        if event.option_index < len(COMMANDS):
            command = COMMANDS[event.option_index][0]
            palette.visible = False
            self._command_index = -1
            input_widget = self.query_one("#user-input", Input)
            input_widget.value = ""
            self.run_command(command)

    @on(Input.Submitted, "#user-input")
    def handle_input(self, event: Input.Submitted) -> None:
        palette = self.query_one("#command-palette", OptionList)
        value = event.value.strip()
        event.input.value = ""

        palette.visible = False
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
        log = self.query_one("#message-log", RichLog)
        history_log = self.query_one("#history-log", RichLog)

        log.write(f"[bold blue]You:[/] {question}")
        history_log.write(f"[dim]{question[:30]}...[/]" if len(question) > 30 else f"[dim]{question}[/]")

        log.write("[dim]Thinking...[/]")

        try:
            from app.agents.sql_agent import ask
            result = await ask(question)

            if result.get("error"):
                log.write(f"[bold red]Error:[/] {result['error']}")
            else:
                log.write(f"[bold green]SQL:[/] {result['sql']}")
                if result.get("columns") and result.get("rows"):
                    log.write(f"[dim]Results: {len(result['rows'])} rows[/]")
        except Exception as e:
            log.write(f"[bold red]Error:[/] {e}")

    async def handle_command(self, command: str) -> None:
        log = self.query_one("#message-log", RichLog)

        cmd = command.lower().strip()

        if cmd == "/help":
            log.write("[bold yellow]Commands:[/]\n"
                      "  /help     - Show this help\n"
                      "  /clear    - Clear message area\n"
                      "  /history  - Show chat history\n"
                      "  /export   - Export history to nl2sql_history.txt\n"
                      "  /config   - Show current configuration\n"
                      "  /schema   - Show database schema")
        elif cmd == "/clear":
            self.query_one("#message-log", RichLog).clear()
            log.write("[dim]Messages cleared[/]")
        elif cmd == "/history":
            log.write("[bold yellow]Chat History:[/]")
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
            log.write(f"[bold yellow]Config:[/]\n"
                      f"  Database: {masked_db}\n"
                      f"  LLM: {MODEL_NAME}\n"
                      f"  API: {BASE_URL}")
        elif cmd == "/schema":
            from app.core.database import get_database_schema
            try:
                schema = await get_database_schema()
                log.write(f"[bold yellow]Schema:[/]\n{schema}")
            except Exception as e:
                log.write(f"[bold red]Error fetching schema:[/] {e}")
        else:
            log.write(f"[red]Unknown command: {command}[/]")

    async def export_history(self) -> None:
        log = self.query_one("#message-log", RichLog)
        history = self.query_one("#history-log", RichLog)

        try:
            with open("nl2sql_history.txt", "w", encoding="utf-8") as f:
                for line in history.lines:
                    f.write(line.text + "\n")
            log.write("[green]History exported to nl2sql_history.txt[/]")
        except Exception as e:
            log.write(f"[red]Export failed: {e}[/]")

    def action_clear_messages(self) -> None:
        self.query_one("#message-log", RichLog).clear()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display
