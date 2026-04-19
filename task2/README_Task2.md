# Task 2: Routing, Parallelization & Reflection in Depth
## Deep Research Assistant
This task implements a fully agentic research system that routes, parallelizes, synthesizes, and reflects on complex open-ended questions.

## Architecture
### 1. Routing (Domain Supervisor)
- Scientific / Technical
- Historical / Cultural
- Financial / Business
- General
- Fallback (with guardrail against prompt injection)

### 2. Parallelization (Map-Reduce + Best-of-N)
- Decompose into 3 sub-questions
- Parallel fan-out with asyncio.gather()
- Best-of-3 candidate selection
- Timing logs: parallel vs sequential

### 3. Reflection (Producer-Critic Loop)
- 3 iterations
- Structured scoring (0–10)
- Measurable improvement
- Plateau-safe

## How to Run
```bash
python task2/research_assistant.py

Example Input
Compare environmental impact of lithium-ion vs sodium-ion batteries for grid storage?
Example Output
Please enter your research question: Compare environmental impact of lithium-ion vs sodium-ion batteries for grid storage?======================================================================DEEP RESEARCH ASSISTANT======================================================================
✅ Routed domain: GENERAL
⏱ Parallel time: 0.3s | Estimated sequential: 0.9s
=== DRAFT RESEARCH BRIEF ===
Answer: Define core concepts in: Compare environmental imp... | FactScore: 6.9
Answer: Key evidence and findings for: Compare environment... | FactScore: 3.7
Answer: Pros, cons, and challenges for: Compare environmen... | FactScore: 4.4
=== REFLECTION LOOP START ===Iter 1 | Score: 6.5 | Feedback: Improve factual precision, clarity, and structure.Iter 2 | Score: 6.1 | Feedback: Improve factual precision, clarity, and structure.Iter 3 | Score: 7.2 | Feedback: Improve factual precision, clarity, and structure.=== REFLECTION LOOP END ===
======================================================================FINAL RESEARCH BRIEF======================================================================
Answer: Define core concepts in: Compare environmental imp... | FactScore: 6.9
Answer: Key evidence and findings for: Compare environment... | FactScore: 3.7
Answer: Pros, cons, and challenges for: Compare environmen... | FactScore: 4.4
[Improved] Improve factual precision, clarity, and structure.
[Improved] Improve factual precision, clarity, and structure.
[Improved] Improve factual precision, clarity, and structure.
Score history: [6.5, 6.1, 7.2]
