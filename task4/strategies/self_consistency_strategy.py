"""Self-Consistency Strategy.

Samples N ≥ 3 reasoning paths in parallel using Chain-of-Thought prompting,
then performs majority-vote (or judge-vote) on the final answer.

Uses the same calculator tool for consistency with other strategies.
The CoT instructions encourage the model to use CALC: syntax for the shared calculator.
"""

import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from strategies.base import Strategy, Trace
from observability.tracer import Tracer, make_event
from llm_client import chat
from tools.calculator import calculator
from config import CONFIG


COT_PROMPT = """You are an expert math problem solver.

Solve the problem step by step. Show your reasoning clearly.
For any arithmetic computation, you can use:
CALC: <expression>

When you reach the final answer, end with:
Final Answer: <the numerical answer only>

Solve carefully and double-check your work.
"""


def _extract_final_answer(text: str) -> str:
    """Extract final answer from CoT output."""
    # Look for "Final Answer: X"
    match = re.search(r"Final Answer:\s*(.+?)$", text, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Look for "the answer is X"
    match = re.search(r"(?:the\s+)?answer\s+is\s*[:]?\s*(.+?)$", text, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Look for last number in text
    numbers = re.findall(r"-?\d+[.,\d]*", text)
    if numbers:
        return numbers[-1].replace(",", "")

    return text.strip()


def _normalize_numeric(answer: str) -> str:
    """Normalize answer for majority-vote counting."""
    ans = answer.replace("$", "").replace(",", "").strip()
    try:
        f = float(ans)
        if f == int(f):
            return str(int(f))
        return str(round(f, 6))
    except ValueError:
        return ans.lower().strip()


def _single_cot_run(problem: str, problem_id: str, run_idx: int, tracer: Tracer) -> tuple:
    """Run a single CoT path and return (final_answer, raw_output, trace_events)."""
    events = []

    messages = [
        {"role": "user", "content": f"{COT_PROMPT}\n\nProblem: {problem}"},
    ]

    # We may need multiple turns if the model uses CALC:
    max_turns = 5
    for turn in range(max_turns):
        resp = chat(messages, temperature=0.7, max_tokens=512)

        events.append({
            "turn": turn,
            "raw": resp["content"],
            "input_tokens": resp["input_tokens"],
            "output_tokens": resp["output_tokens"],
            "latency_ms": resp["latency_ms"],
        })

        messages.append({"role": "assistant", "content": resp["content"]})

        # Check for calculator invocation
        calc_matches = re.findall(r"CALC:\s*(.+?)(?:\n|$)", resp["content"], re.IGNORECASE)
        if calc_matches:
            for expr in calc_matches:
                calc_res = calculator(expr.strip())
                observation = f"[CALCULATOR RESULT for '{expr.strip()}']: {calc_res['result']}"
                if calc_res["error"]:
                    observation = f"[CALCULATOR ERROR for '{expr.strip()}']: {calc_res['error']}"
                messages.append({"role": "user", "content": observation})
            continue  # Continue loop to process CALC results

        # Check if we have a final answer
        if "final answer:" in resp["content"].lower() or "answer is" in resp["content"].lower():
            break

    final_answer = _extract_final_answer(messages[-1]["content"])
    return final_answer, messages[-1]["content"], events


class SelfConsistencyStrategy(Strategy):
    """Self-Consistency: N parallel CoT runs, majority vote on answer."""

    name = "self_consistency"

    def __init__(self):
        self.tracer = Tracer.get()
        self.n = CONFIG.self_consistency_n

    def solve(self, problem: str, problem_id: str = "", ground_truth: str = "") -> Trace:
        trace = self.tracer.new_trace(
            problem_id=problem_id,
            strategy=self.name,
            problem_text=problem,
            ground_truth=ground_truth,
        )

        # Run N paths in parallel
        all_answers = []
        all_raw = []
        all_events = []

        with ThreadPoolExecutor(max_workers=min(self.n, 5)) as executor:
            futures = {
                executor.submit(_single_cot_run, problem, problem_id, i, self.tracer): i
                for i in range(self.n)
            }
            for future in as_completed(futures):
                idx = futures[future]
                answer, raw, events = future.result()
                all_answers.append((idx, answer))
                all_raw.append((idx, raw))
                all_events.append((idx, events))

        # Sort by index
        all_answers.sort(key=lambda x: x[0])
        all_raw.sort(key=lambda x: x[0])
        all_events.sort(key=lambda x: x[0])

        answers_in_order = [a[1] for a in all_answers]

        # Log each path as an event
        for i, (idx, events) in enumerate(all_events):
            total_in = sum(e["input_tokens"] for e in events)
            total_out = sum(e["output_tokens"] for e in events)
            total_lat = sum(e["latency_ms"] for e in events)

            event = make_event(
                strategy=self.name,
                problem_id=problem_id,
                step_type=f"cot_path_{i}",
                inputs={"problem": problem},
                outputs={"answer": all_answers[i][1], "raw": all_raw[i][1]},
                token_usage={"input": total_in, "output": total_out},
                latency_ms=total_lat,
                meta={"path_index": i},
            )
            trace.add_event(event)
            trace.total_input_tokens += total_in
            trace.total_output_tokens += total_out
            trace.total_latency_ms += total_lat

        # Majority vote
        normalized = [_normalize_numeric(a) for a in answers_in_order]
        counter = Counter(normalized)
        majority_answer, count = counter.most_common(1)[0]

        event = make_event(
            strategy=self.name,
            problem_id=problem_id,
            step_type="majority_vote",
            inputs={"all_answers": answers_in_order, "normalized": normalized},
            outputs={"winner": majority_answer, "count": count, "total": self.n},
        )
        trace.add_event(event)

        trace.final_answer = majority_answer
        trace.extra["all_answers"] = answers_in_order
        trace.extra["vote_counts"] = dict(counter)
        self.tracer.save_trace(trace)
        return trace