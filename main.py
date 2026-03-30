from agent.agent import app
from langchain_core.messages import HumanMessage
from agent.agent import model

if __name__ == "__main__":
    print("🤖 Coding Agent Ready! (Type 'exit' to stop)\n")

    while True:
        print("\n" + "="*50)
        print("1. New Chat (start fresh thread)")
        print("2. List saved chats")
        print("3. Exit")
        choice = input("\nChoose (1/2/3): ").strip()
        if choice == "3":
            print("👋 Goodbye!")
            break

        if choice == "1":
            # Start a brand new thread
            thread_id = f"chat-{os.urandom(4).hex()}"   # random unique id
            print(f"\n🆕 Starting NEW chat → {thread_id}")
        
        elif choice == "2":
            # List all saved threads (simple way)
            print("\nSaved chats:")
            # We can list them from the database later if you want fancy names
            # For now we show raw thread_ids
            print("→ Checkpoints are saved in 'checkpoints.db'")
            thread_id = input("Paste thread_id to resume (or press Enter for new): ").strip()
            if not thread_id:
                thread_id = f"chat-{os.urandom(4).hex()}"
                print(f"Starting new chat → {thread_id}")
        else:
            continue

        print(f"📌 Using thread: {thread_id}\n")
        print("Type your request. Type 'exit' to go back to menu.\n")

        while True:
            user_query = input("You: ").strip()
            
            if user_query.lower() in ["exit", "quit", "back"]:
                break
            if not user_query:
                continue

            print("\nThinking...\n")

            # STREAM MODE → shows reasoning live!
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "model": llm
                }
            }

            # This is the key part for seeing reasoning
            for event in coding_agent.stream(
                {"messages": [HumanMessage(content=user_query)]},
                config,
                stream_mode="updates"   # shows every node update
            ):
                # Print whatever the agent does
                if "agent" in event:
                    msg = event["agent"]["messages"][-1]
                    if msg.content:
                        print(f"🧠 Agent thought: {msg.content}")
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"🔧 Calling tool: {tc['name']}({tc['args']})")
            
                elif "tools" in event:
                    tool_output = event["tools"]["messages"][-1]
                    print(f"🛠️  Tool result: {tool_output.content[:500]}...")

            # Print final answer cleanly
            final_state = coding_agent.get_state(config)
            final_msg = final_state.values["messages"][-1]
            print(f"\n✅ Final Answer:\n{final_msg.content}\n")