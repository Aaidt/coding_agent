import os
from datetime import datetime
from dotenv import load_dotenv

from textual.app import App, ComposeResult
from textual.widgets import Input, Static
from textual.containers import Vertical
from textual.reactive import reactive

from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich import box

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.agent import graph_builder

load_dotenv()


class OpenCodeTUI(App):
    CSS = """
    Screen {
        background: transparent;
    }

    #terminal {
        height: 1fr;
        overflow-y: auto;
        scrollbar-size: 0 0;
        padding: 1 2;
    }

    #input {
        dock: bottom;
        border: none;
        background: transparent;
        color: white;
        padding: 0 1;
    }

    .line-user { 
        margin: 1 0 0 10;
        content-align: right middle;
    }
    .line-agent { 
        margin: 1 10 0 0;
    }
    .line-tool { 
        margin: 0 10 0 5;
    }
    .line-system { 
        margin: 1 0;
        content-align: center middle;
    }
    """

    thread_id = reactive("")

    def compose(self) -> ComposeResult:
        yield Vertical(id="terminal")
        yield Input(placeholder="› Enter task...", id="input")

    def on_mount(self):
        self.thread_id = f"chat-{datetime.now().timestamp()}"
        self.write(Text("🤖 OpenCode Agent", justify="center", style="bold magenta"))
        self.write(Text("Type a task or /new", justify="center", style="dim"))

    def write(self, renderable: RenderableType, cls="line-system"):
        terminal = self.query_one("#terminal")
        terminal.mount(Static(renderable, classes=cls))
        terminal.scroll_end(animate=False)

    def handle_command(self, text: str) -> bool:
        if text == "/new":
            self.thread_id = f"chat-{datetime.now().timestamp()}"
            self.write(Text(f"[new session: {self.thread_id}]", justify="center", style="bold green"))
            return True
        elif text == "/exit":
            self.exit()
            return True
        return False

    async def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        if not text:
            return

        event.input.clear()

        if self.handle_command(text):
            return

        self.write(Panel(Text(text, justify="right", style="cyan"), box=box.ROUNDED, title="[cyan]You", title_align="right", border_style="cyan"), "line-user")

        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as cp:
            app = graph_builder().compile(checkpointer=cp)

            config = {
                "configurable": {
                    "thread_id": self.thread_id
                }
            }

            try:
                async for chunk in app.astream(
                    {"messages": [HumanMessage(content=text)]},
                    config,
                    stream_mode="updates"
                ):
                    if "agent" in chunk:
                        msg = chunk["agent"]["messages"][-1]
                        if msg.content:
                            self.write(Panel(Markdown(msg.content), box=box.ROUNDED, title="[orange1]Agent", title_align="left", border_style="orange1"), "line-agent")

                    elif "tools" in chunk:
                        tool = chunk["tools"]["messages"][-1]
                        tool_content = str(tool.content)[:200]
                        if len(str(tool.content)) > 200:
                            tool_content += "..."
                        self.write(
                            Panel(Text(tool_content, style="dim"), box=box.ROUNDED, title=f"[dim]Tool: {tool.name}", title_align="left", border_style="dim"),
                            "line-tool"
                        )

            except Exception as e:
                self.write(Panel(Text(f"[error] {e}", style="red"), box=box.ROUNDED, title="[red]System Error", border_style="red"), "line-system")


if __name__ == "__main__":
    OpenCodeTUI().run()