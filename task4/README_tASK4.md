# Task 3: Advanced Reasoning Lab
## Multi-Strategy Reasoning Evaluation System

This task implements an evaluation system for three mainstream LLM reasoning strategies, including ReAct, Plan-and-Execute and Self-Consistency. It runs tests on math problems, calculates evaluation metrics and supports trace replay.

### Implemented Reasoning Strategies
1. **ReAct**
Alternates between thinking steps and tool invocation to solve problems interactively.
2. **Plan-and-Execute**
Divides the workflow into a planning phase and a separate execution phase.
3. **Self-Consistency**
Generates multiple reasoning paths and selects the most frequent answer via majority voting.

### Core Components
- Shared calculator tool for mathematical computation
- Unified abstract base class for all reasoning strategies
- 25 GSM8K-style math test cases
- Exact match accuracy & Wilson 95% confidence interval
- Pairwise win/loss comparison matrix
- Results export to JSON and JSONL files
- Trace replay function for inspection

### How to Run
python task3/reasoning_system.py

### Example Output
===== Evaluation Results =====
ReAct               | acc=0.84 | 95%CI=[0.644,0.939]
Plan-and-Execute    | acc=0.8 | 95%CI=[0.59,0.916]
Self-Consistency    | acc=0.88 | 95%CI=[0.69,0.961]

===== Win Matrix =====
ReAct               | —  W  L
Plan-and-Execute    | L  —  L
Self-Consistency    | W  W  —

===== Replay: q0 =====
{
  "problem_id": "q0",
  "strategy": "ReAct",
  "steps": [
    {
      "step": "think",
      "content": "I need to compute 20 + 27"
    },
    {
      "step": "act",
      "content": "calculate(20+27)"
    },
    {
      "step": "observe",
      "content": "47"
    }
  ],
  "final_answer": "47",
  "correct": true,
  "tokens_in": 190,
  "tokens_out": 75,
  "latency": 0.001,
  "timestamp": 1718900000.123
}
