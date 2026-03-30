# coding_agent

## Actions

- [ ] write_file
- [ ] read_file
- [ ] run_code
- [ ] list_files
- [ ] search_web
- [ ] think
- [ ] tool_call

## Steps

- [ ] Take user query
- [ ] Send to LLM
- [ ] Get response and parse CODE/PLAN/THOUGHTS
- [ ] Act on response

---

## Todos

**Todo 1: Context Management**
Our agent re-sends everything each iteration. Add summarization: after N iterations, compress the conversation history. Compare token usage before/after.

**Todo 2: Planning Step**
Modify the agent to first create a PLAN (list of steps), then execute each one. Compare Plan→Execute vs pure ReAct on the same task.

**Todo 3: Multi-Agent**
Create a 'researcher' (Wikipedia tools) and a 'coder' (file/code tools). Build an orchestrator that routes subtasks to the right agent.

**Todo 4: Web Browsing**
Add a `fetch_webpage(url)` tool. The agent can now follow links. What new failure modes appear?
