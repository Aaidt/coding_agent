from agent.agent import app
from langchain_core.messages import HumanMessage
from agent.agent import model

if __name__ == "__main__":
    print("Coding Agent Ready! (Type 'exit' to stop)\n")

    while True:
        user_input = input("User: ").strip()
        if user_input.lower() == "exit":
            break
        if not user_input:
            continue

        print("Thinking...\n")

        result = app.invoke(
            {"messages": [HumanMessage(content=user_input)]}
        )
        print(result["messages"][-1].content)
        print("\n" + "=" * 60 + "\n")
