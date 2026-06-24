"""Plan-and-Execute Strategy.

A planner LLM produces a step-by-step plan upfront.
An executor (separate persona) runs each step in sequence,
calling tools as needed.
"""

import re
from datetime import datetime, timezone

from strategies.base import Strategy, Trace
from observability.tracer import Tracer, make_event
from llm_client import chat
from tools.calculator import calculator
from config import CONFIG


PLANNER_PROMPT = """You are a math problem planner. Given a problem, produce a step-by-step plan.

The plan MUST be a numbered list of steps. Each step should describe exactly ONE computation.
At the end, add a final step: "Step N: State the final answer."

Format:
Step 1: <description of computation>
Step 2: <description of computation>
...
Step N: State the final answer (just the number).

Be concise. Do NOT solve the problem — just lay out the steps.
"""

EXECUTOR_PROMPT = """You are a math problem executor. You will be given a single step from a plan.

Your job is to perform exactly that step's computation and output the result.

You have access to a calculator tool. To use it, write:
CALC: <expression>

Otherwise just compute and output the number.

IMPORTANT: Output ONLY the numerical result of this step, nothing else.
"""


def _parse_plan(plan_text: str) -> list[dict]:
    """Parse the planner's output into a list of step dicts."""
    steps = []
    # Match "Step X:" or "X." patterns
    pattern = r"(?:Step\s*)?(\d+)[.:)\s]+\s*(.+?)(?=(?:Step\s*)?\d+[.:)\s]+|\Z)"
    matches = re.findall(pattern, plan_text, re.DOTALL | re.IGNORECASE)

    for match in matches:
        num = match[0].strip()
        desc = match[1].strip() if len(match) > 1 else ""
        if desc:
            steps.append({"step_num": int(num), "description": desc, "result": ""})

    if not steps:
        # Fallback: split by newlines that start with digits
        for line in plan_text.split("\n"):
            line = line.strip()
            m = re.match(r"(\d+)[.:)]\s*(.+)", line)
            if m:
                steps.append({"step_num": int(m.group(1)), "description": m.group(2).strip(), "result": ""})

    # Separate final answer step
    final_step = None
    execution_steps = []
    for s in steps:
        desc_lower = s["description"].lower()
        if any(kw in desc_lower for kw in ["final answer", "state the", "final", "the answer is"]):
            if final_step is None:
                final_step = s
        else:
            execution_steps.append(s)

    if final_step is None and len(steps) > 0:
        final_step = steps[-1]
        execution_steps = steps[:-1]

    return execution_steps, final_step


def _extract_number(text: str) -> str:
    """Extract a number from text."""
    # Remove currency symbols
    text = text.replace("$", "").replace(",", "").strip()
    match = re.search(r"-?[\d.]+", text)
    if match:
        try:
            val = float(match.group(0))
            if val == int(val):
                return str(int(val))
            return str(val)
        except ValueError:
            pass
    return text.strip()


class PlanExecuteStrategy(Strategy):
    """Plan-and-Execute reasoning with shared calculator."""

    name = "plan_execute"

    def __init__(self):
        self.tracer = Tracer.get()

    def solve(self, problem: str, problem_id: str = "", ground_truth: str = "") -> Trace:
        trace = self.tracer.new_trace(
            problem_id=problem_id,
            strategy=self.name,
            problem_text=problem,
            ground_truth=ground_truth,
        )

        # --- Phase 1: Plan ---
        plan_resp = chat(
            [{"role": "user", "content": f"Problem: {problem}\n\n{PLANNER_PROMPT}"}],
            temperature=0.0,
            max_tokens=512,
        )

        event = make_event(
            strategy=self.name,
            problem_id=problem_id,
            step_type="plan",
            inputs={"problem": problem},
            outputs={"plan": plan_resp["content"]},
            token_usage={
                "input": plan_resp["input_tokens"],
                "output": plan_resp["output_tokens"],
            },
            latency_ms=plan_resp["latency_ms"],
        )
        trace.add_event(event)
        trace.total_input_tokens += plan_resp["input_tokens"]
        trace.total_output_tokens += plan_resp["output_tokens"]
        trace.total_latency_ms += plan_resp["latency_ms"]

        execution_steps, final_step = _parse_plan(plan_resp["content"])

        # --- Phase 2: Execute ---
        results = {}
        for step in execution_steps:
            exec_resp = chat(
                [
                    {"role": "system", "content": EXECUTOR_PROMPT},
                    {
                        "role": "user",
                        "content": f"Problem: {problem}\n\nStep to execute: {step['description']}\n\nOutput only the numerical result.",
                    },
                ],
                temperature=0.0,
                max_tokens=256,
            )

            # Check if executor requested calculator
            exec_text = exec_resp["content"].strip()
            calc_match = re.match(r"CALC:\s*(.+)", exec_text, re.IGNORECASE)

            if calc_match:
                calc_result = calculator(calc_match.group(1).strip())
                step_result = calc_result["result"] if calc_result["result"] is not None else "ERROR"

                event = make_event(
                    strategy=self.name,
                    problem_id=problem_id,
                    step_type="tool_call",
                    inputs={"tool": "calculator", "expression": calc_match.group(1).strip()},
                    outputs={"result": calc_result["result"], "error": calc_result["error"]},
                )
                trace.add_event(event)

                # Now have executor format the result
                format_resp = chat(
                    [
                        {"role": "system", "content": "Output only the number."},
                        {"role": "user", "content": f"Calculator says: {step_result}. Output only the number."},
                    ],
                    temperature=0.0,
                    max_tokens=64,
                )
                step_result = _extract_number(format_resp["content"])
                trace.total_input_tokens += format_resp["input_tokens"]
                trace.total_output_tokens += format_resp["output_tokens"]
            else:
                step_result = _extract_number(exec_text)

            step["result"] = step_result
            results[step["step_num"]] = step_result

            event = make_event(
                strategy=self.name,
                problem_id=problem_id,
                step_type="execute_step",
                inputs={"step": step["description"]},
                outputs={"result": step_result, "raw": exec_text},
                token_usage={
                    "input": exec_resp["input_tokens"],
                    "output": exec_resp["output_tokens"],
                },
                latency_ms=exec_resp["latency_ms"],
            )
            trace.add_event(event)
            trace.total_input_tokens += exec_resp["input_tokens"]
            trace.total_output_tokens += exec_resp["output_tokens"]
            trace.total_latency_ms += exec_resp["latency_ms"]

        # --- Phase 3: Synthesize final answer ---
        context = "\n".join([f"Step {s['step_num']}: {s['description']} => {s['result']}" for s in execution_steps])

        if final_step:
            final_prompt = f"Problem: {problem}\n\nIntermediate results:\n{context}\n\nNow execute the final step: {final_step['description']}\nOutput ONLY the final numerical answer."
        else:
            final_prompt = f"Problem: {problem}\n\nIntermediate results:\n{context}\n\nNow give the final numerical answer ONLY."

        final_resp = chat(
            [{"role": "user", "content": final_prompt}],
            temperature=0.0,
            max_tokens=128,
        )

        final_answer = _extract_number(final_resp["content"])

        event = make_event(
            strategy=self.name,
            problem_id=problem_id,
            step_type="final_answer",
            inputs={"context": context},
            outputs={"final_answer": final_answer, "raw": final_resp["content"]},
            token_usage={
                "input": final_resp["input_tokens"],
                "output": final_resp["output_tokens"],
            },
            latency_ms=final_resp["latency_ms"],
        )
        trace.add_event(event)
        trace.total_input_tokens += final_resp["input_tokens"]
        trace.total_output_tokens += final_resp["output_tokens"]
        trace.total_latency_ms += final_resp["latency_ms"]

        trace.final_answer = final_answer
        trace.extra["plan"] = plan_resp["content"]
        trace.extra["step_results"] = {str(k): v for k, v in results.items()}
        self.tracer.save_trace(trace)
        return trace