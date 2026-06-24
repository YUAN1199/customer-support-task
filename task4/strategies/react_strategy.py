"""ReAct Strategy — interleaved Reason–Act–Observe loop.

The agent alternates between:
  - Reason: think about what to do next
  - Act: choose a tool to call (or final answer)
  - Observe: receive the result of the tool call

Uses the shared calculator tool as the external tool.
"""

import re
import time
from datetime import datetime, timezone

from strategies.base import Strategy, Trace
from observability.tracer import Tracer, make_event
from llm_client import chat
from tools.calculator import calculator
from config import CONFIG


REACT_SYSTEM_PROMPT = """You are an expert math problem solver using the ReAct framework.

You solve problems step by step.  For each step, you must respond in one of two formats:

FORMAT A — when you need to compute something:
Thought: <your reasoning about what to compute>
Action: calculator
Action Input: <mathematical expression to evaluate, e.g., "16 - 3 - 4">

FORMAT B — when you have the final answer:
Thought: <final reasoning>
Final Answer: <the numerical answer only>
"""


def _parse_react_output(text: str) -> dict:
    """Parse the ReAct agent's output."""
    result = {"thought": "", "action": "", "action_input": "", "final_answer": ""}

    # Look for Final Answer first (higher priority)
    fa_match = re.search(r"Final Answer:\s*(.+?)$", text, re.MULTILINE | re.IGNORECASE)
    if fa_match:
        result["final_answer"] = fa_match.group(1).strip()

    # Look for Thought
    thought_match = re.search(r"Thought:\s*(.+?)$", text, re.MULTILINE | re.IGNORECASE)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()

    # If there's a final answer but the text also shows "Thought:" pattern, extract first one
    # Look for Action
    action_match = re.search(r"Action:\s*(.+?)$", text, re.MULTILINE | re.IGNORECASE)
    if action_match:
        result["action"] = action_match.group(1).strip()

    # Look for Action Input
    ai_match = re.search(r"Action Input:\s*(.+?)$", text, re.MULTILINE | re.IGNORECASE)
    if ai_match:
        result["action_input"] = ai_match.group(1).strip()

    # If no final answer found but text contains just a number, try to extract
    if not result["final_answer"]:
        # Check if the whole text is just a number
        num_match = re.match(r"^\s*[\d.,$]+\s*$", text)
        if num_match:
            result["final_answer"] = text.strip()

    return result


class ReActStrategy(Strategy):
    """ReAct reasoning with calculator tool."""

    name = "react"

    def __init__(self):
        self.tracer = Tracer.get()
        self.max_steps = CONFIG.react_max_steps

    def solve(self, problem: str, problem_id: str = "", ground_truth: str = "") -> Trace:
        trace = self.tracer.new_trace(
            problem_id=problem_id,
            strategy=self.name,
            problem_text=problem,
            ground_truth=ground_truth,
        )

        messages = [
            {"role": "system", "content": REACT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Problem: {problem}\n\nSolve step by step."},
        ]

        final_answer = ""
        step_count = 0

        while step_count < self.max_steps:
            step_count += 1

            # Reason step
            resp = chat(messages, temperature=0.0, max_tokens=512)

            event = make_event(
                strategy=self.name,
                problem_id=problem_id,
                step_type="reason",
                inputs={"messages_snapshot": [m["role"] for m in messages[-4:]]},
                outputs={"raw_response": resp["content"]},
                token_usage={
                    "input": resp["input_tokens"],
                    "output": resp["output_tokens"],
                },
                latency_ms=resp["latency_ms"],
            )
            trace.add_event(event)
            trace.total_input_tokens += resp["input_tokens"]
            trace.total_output_tokens += resp["output_tokens"]
            trace.total_latency_ms += resp["latency_ms"]

            assistant_msg = resp["content"]
            messages.append({"role": "assistant", "content": assistant_msg})

            parsed = _parse_react_output(assistant_msg)

            if parsed["final_answer"]:
                final_answer = parsed["final_answer"]
                event = make_event(
                    strategy=self.name,
                    problem_id=problem_id,
                    step_type="final_answer",
                    inputs={"parsed": parsed},
                    outputs={"final_answer": final_answer},
                )
                trace.add_event(event)
                break

            if parsed["action"].lower() == "calculator" and parsed["action_input"]:
                # Act step
                calc_result = calculator(parsed["action_input"])
                observation = (
                    f"Observation: {calc_result['result']}"
                    if calc_result["result"] is not None
                    else f"Observation: Error - {calc_result['error']}"
                )

                event = make_event(
                    strategy=self.name,
                    problem_id=problem_id,
                    step_type="tool_call",
                    inputs={"tool": "calculator", "expression": parsed["action_input"]},
                    outputs={"result": calc_result["result"], "error": calc_result["error"]},
                )
                trace.add_event(event)

                messages.append({"role": "user", "content": observation})
            else:
                # No valid action — try to extract just a number as final answer
                num_match = re.search(r"\d+", assistant_msg)
                if num_match and step_count >= 2:
                    final_answer = num_match.group(0)
                    break
                messages.append(
                    {
                        "role": "user",
                        "content": "Please continue with the ReAct format: Thought / Action / Action Input, or give Final Answer.",
                    }
                )

        if not final_answer:
            final_answer = "NO_ANSWER"
            event = make_event(
                strategy=self.name,
                problem_id=problem_id,
                step_type="final_answer",
                inputs={},
                outputs={"final_answer": "NO_ANSWER", "reason": "max_steps_exceeded"},
            )
            trace.add_event(event)

        trace.final_answer = final_answer
        self.tracer.save_trace(trace)
        return trace