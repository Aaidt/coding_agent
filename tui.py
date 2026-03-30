import os
from datetime import datetime
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, Static, Label
from textual.containers import Vertical, Horizontal, Container
from textual.reactive import reactive
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.agent import graph_builder 

load_dotenv()

class CodingAgentTUI(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #left-pane {
        width: 1fr;
        height: 100%;
        border: solid $secondary;
        padding: 1;
    }

    #right-pane {
        width: 1fr;
        height: 100%;
        border: solid $accent;
        padding: 1;
    }
    
    #chat-container {
        height: 1fr;
        overflow-y: auto;
        border: round $primary;
        margin-bottom: 1;
    }

    #agent-logs {
        height: 1fr;
        overflow-y: auto;
        border: dashed $warning;
        margin-top: 1;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        background: $boost;
        padding: 1;
        margin-bottom: 1;
    }
    
    .message {
        margin: 1 0;
    }
    .user-message {
        color: $success;
    }
    .agent-message {
        color: $primary;
    }
    .tool-message {
        color: $warning;
    }
    
    #controls {
        height: auto;
        align:center middle;
    }
    
    #status {
        text-align: center;
        color: $text-muted;
        margin: 1;
    }
    """

    title = "OpenCode TUI mode"
    current_thread_id = reactive("")

    def __init__(self):
        super().__init__()
        self.graph_app = None 

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            # Left side for Chat
            with Vertical(id="left-pane"):
                yield Label("💬 Chat", classes="title")
                yield Vertical(id="chat-container")
                yield Input(placeholder="Ask OpenCode a programming task...", id="user_input")
                
            # Right side for Controls & Logs
            with Vertical(id="right-pane"):
                yield Label("⚙️ Control Panel", classes="title")
                with Horizontal(id="controls"):
                    yield Button("New Chat", id="new_chat", variant="primary")
                    yield Button("Save/List", id="list_chats")
                    yield Button("Quit", id="quit", variant="error")
                
                yield Static("Status: Ready", id="status")
                yield Label("📜 Agent Logs & Tools Activity", classes="title")
                yield Vertical(id="agent-logs")
                
        yield Footer()

    def on_mount(self):
        self.query_one("#chat-container").mount(Label("No active session. Start a new chat.", classes="message"))

    def on_button_pressed(self, event):
        if event.button.id == "new_chat":
            self.start_new_chat()
        elif event.button.id == "list_chats":
            self.list_saved_chats()
        elif event.button.id == "quit":
            self.exit()

    def start_new_chat(self):
        self.current_thread_id = f"chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.query_one("#status").update(f"Session Active: {self.current_thread_id}")
        
        chat_container = self.query_one("#chat-container")
        chat_container.remove_children()
        
        logs_container = self.query_one("#agent-logs")
        logs_container.remove_children()
        logs_container.mount(Label(f"Started trace for thread {self.current_thread_id}", classes="message"))

    async def on_input_submitted(self, event: Input.Submitted):
        if not self.current_thread_id:
            self.query_one("#status").update("❌ Please click 'New Chat' first!")
            return

        user_text = event.value.strip()
        if not user_text:
            return

        chat_container = self.query_one("#chat-container")
        chat_container.mount(Label(f"🧑 You: {user_text}", classes="user-message message"))
        
        event.input.clear()

        # Fix here: Added () to graph_builder to call it properly
        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
            self.graph_app = graph_builder().compile(checkpointer=checkpointer)

            config = {
                "configurable": {
                    "thread_id": self.current_thread_id
                }
            }

            status = self.query_one("#status")
            status.update("🤔 Agent is thinking...")

            logs_container = self.query_one("#agent-logs")

            try:
                # Handle async updates stream from LangGraph
                async for chunk in self.graph_app.astream(
                    {"messages": [HumanMessage(content=user_text)]},
                    config,
                    stream_mode="updates"
                ):            
                    if "agent" in chunk:
                        msg = chunk["agent"]["messages"][-1]
                        if msg.content:
                            chat_container.mount(Label(f"🤖 Agent: {msg.content}", classes="agent-message message"))
                            logs_container.mount(Label("Agent returned a response.", classes="message"))
                            chat_container.scroll_end()
                    elif "tools" in chunk:
                        tool_msg = chunk["tools"]["messages"][-1]
                        # Handling the tool call attribute format correctly
                        # Sometimes tool content can be a string, sometimes empty if multiple things failed
                        content_str = str(tool_msg.content)[:150]
                        logs_container.mount(Label(f"🔧 Tool Output ({tool_msg.name}): {content_str}...", classes="tool-message message"))
                        logs_container.scroll_end()
            
            except Exception as e:
                logs_container.mount(Label(f"❌ Error during execution: {e}", classes="message"))
                status.update("❌ Error occurred")
                return

            status.update("✅ Done thinking.")
            chat_container.scroll_end()
            logs_container.scroll_end()

    def list_saved_chats(self):
        self.query_one("#status").update("Chats stored in local checkpoints.db")

if __name__ == "__main__":
    CodingAgentTUI().run()