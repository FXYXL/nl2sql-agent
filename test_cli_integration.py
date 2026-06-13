import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from app.cli.app import NL2SQLApp


def get_richlog_text(widget) -> str:
    """Extract plain text from all rendered lines in a RichLog."""
    parts = []
    for strip in widget.lines:
        parts.append(strip.text)
    return "\n".join(parts)


async def focus_input(app):
    """Focus the input widget and wait."""
    input_w = app.query_one("#user-input")
    input_w.focus()
    from textual import get_app
    # Small pause after focus
    app = get_app()
    await asyncio.sleep(0.05)


async def type_and_submit(app, pilot, text):
    """Type text into the focused input and submit."""
    input_w = app.query_one("#user-input")
    input_w.focus()
    await pilot.pause()
    for ch in text:
        await pilot.press(ch)
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


@pytest.mark.asyncio
async def test_app_starts():
    """Test that the app starts without errors."""
    app = NL2SQLApp()
    async with app.run_test(size=(120, 40)) as pilot:
        assert app.query_one("#message-log") is not None, "message-log not found"
        assert app.query_one("#history-log") is not None, "history-log not found"
        assert app.query_one("#user-input") is not None, "user-input not found"
        assert app.query_one("#sidebar") is not None, "sidebar not found"
        assert app.query_one("#command-palette") is not None, "command-palette not found"
        print("PASS: App starts and all widgets render")
    return True


@pytest.mark.asyncio
async def test_help_command():
    """Test /help command."""
    app = NL2SQLApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await type_and_submit(app, pilot, "/help")

        log = app.query_one("#message-log")
        text = get_richlog_text(log)
        assert "Commands" in text or "help" in text.lower(), f"/help output missing. Got: {text[:300]}"
        print("PASS: /help command works")
    return True


@pytest.mark.asyncio
async def test_clear_command():
    """Test /clear command."""
    app = NL2SQLApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await type_and_submit(app, pilot, "/help")
        await asyncio.sleep(0.1)
        await type_and_submit(app, pilot, "/clear")
        await asyncio.sleep(0.1)

        log = app.query_one("#message-log")
        text = get_richlog_text(log)
        assert "cleared" in text.lower() or "消息已清空" in text or "Messages cleared" in text, f"/clear output missing. Got: {text[:300]}"
        print("PASS: /clear command works")
    return True


@pytest.mark.asyncio
async def test_export_command():
    """Test /export command creates the file."""
    app = NL2SQLApp()
    export_file = "nl2sql_history.txt"
    if os.path.exists(export_file):
        os.remove(export_file)

    async with app.run_test(size=(120, 40)) as pilot:
        await type_and_submit(app, pilot, "/export")
        await asyncio.sleep(0.2)

        log = app.query_one("#message-log")
        text = get_richlog_text(log)
        assert "exported" in text.lower() or "nl2sql_history.txt" in text, f"/export output missing. Got: {text[:300]}"
        assert os.path.exists(export_file), "nl2sql_history.txt was not created"
        content = open(export_file, "r", encoding="utf-8").read()
        print(f"PASS: /export command works. File content length: {len(content)}")
        if os.path.exists(export_file):
            os.remove(export_file)
    return True


@pytest.mark.asyncio
async def test_config_command():
    """Test /config command."""
    app = NL2SQLApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await type_and_submit(app, pilot, "/config")

        log = app.query_one("#message-log")
        text = get_richlog_text(log)
        assert "Config" in text or "Database" in text or "LLM" in text, f"/config output missing. Got: {text[:300]}"
        print("PASS: /config command works")
    return True


@pytest.mark.asyncio
async def test_unknown_command():
    """Test unknown command handling."""
    app = NL2SQLApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await type_and_submit(app, pilot, "/foo")

        log = app.query_one("#message-log")
        text = get_richlog_text(log)
        assert "Unknown" in text or "unknown" in text or "未知命令" in text, f"Unknown command output missing. Got: {text[:300]}"
        print("PASS: Unknown command handling works")
    return True


@pytest.mark.asyncio
async def test_empty_input():
    """Test that empty input is handled gracefully."""
    app = NL2SQLApp()
    async with app.run_test(size=(120, 40)) as pilot:
        input_w = app.query_one("#user-input")
        input_w.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        print("PASS: Empty input handled gracefully")
    return True


@pytest.mark.asyncio
async def test_question_input_mocked():
    """Test question handling with mocked backend."""
    app = NL2SQLApp()
    mock_result = {
        "question": "show all users",
        "sql": "SELECT * FROM users",
        "columns": ["id", "name"],
        "rows": [[1, "Alice"]],
        "error": None,
    }
    async with app.run_test(size=(120, 40)) as pilot:
        with patch("app.agents.sql_agent.ask", new_callable=AsyncMock, return_value=mock_result):
            await type_and_submit(app, pilot, "show all users")
            await asyncio.sleep(0.5)

            log = app.query_one("#message-log")
            text = get_richlog_text(log)
            assert "SQL" in text or "SELECT" in text, f"SQL result not shown. Got: {text[:500]}"
            print("PASS: Question handling with mocked backend works")
    return True


@pytest.mark.asyncio
async def test_question_error_mocked():
    """Test question handling when backend returns error."""
    app = NL2SQLApp()
    mock_result = {
        "question": "test question",
        "sql": "SELECT 1",
        "columns": [],
        "rows": [],
        "error": "Connection refused",
    }
    async with app.run_test(size=(120, 40)) as pilot:
        with patch("app.agents.sql_agent.ask", new_callable=AsyncMock, return_value=mock_result):
            await type_and_submit(app, pilot, "test question")
            await asyncio.sleep(1.0)

            log = app.query_one("#message-log")
            text = get_richlog_text(log)
            assert "Error" in text or "error" in text or "错误" in text, f"Error message not shown. Got: {text[:500]}"
            print("PASS: Error handling works")
    return True


@pytest.mark.asyncio
async def test_sidebar_toggle():
    """Test sidebar toggle with Ctrl+H."""
    app = NL2SQLApp()
    async with app.run_test(size=(120, 40)) as pilot:
        sidebar = app.query_one("#sidebar")
        initial = sidebar.display
        await pilot.press("ctrl+h")
        await pilot.pause()
        assert sidebar.display != initial, "Sidebar did not toggle"
        await pilot.press("ctrl+h")
        await pilot.pause()
        assert sidebar.display == initial, "Sidebar did not toggle back"
        print("PASS: Sidebar toggle works")
    return True


@pytest.mark.asyncio
async def test_ctrl_l_clear():
    """Test Ctrl+L shortcut to clear messages."""
    app = NL2SQLApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await type_and_submit(app, pilot, "/help")
        await asyncio.sleep(0.1)

        log = app.query_one("#message-log")
        text_before = get_richlog_text(log)
        assert len(text_before.strip()) > 0, "No content before clear"

        await pilot.press("ctrl+l")
        await pilot.pause()

        text_after = get_richlog_text(log)
        assert len(text_after.strip()) == 0, f"Content not cleared. Got: {text_after[:200]}"
        print("PASS: Ctrl+L shortcut works")
    return True


@pytest.mark.asyncio
async def test_export_includes_history():
    """Test that export includes previously typed questions."""
    app = NL2SQLApp()
    mock_result = {
        "question": "count users",
        "sql": "SELECT COUNT(*) FROM users",
        "columns": ["count"],
        "rows": [[42]],
        "error": None,
    }
    export_file = "nl2sql_history.txt"
    if os.path.exists(export_file):
        os.remove(export_file)

    async with app.run_test(size=(120, 40)) as pilot:
        with patch("app.agents.sql_agent.ask", new_callable=AsyncMock, return_value=mock_result):
            await type_and_submit(app, pilot, "count users")
            await asyncio.sleep(1.0)

            await type_and_submit(app, pilot, "/export")
            await asyncio.sleep(0.5)

        assert os.path.exists(export_file), "Export file not created"
        content = open(export_file, "r", encoding="utf-8").read()
        assert "count users" in content, f"Export does not contain question. Content: {content[:200]}"
        print(f"PASS: Export includes history (content length: {len(content)})")
        if os.path.exists(export_file):
            os.remove(export_file)
    return True


async def main():
    tests = [
        ("App starts", test_app_starts),
        ("/help command", test_help_command),
        ("/clear command", test_clear_command),
        ("/export command", test_export_command),
        ("/config command", test_config_command),
        ("Unknown command", test_unknown_command),
        ("Empty input", test_empty_input),
        ("Question (mocked)", test_question_input_mocked),
        ("Error handling (mocked)", test_question_error_mocked),
        ("Sidebar toggle", test_sidebar_toggle),
        ("Ctrl+L clear", test_ctrl_l_clear),
        ("Export includes history", test_export_includes_history),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, test_fn in tests:
        try:
            result = await test_fn()
            if result:
                passed += 1
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"FAIL: {name}: {e}")

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    if errors:
        print("Failures:")
        for name, err in errors:
            print(f"  - {name}: {err}")
    print(f"{'='*50}")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
