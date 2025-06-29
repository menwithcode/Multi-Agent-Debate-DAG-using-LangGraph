# Multi-Agent Structured Debate Pipeline

This project implements a **multi-agent structured debate workflow** using **OpenAI SDK with Together API**, Mixtral-8x7B-Instruct, and a **Node-based DAG architecture** to simulate debates between two agents with a judge for structured summaries.

---

## Features

✅ Node-based architecture (UserInput, AgentA, AgentB, Memory, Judge).  
✅ Partial memory context window for each agent (last 2 rounds).  
✅ Explicit state validation on each transition.  
✅ Full structured logs with timestamp per step (`debate_log.jsonl`).  
✅ Generates clean `debate_summary.txt` and `debate_log.txt`.  
✅ Generates `debate_dag.png` for visual reference of the pipeline.

---

## Requirements

- Python 3.8+
- Dependencies:
  - `openai`
  - `rich`
  - `graphviz`

Install via:
```bash
pip install openai rich graphviz
