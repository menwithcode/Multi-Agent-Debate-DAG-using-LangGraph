# -*- coding: utf-8 -*-
"""main task 3.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/12HFzBepw-BxQgMrShsh3sjGrkJvuTAdu
"""

!pip install openai rich graphviz

# !pip install openai rich graphviz

from openai import OpenAI
from graphviz import Digraph
from rich.console import Console
import os
import json
from datetime import datetime

# Initialize Together API via OpenAI SDK
client = OpenAI(
    api_key="aa42e00c41af9a363a8d90cd31bf790055cd4f3a2bd2fb053e56135aab351753",
    base_url="https://api.together.xyz/v1"
)

console = Console()

# -------------------- Logger -------------------- #
LOG_FILE_NAME = "debate_log.jsonl"


def log_transition(node_name, state, message=None):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "node": node_name,
        "state_snapshot": {
            "topic": state.get("topic"),
            "agent_a_profession": state.get("agent_a_profession"),
            "agent_b_profession": state.get("agent_b_profession"),
            "round": state.get("round"),
            "previous_b": state.get("previous_b"),
            "memory_count": len(state.get("memory", []))
        },
        "message": message
    }
    with open(LOG_FILE_NAME, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

# -------------------- Explicit State Validation -------------------- #
def validate_state(state, current_node):
    required_keys = ['topic', 'agent_a_profession', 'agent_b_profession', 'memory', 'round', 'previous_b']
    for key in required_keys:
        if key not in state:
            raise ValueError(f"[State Validation] Missing required key: {key} in state during {current_node}")
    if not isinstance(state['memory'], list):
        raise TypeError(f"[State Validation] 'memory' should be a list, got {type(state['memory'])} during {current_node}")
    if not isinstance(state['round'], int) or state['round'] < 1:
        raise ValueError(f"[State Validation] 'round' should be a positive integer, got {state['round']} during {current_node}")
    if state['round'] > 8 and current_node != 'judge':
        raise ValueError(f"[State Validation] Round exceeded maximum limit before Judge Node during {current_node}")
    # Silent validation

# -------------------- Node Base -------------------- #
class Node:
    def __init__(self, name):
        self.name = name

    def run(self, state):
        raise NotImplementedError

# -------------------- Nodes -------------------- #
class UserInputNode(Node):
    def run(self, state):
        topic = input("Enter topic for debate: ")
        agent_a_profession = input("Enter profession for Agent A (e.g., Scientist): ")
        agent_b_profession = input("Enter profession for Agent B (e.g., Philosopher): ")

        state['topic'] = topic
        state['agent_a_profession'] = agent_a_profession
        state['agent_b_profession'] = agent_b_profession
        state['memory'] = []
        state['round'] = 1
        state['previous_b'] = ""

        console.print(f"\n[bold green]Debate Topic:[/bold green] {topic}")
        console.print(f"[bold green]Agent A Profession:[/bold green] {agent_a_profession}")
        console.print(f"[bold green]Agent B Profession:[/bold green] {agent_b_profession}\n")
        log_transition(self.name, state, "Initialized debate state with user input.")
        return state

class AgentANode(Node):
    def run(self, state):
        context_rounds = state['memory'][-2:] if len(state['memory']) >= 2 else state['memory']
        transcript = "\n".join([
            f"Round {len(state['memory']) - len(context_rounds) + idx + 1}:\n{state['agent_a_profession']}: {a}\n{state['agent_b_profession']}: {b}"
            for idx, (a, b) in enumerate(context_rounds)
        ]) if context_rounds else "None yet."

        prompt = f"""
You are a {state['agent_a_profession']} participating in a structured debate on: "{state['topic']}".
Round {state['round']}.

Here is the transcript of previous relevant rounds:
{transcript}

Instructions:
- Carefully read all previous arguments by both yourself and your opponent before responding.
- Do not repeat any points or arguments already made in earlier rounds.
- Do not contradict any points that have been accepted by both parties in previous rounds.
- Do not claim that your own previous arguments were wrong.
- If a point has already been agreed upon, add new supporting evidence, examples, or additional relevant perspectives to deepen the discussion.
- Only introduce new, relevant angles if they add value to the debate and align with your professional perspective.
- Keep your argument clear, logical, and directly tied to the topic.
- Write 3-5 sentences maximum.
- Do not include references, citations, or source lists in your response.
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        ).choices[0].message.content.strip()

        console.print(f"[bold red]{state['agent_a_profession']}:[/bold red ] {response}\n")
        state['current_a'] = response
        log_transition(self.name, state, f"{state['agent_a_profession']} responded.")
        return state

class AgentBNode(Node):
    def run(self, state):
        context_rounds = state['memory'][-2:] if len(state['memory']) >= 2 else state['memory']
        transcript = "\n".join([
            f"Round {len(state['memory']) - len(context_rounds) + idx + 1}:\n{state['agent_a_profession']}: {a}\n{state['agent_b_profession']}: {b}"
            for idx, (a, b) in enumerate(context_rounds)
        ]) if context_rounds else "None yet."

        prompt = f"""
You are a {state['agent_b_profession']} debating on: "{state['topic']}".
Round {state['round']}.
{state['agent_a_profession']} said: "{state['current_a']}"

Here is the transcript of previous relevant rounds:
{transcript}

Instructions:
- Carefully read all previous arguments by both yourself and your opponent before responding.
- Do not repeat any points or arguments already made in earlier rounds.
- Do not contradict any points that have been accepted by both parties in previous rounds.
- Do not claim that your own previous arguments were wrong.
- If a point has already been agreed upon, add new supporting evidence, examples, or additional relevant perspectives to deepen the discussion.
- Only introduce new, relevant angles if they add value to the debate and align with your professional perspective.
- Keep your argument clear, logical, and directly tied to the topic.
- Write 3-5 sentences maximum.
- Do not include references, citations, or source lists in your response.
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        ).choices[0].message.content.strip()

        console.print(f"[bold magenta]{state['agent_b_profession']}:[/bold magenta] {response}\n")
        state['current_b'] = response
        state['previous_b'] = response
        log_transition(self.name, state, f"{state['agent_b_profession']} responded.")
        return state

class MemoryNode(Node):
    def run(self, state):
        state['memory'].append((state['current_a'], state['current_b']))
        state['round'] += 1
        log_transition(self.name, state, "Memory updated with current round's conversation.")
        return state

class JudgeNode(Node):
    def run(self, state):
        transcript = "\n".join([
            f"Round {i+1}:\n{state['agent_a_profession']}: {a}\n{state['agent_b_profession']}: {b}\n"
            for i, (a, b) in enumerate(state['memory'])
        ])
        prompt = f"""
You are an impartial debate judge.
Topic: "{state['topic']}"

Debate transcript:
{transcript}

Instructions:
- Summarize each round in 1-2 lines.
- Decide the winner between ({state['agent_a_profession']} or {state['agent_b_profession']}) with a clear, logical reason.
- Do not include references, citations, or source lists in your response.
- Return the result in the following format:
Summary:
...
Winner: <winner name only>
Reason: <short reason why the winner won>
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        ).choices[0].message.content.strip()

        console.print(f"\n[bold yellow]Judge Summary:[/bold yellow]\n{response}\n")
        with open("debate_summary.txt", "w") as f:
            f.write(response)
        with open("debate_log.txt", "w") as f:
            f.write(transcript)
        log_transition(self.name, state, "Judge provided summary and decision.")
        print("\nLogs saved as debate_summary.txt and debate_log.txt")
        return state

# -------------------- DAG Engine with Validation -------------------- #
# Maps string identifiers to node instances for your finite state machine workflow.
nodes = {
    'user_input': UserInputNode('user_input'),
    'agent_a': AgentANode('agent_a'),
    'agent_b': AgentBNode('agent_b'),
    'memory': MemoryNode('memory'),
    'judge': JudgeNode('judge')
}
# initializes the starting node and empty state.
current = 'user_input'
state = {}
# Runs state validation before and after each node except user_input
while True:
    if current != 'user_input':
        validate_state(state, current)

    state = nodes[current].run(state)

    if current != 'user_input':
        validate_state(state, current)

    if current == 'user_input':
        current = 'agent_a'
    elif current == 'agent_a':
        current = 'agent_b'
    elif current == 'agent_b':
        current = 'memory'
    elif current == 'memory':
        if state['round'] > 4:
            current = 'judge'
        else:
            current = 'agent_a'
    elif current == 'judge':
        break

# -------------------- DAG Visualization -------------------- #
dot = Digraph(comment='Debate DAG', format='png')
dot.attr(rankdir='LR')
dot.node('User', 'User Input')
dot.node('AgentA', 'Agent A')
dot.node('AgentB', 'Agent B')
dot.node('Memory', 'Memory Node')
dot.node('Judge', 'Judge')
dot.edge('User', 'AgentA')
dot.edge('AgentA', 'AgentB')
dot.edge('AgentB', 'Memory')
dot.edge('Memory', 'AgentA')
dot.edge('AgentA', 'Judge')
dot.render('debate_dag', cleanup=True)
print("DAG diagram saved as debate_dag.png")

