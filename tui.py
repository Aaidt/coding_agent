import os
from datetime import datetime
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.widgets import Footer, Input, Button, Static, Label, Markdown
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
        background: black;
    }
    
    #chat-pane {
        width: 1fr;
        height: 100%;
        border: none;
        padding: 1;
        background: transparent;
    }

    #control-pane {
        width: 1fr;
        height: 100%;
        border-left: solid rgba(255,255,255,0.2);
        padding: 1;
        background: transparent;
    }
    
    #chat-container {
        height: 1fr;
        overflow-y: auto;
        border: none;
        margin-bottom: 1;
        background: transparent;
    }

    #agent-logs {
        height: 1fr;
        overflow-y: auto;
        border: none;
        margin-top: 1;
        background: transparent;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        background: transparent;
        color: orange;
        padding: 1;
        margin-bottom: 1;
    }
    
    .message {
        margin: 1 0;
        width: 100%;
        height: auto;
    }
    .user-message {
        color: white;
        text-style: bold;
    }
    .agent-message {
        color: orange;
    }
    .tool-message {
        color: #888888;
    }
    
    #controls {
        height: auto;
        align: center middle;
    }
    
    #status {
        text-align: center;
        color: white;
        margin: 1;
    }

    Button {
        background: white;
        color: black;
        border: round;
        padding: 0 0;
        margin: 0 1;
    }
    
    Button:hover {
        color: white;
        background: orange;
        border: round;
    }

    Input {
        background: #111111;
        color: white;
        border: round;
        padding: 0 1;
        margin-top: 1;
    }
    Input:focus {
        border: round;
    }
    """

    current_thread_id = reactive("")

    def __init__(self):
        super().__init__()
        self.graph_app = None 

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="chat-pane"):
                yield Label("💬 Chat", classes="title")
                yield Vertical(id="chat-container")
                yield Input(placeholder="Ask OpenCode a programming task...", id="user_input")
                
            with Vertical(id="control-pane"):
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
                            # Use Markdown widget for better output rendering and legibility
                            chat_container.mount(Markdown(f"🤖 **Agent:**\n{msg.content}", classes="agent-message message"))
                            logs_container.mount(Label("Agent returned a response.", classes="message"))
                            chat_container.scroll_end()
                    elif "tools" in chunk:
                        tool_msg = chunk["tools"]["messages"][-1]
                        content_str = str(tool_msg.content)[:150]
                        logs_container.mount(Label(f"🔧 Tool Output ({tool_msg.name}): {content_str}...", classes="tool-message message"))
                        logs_container.scroll_end()
            
            except Exception as e:
                logs_container.mount(Label(f"❌ Error during execution: {e}", classes="message"))
                status.update("❌ Error occurred")
                return

            status.update("✅ Done thinking.")
            
            # Print state one more time at the end to ensure the user gets the final output if astream updates missed it
            # This fetches the final state payload directly from LangGraph
            try:
                final_state = await self.graph_app.aget_state(config)
                final_msg = final_state.values.get("messages", [])[-1]
                if "agent" not in chunk: # If the last chunk wasn't the agent message
                    chat_container.mount(Markdown(f"🤖 **Final Output:**\n{final_msg.content}", classes="agent-message message"))
            except Exception:
                pass

                chat_container.scroll_end()
            logs_container.scroll_end()

    def list_saved_chats(self):
        self.query_one("#status").update("Chats stored in local checkpoints.db")

if __name__ == "__main__":
    CodingAgentTUI().run()