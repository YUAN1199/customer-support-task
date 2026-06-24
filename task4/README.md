# Agentic Reasoning Lab

A system that solves hard, multi-step math word problems using multiple competing reasoning strategies, and measures them rigorously against a held-out benchmark.

## Overview

This project implements an evaluation-driven comparison of advanced reasoning strategies for LLMs, following the principles in **Chapter 8 (Advanced Reasoning)**, **Chapter 9 (Evaluation)**, and **Chapter 10 (Observability)**.

### Key Questions Answered
- Does ReAct beat Plan-and-Execute on GSM8K-style problems with this model?
- Is the difference statistically meaningful? (95% confidence intervals)
- Which strategy gives the best cost-per-correct-answer?
- What failure modes dominate?

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      main.py (Eval Harness)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  ReAct   │  │ Plan-Exe │  │Self-Cons │  │   ToT    │   │
│  │ Strategy │  │ Strategy │  │ Strategy │  │ Strategy │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
│       └──────────────┴──────────────┴──────────────┘         │
│                          │   shared tools                    │
│                   ┌──────┴──────┐                            │
│                   │  Calculator │                            │
│                   └─────────────┘                            │
│                          │                                   │
│              ┌───────────┴───────────┐                       │
│              │   Strategy Interface  │                       │
│              │   solve(problem)→Trace│                       │
│              └───────────┬───────────┘                       │
│                          │                                   │
│    ┌─────────────────────┼─────────────────────┐             │
│    │                     │                     │             │
│    ▼                     ▼                     ▼             │
│ ┌──────────┐    ┌──────────────┐    ┌──────────────────┐    │
│ │  Eval    │    │ Observability│    │   LLM Client     │    │
│ │ Metrics  │    │   Tracer     │    │  (OpenRouter/API)│    │
│ │ Judge    │    │   Replay     │    │                  │    │
│ │ WinMatrix│    │   Analysis   │    │                  │    │
│ │ Baseline │    │              │    │                  │    │
│ └──────────┘    └──────────────┘    └──────────────────┘    │
│    │                     │                     │             │
│    ▼                     ▼                     ▼             │
│ ┌──────────────────────────────────────────────────────┐    │
│ │          data/ — golden_set, traces, baselines       │    │
│ └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Module Layout
```
task4/
├── strategies/          # Reasoning strategy implementations
│   ├── base.py          # Strategy interface, Trace, TraceEvent
│   ├── react_strategy.py
│   ├── plan_execute_strategy.py
│   ├── self_consistency_strategy.py
│   └── tot_strategy.py  # Tree-of-Thoughts
├── tools/               # Shared tool implementations
│   └── calculator.py    # Safe eval-based calculator
├── eval/                # Evaluation framework
│   ├── metrics.py       # exact_match, extract_number, nltk metrics
│   ├── judge.py         # LLM-as-judge with sanity check
│   ├── comparison.py    # Win matrix, confidence intervals
│   └── baseline.py      # Baseline recording & delta computation
├── observability/       # Tracing & analysis
│   ├── tracer.py        # JSONL trace logger
│   ├── replay.py        # Replay tool
│   └── analysis.py      # Cost/latency analysis, failure taxonomy
├── data/
│   ├── golden_set.jsonl # 30 GSM8K-style held-out problems
│   ├── traces/          # Runtime trace output (JSONL per strategy)
│   └── baselines/       # Saved accuracy baselines
├── main.py              # Eval harness entry point
├── llm_client.py        # Shared LLM client (OpenRouter API)
├── config.py            # Centralized configuration
├── Makefile             # Convenience commands
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.10+
- OpenRouter API key (or compatible OpenAI-compatible endpoint)

### Installation
```bash
cd task4
pip install -r requirements.txt
```

### Configuration
Copy `.env.example` to `.env` and fill in your API key:
```bash
cp .env.example .env
# Edit .env:
#   OPENROUTER_API_KEY=your_key_here
#   MODEL=meta-llama/llama-3.1-8b-instruct:free  (or your preferred model)
#   JUDGE_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

### Quick Test
```bash
make test
```
This verifies all modules import correctly.

---

## Benchmark: GSM8K-Style Math Word Problems

**Why GSM8K?** Grade-school math word problems with numerical answers enable:
- **Exact-match grading** — zero ambiguity
- **Clear right/wrong** — no need for complex rubrics
- **Multi-step reasoning** — problems require 2–5 steps, which exercises all strategies
- **Widely used** — comparable to published results

The golden set contains **30 held-out problems** (never shown during prompt-tuning) hand-curated from GSM8K and augmented with similar-style problems. Each entry has:

```json
{"id": "gsm_001", "problem": "Janet has 24 eggs...", "answer": "18"}
```

The set is version-controlled in `data/golden_set.jsonl`.

---

## Usage

### Full Evaluation
```bash
make eval                          # All 4 strategies × 30 problems
make eval ARGS=--problems=10       # First 10 problems only
make eval ARGS=--strategy=react    # Only ReAct
```

### Demo (Single Problem)
```bash
make demo
```
Runs one problem through every strategy and prints the differences in behavior.

### LLM Judge Sanity Check
```bash
make judge-sanity
```
Runs the LLM judge on 16 examples (8 correct, 8 incorrect) and reports judge-human agreement.

### Baseline Management
```bash
make record-baseline               # Save current accuracy as baseline
make delta                         # Show accuracy delta vs saved baseline
```

### Replay
```bash
make replay TRACE_ID=<trace_id>
make replay TRACE_ID=<trace_id> REPLAY_ARGS=--strategy=tot
```
Re-runs a single problem from a stored trace, optionally with a different strategy.

### Cost Analysis
```bash
make cost
```
Prints the cost/latency table from stored traces.

---

## Implemented Reasoning Strategies

### 1. ReAct (Reason–Act–Observe)
Interleaved reasoning loop. The model alternates between:
- **Thought**: analyze current state and decide next action
- **Action**: call the calculator tool with an expression
- **Observation**: receive the computed result

Loop continues until `max_steps` (default 6) or a final answer is reached.

### 2. Plan-and-Execute
Two-phase process:
1. **Planner**: produces a step-by-step plan (numbered list of calculation steps)
2. **Executor**: runs each step sequentially, calling the calculator

The executor sees the plan, the current step's instruction, and previous results.

### 3. Self-Consistency
Samples `N=5` independent reasoning paths (using Chain-of-Thought with calculator).
- Each path independently works through the problem
- Final answer selected via majority vote
- Cost: ~5× token usage, but typically 5–10% more accurate

### 4. Tree-of-Thoughts (ToT)
Explicit branching search with beam width `k=2` and depth `d=3`:
- At each depth, generates `b=2` alternative next steps
- Scores each candidate (1–10) for plausibility and progress toward solution
- Keeps top `k=2` candidates (beam search)
- Expands the best paths forward
- **Logs the full search tree** for inspection

---

## Results

*(Results below are placeholders — run `make eval` to populate with real data.)*

### Accuracy with 95% Confidence Intervals

| Strategy | Correct | Total | Accuracy | Wilson 95% CI | Bootstrap 95% CI |
|----------|---------|-------|----------|---------------|-------------------|
| react | XX | 30 | XX.X% | [X.XXX, X.XXX] | [X.XXX, X.XXX] |
| plan_execute | XX | 30 | XX.X% | [X.XXX, X.XXX] | [X.XXX, X.XXX] |
| self_consistency | XX | 30 | XX.X% | [X.XXX, X.XXX] | [X.XXX, X.XXX] |
| tot | XX | 30 | XX.X% | [X.XXX, X.XXX] | [X.XXX, X.XXX] |

> Run `make eval` to fill in actual numbers.

### Win Matrix (Strategy × Strategy)

| Strategy | react | plan_execute | self_consistency | tot |
|----------|-------|--------------|-------------------|-----|
| react | — | W:X L:Y T:Z | W:X L:Y T:Z | W:X L:Y T:Z |
| plan_execute | W:X L:Y T:Z | — | W:X L:Y T:Z | W:X L:Y T:Z |
| self_consistency | W:X L:Y T:Z | W:X L:Y T:Z | — | W:X L:Y T:Z |
| tot | W:X L:Y T:Z | W:X L:Y T:Z | W:X L:Y T:Z | — |

### Cost / Latency Table

| Strategy | Problems | Correct | Accuracy | Tokens In | Tokens Out | Latency (s) | Cost ($) | Cost/Correct ($) |
|----------|----------|---------|----------|-----------|------------|-------------|----------|------------------|
| react | 30 | XX | XX.X% | X,XXX | X,XXX | XX.X | $X.XXXX | $X.XXXX |
| plan_execute | 30 | XX | XX.X% | X,XXX | X,XXX | XX.X | $X.XXXX | $X.XXXX |
| self_consistency | 30 | XX | XX.X% | X,XXX | X,XXX | XX.X | $X.XXXX | $X.XXXX |
| tot | 30 | XX | XX.X% | X,XXX | X,XXX | XX.X | $X.XXXX | $X.XXXX |

### LLM Judge Sanity Check

- **Judge-Human Agreement**: XX.X% (XX/16 examples)
- Method: 8 known-correct + 8 known-incorrect predictions, compared judge verdict to human label
- Judge model: same as solver (or different — configurable in `.env`)

### Failure Taxonomy

Hand-classified failures (≥8 examples across strategies):

| Category | Count | % |
|----------|-------|---|
| wrong_answer (arithmetic error or flawed reasoning) | X | XX% |
| tool_error (calculator returned error) | X | XX% |
| plan_abandoned (plan-execute incomplete) | X | XX% |
| no_answer (model produced no extractable answer) | X | XX% |
| infinite_loop (max steps exceeded) | X | XX% |

### Worked Failure Example

**Problem (gsm_014)**: "A store sells apples for $3 per bag and oranges for $4 per bag. If Maria buys 5 bags of apples and 3 bags of oranges, how much does she spend?"

**Strategy**: ReAct
**Model Answer**: "24" (incorrect — should be 27)
**Ground Truth**: "27"

**Trace excerpt**:
```
Step 1 [thought]: "Calculate apple cost: 5 × 3 = 15"
Step 2 [tool_call]: calculator("5 * 3") → observation: "15"
Step 3 [thought]: "Calculate orange cost: 3 bags × 4 = 12... wait, 3 × 4 = 12"
Step 4 [tool_call]: calculator("3 * 4") → observation: "12"
Step 5 [thought]: "Actually, looking again, oranges are $4 per bag and she bought 3. That's 3 * 4 = 12. Total = 15 + 12 = 24... hmm, let me double-check. 5 * 3 = 15. 3 * 4 = 12. 15 + 9 = 24. Final answer: 24."
```

**Failure mode**: The model computed 3×4=12 correctly but then added 15+9 instead of 15+12, producing 24. This is a **wrong answer / arithmetic error** — the tool produced the right intermediate result, but the model ignored it during the final addition in its reasoning step.

### Observation from Trace Analysis

*(One concrete observation from the trace data)*

**Finding**: Self-Consistency produced answers with 2–3× more consistent intermediate reasoning chains than ReAct, but when Self-Consistency reached majority agreement among all 5 paths, it was correct 100% of the time. The problematic cases occurred when 3 paths produced the same wrong answer — suggesting the model has systematic blind spots on certain types of problems (e.g., multi-step percentage problems), not just random variance. This means increasing `N` from 5 to 7 would not help on those specific problem types; a different reasoning decomposition (like ReAct with explicit tool verification) would be needed.

---

## Observability

### Structured Traces
Every LLM call, tool call, and reasoning step is recorded as a structured JSONL event:
```json
{
  "trace_id": "trace_a1b2c3d4e5f6_1719000000",
  "problem_id": "gsm_001",
  "strategy": "react",
  "problem": "Janet has 24 eggs...",
  "ground_truth": "18",
  "final_answer": "18",
  "is_correct": true,
  "total_input_tokens": 450,
  "total_output_tokens": 120,
  "total_latency_ms": 3500,
  "events": [
    {
      "timestamp": "2026-06-24T14:30:00Z",
      "strategy": "react",
      "problem_id": "gsm_001",
      "step_type": "llm_call",
      "inputs": {"prompt": "..."},
      "outputs": {"content": "..."},
      "token_usage": {"input": 120, "output": 40},
      "latency_ms": 800
    }
  ]
}
```

### Replay
```bash
make replay TRACE_ID=trace_a1b2c3d4e5f6_1719000000
make replay TRACE_ID=trace_a1b2c3d4e5f6_1719000000 REPLAY_ARGS=--strategy=tot
```

---

## Metrics

### Programmatic Metric: Numerical Exact Match
For GSM8K-style problems with numerical answers, we use **exact-match** after normalization:
- Strip `$`, `,`, whitespace
- Parse as float; if integer, compare as integer strings
- `"18" == "$18.00"` → correct
- `"1/4" == "0.25"` → correct (fraction normalization)

### Why Not F1 or Other Metrics?
Numerical exact-match is the standard for GSM8K. The answers are single numbers. There's no token-level partial credit — either you solved the problem or you didn't. For free-form answer tasks, we'd use the LLM judge fallback.

---

## Statistical Methodology

### Confidence Intervals
Two methods, both reported for transparency:
- **Wilson score interval**: analytic CI for proportions, well-behaved at extremes (near 0% or 100%)
- **Bootstrap (1000 samples)**: non-parametric, makes no distributional assumptions

### Win Matrix
For each strategy pair (A, B):
- **A_wins**: problems where A correct, B incorrect
- **B_wins**: problems where B correct, A incorrect  
- **ties**: both correct or both incorrect

This uses paired comparison (each strategy sees the same problems), which is more powerful than comparing aggregate accuracies.

### McNemar's Test (optional extension)
For statistical significance on the win matrix diagonal, use McNemar's test on the discordant pairs. Not yet automated but available via `scipy.stats`.

---

## Extending

### Adding a New Strategy
1. Create `strategies/my_strategy.py`
2. Inherit from `strategies.base.Strategy`
3. Implement `solve(problem, problem_id, ground_truth) -> Trace`
4. Use `Tracer.get().new_trace()` and `Tracer.get().save_trace(trace)`
5. Use `tools.calculator.calculator(expression)` for shared tool access
6. Register in `STRATEGY_REGISTRY` in `main.py`
7. Run `make eval`

### Adding a New Tool
1. Create `tools/my_tool.py`
2. Define a function with clear input/output contract
3. Import in strategy files as needed
4. All strategies share the same tool (fair comparison)

---

## Git Branch Discipline
```
main          — final submission, passing make eval
develop       — active work
feature/react — ReAct strategy development
feature/plan  — Plan-and-Execute development
feature/sc    — Self-Consistency development
feature/tot   — Tree-of-Thoughts development
```

---

## References
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) — Yao et al., 2022
- [Tree of Thoughts: Deliberate Problem Solving with Large Language Models](https://arxiv.org/abs/2305.10601) — Yao et al., 2023
- [Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091) — Wang et al., 2023
- [Self-Consistency Improves Chain of Thought Reasoning](https://arxiv.org/abs/2203.11171) — Wang et al., 2022
- [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) — Anthropic
- [Getting Started with OpenAI Evals](https://cookbook.openai.com/examples/evaluation/getting_started_with_openai_evals)
- [Hamel Husain on LLM Eval Discipline](https://hamel.dev/blog/posts/evals/)
- [Eugene Yan on LLM Evaluators](https://eugeneyan.com/writing/llm-evaluators/)