# Task 2: Routing, Parallelization & Reflection in Depth
## Deep Research Assistant

This task implements a fully agentic research system that routes, parallelizes, synthesizes, and reflects on complex open-ended questions.

---

## Architecture
1. **Routing (Domain Supervisor)**
   - Scientific / Technical
   - Historical / Cultural
   - Financial / Business
   - General
   - Fallback (with guardrail against prompt injection)

2. **Parallelization (Map-Reduce + Best-of-N)**
   - Decompose into 3 sub-questions
   - Parallel fan-out with asyncio.gather()
   - Best-of-3 candidate selection
   - Timing logs: parallel vs sequential

3. **Reflection (Producer-Critic Loop)**
   - 3 iterations
   - Structured scoring (0–10)
   - Measurable improvement
   - Plateau-safe

---

## How to Run
```bash
python task2/research_assistant.py
##Example Input
Compare environmental impact of lithium-ion vs sodium-ion batteries for grid storage
##Example Output
Routed domain: SCIENTIFIC
Parallel time: 1.2s | Sequential ~3.6s
Best-of-N selected top answer
Reflection scores improved across 3 iterations
Final structured research brief
