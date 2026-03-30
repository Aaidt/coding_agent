import os
from datetime import datetime
from dotenv import load_dotenv

from textual.app import App, ComposeResult
from textual.widgets import Input, Label
from textual.containers import Vertical
from textual.reactive import reactive

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.agent import graph_builder

load_dotenv()


class OpenCodeTUI(App):
    CSS = """
    Screen {
        background: black;
    }

    #terminal {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }

    #input {
        dock: bottom;
        border: none;
        background: #111;
        color: white;
    }

    .line-user { color: white; }
    .line-agent { color: orange; }
    .line-tool { color: #888; }
    .line-system { color: #666; }
    """

    thread_id = reactive("")

    def compose(self) -> ComposeResult:
        yield Vertical(id="terminal")
        yield Input(placeholder="› Enter task...", id="input")

    def on_mount(self):
        self.thread_id = f"chat-{datetime.now().timestamp()}"
        self.write("OpenCode Agent")
        self.write("Type a task or /new")

    def write(self, text: str, cls="line-system"):
        terminal = self.query_one("#terminal")
        terminal.mount(Label(text, classes=cls))
        terminal.scroll_end()

    def handle_command(self, text: str) -> bool:
        if text == "/new":
            self.thread_id = f"chat-{datetime.now().timestamp()}"
            self.write(f"[new session: {self.thread_id}]")
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

        self.write(f"› {text}", "line-user")

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
                            self.write(msg.content, "line-agent")

                    elif "tools" in chunk:
                        tool = chunk["tools"]["messages"][-1]
                        self.write(
                            f"[tool:{tool.name}] {str(tool.content)[:120]}",
                            "line-tool"
                        )

            except Exception as e:
                self.write(f"[error] {e}", "line-system")


if __name__ == "__main__":
    OpenCodeTUI().run()