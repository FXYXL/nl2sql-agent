from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, RichLog
from textual.containers import Vertical, VerticalScroll
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


class NL2SQLApp(App):
    """NL2SQL Agent CLI with three-panel layout."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 250;
        grid-rows: 1fr auto;
    }

    #main-area {
        row-span: 2;
        height: 100%;
    }

    #message-container {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #sidebar {
        row-span: 2;
        border: solid $secondary;
        padding: 1;
    }

    #input-container {
        height: 3;
        border: solid $primary;
        padding: 0 1;
    }

    #user-input {
        width: 100%;
    }

    #history-log {
        height: 10;
    }

    #commands-list {
        height: auto;
    }

    #command-palette {
        display: none;
        dock: top;
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
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-area"):
            with VerticalScroll(id="message-container"):
                yield RichLog(id="message-log", auto_scroll=True, markup=True)
            with Vertical(id="input-container"):
                yield Static("/ for commands", id="command-palette")
                yield Input(placeholder="Ask a question...", id="user-input")
        yield Sidebar(id="sidebar")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#message-log", RichLog).write(
            "[bold green]NL2SQL Agent[/] - Type your question or / for commands"
        )

    @on(Input.Changed, "#user-input")
    def handle_input_changed(self, event: Input.Changed) -> None:
        palette = self.query_one("#command-palette")
        if event.value == "/":
            palette.add_class("visible")
            palette.update(
                "[bold]/help[/]     - Show help\n"
                "[bold]/clear[/]    - Clear messages\n"
                "[bold]/history[/]  - Show history\n"
                "[bold]/export[/]   - Export history\n"
                "[bold]/config[/]   - Show config\n"
                "[bold]/schema[/]   - Show DB schema"
            )
        else:
            palette.remove_class("visible")

    @on(Input.Submitted, "#user-input")
    async def handle_input(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        event.input.value = ""

        if not value:
            return

        if value.startswith("/"):
            await self.handle_command(value)
        else:
            await self.handle_question(value)

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
