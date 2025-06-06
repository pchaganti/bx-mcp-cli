# commands/test_help.py
import pytest
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from mcp_cli.commands.help import help_action
from mcp_cli.interactive.registry import InteractiveCommandRegistry
from mcp_cli.interactive.commands.help import HelpCommand


class DummyCmd:
    def __init__(self, name, help_text, aliases=None):
        self.name = name
        self.help = help_text
        self.aliases = aliases or []


@pytest.fixture(autouse=True)
def clear_registry():
    # Force type to dict in case any other test or code polluted it
    InteractiveCommandRegistry._commands = {}
    InteractiveCommandRegistry._aliases = {}
    yield
    InteractiveCommandRegistry._commands = {}
    InteractiveCommandRegistry._aliases = {}


def test_help_action_list_all(monkeypatch):
    # Register two dummy commands
    cmd_a = DummyCmd("a", "help A", aliases=["x"])
    cmd_b = DummyCmd("b", "help B", aliases=[])
    InteractiveCommandRegistry.register(cmd_a)
    InteractiveCommandRegistry.register(cmd_b)

    printed = []
    monkeypatch.setattr(Console, "print", lambda self, *args, **kw: printed.append(args[0]))

    console = Console()
    help_action(console=console)

    # Should have printed a Table of commands
    tables = [o for o in printed if isinstance(o, Table)]
    assert tables, f"No Table printed, got: {printed}"
    table = tables[0]
    # Check headers
    headers = [col.header for col in table.columns]
    assert headers == ["Command", "Aliases", "Description"]
    # Two rows
    assert table.row_count == 2

    # And a dim hint at the end (string)
    hints = [o for o in printed if isinstance(o, str) and "Type 'help &lt;command&gt;'" in o]
    assert hints, "Expected hint string at end"


def test_help_action_specific(monkeypatch):
    # Register one dummy command
    cmd = DummyCmd("foo", "Foo does X", aliases=["f"])
    InteractiveCommandRegistry.register(cmd)

    printed = []
    monkeypatch.setattr(Console, "print", lambda self, *args, **kw: printed.append(args[0]))

    console = Console()
    # Request help for command "foo"
    help_action("foo")

    # Should have printed a Panel
    panels = [o for o in printed if isinstance(o, Panel)]
    assert panels, f"No Panel printed, got: {printed}"
    panel = panels[0]

    # The Panel.renderable should be a Markdown instance
    from rich.markdown import Markdown
    assert isinstance(panel.renderable, Markdown)

    # Then aliases line (string) should follow
    alias_lines = [o for o in printed if isinstance(o, str) and "Aliases:" in o]
    assert alias_lines, "Expected an aliases line"


@pytest.mark.asyncio
async def test_interactive_wrapper(monkeypatch):
    # Register a no-op help command to satisfy registry in shell
    # (so that HelpCommand.execute() finds something)
    cmd_dummy = DummyCmd("foo", "help foo", aliases=[])
    InteractiveCommandRegistry.register(cmd_dummy)

    printed = []
    monkeypatch.setattr(Console, "print", lambda self, *args, **kw: printed.append(args[0]))

    help_cmd = HelpCommand()
    # call wrapper with no args → should call help_action(console, None)
    await help_cmd.execute([], tool_manager=None)
    # we should see at least one Table
    assert any(isinstance(o, Table) for o in printed)

    printed.clear()
    # call wrapper with specific arg → get Panel
    await help_cmd.execute(["foo"], tool_manager=None)
    assert any(isinstance(o, Panel) for o in printed)
