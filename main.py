from agent.agent import app
from langchain_core.messages import HumanMessage
from agent.agent import model

if __name__ == "__main__":
    result = app.invoke(
        {"messages": [HumanMessage(content="Write a function that reverses a string and test it with 'hello world'.")]},
        config={
            "configurable": {
                "model": model
            }
        }
    )
    print(result["messages"][-1].content)
    