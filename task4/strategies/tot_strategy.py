"""Tree-of-Thoughts (ToT) Strategy.

Explicit branching with ≥ 2 alternatives per step, a value/score function
over partial states, and a beam search strategy.

Uses the shared calculator tool for all computations.
Logs the search tree in extra.tree_structure for visualization.
"""

import re
import math
import json
from typing import List, Dict, Optional

from strategies.base import Strategy, Trace
from observability.tracer import Tracer, make_event
from llm_client import chat
from tools.calculator import calculator
from config import CONFIG


GENERATE_PROMPT = """You are solving this math problem step by step.

Problem: {problem}

Current state (intermediate results so far):
{state_summary}

Propose EXACTLY {num_branches} different possible next steps.
Each step should be ONE computation that moves toward the solution.

Format each as:
Branch {i}: <description of the computation>
"""

EVALUATE_PROMPT = """You are evaluating partial solutions to a math problem.

Problem: {problem}

Current state:
{state}

Proposed next step:
{step}

Rate how promising this step is on a scale of 1-10 (10 = definitely correct and leading to answer).
Consider:
- Is the computation relevant to the problem?
- Is the arithmetic logic sound?
- Does it bring us closer to the final answer?

Output ONLY a number between 1 and 10.
"""

EXTRACT_ANSWER_PROMPT = """Problem: {problem}

Based on the following solution path:
{path}

What is the final numerical answer? Output ONLY the number.
"""


def _parse_branches(text: str, num_expected: int) -> List[str]:
    """Parse branch proposals from generation output."""
    branches = []
    for i in range(1, num_expected + 1):
        pattern = rf"Branch\s*{i}:\s*(.+?)(?=Branch\s*{i+1}:|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            branches.append(match.group(1).strip())
        else:
            # Try simpler pattern
            pattern2 = rf"{i}[.):]\s*(.+?)(?=\d+[.):]|\Z)"
            match2 = re.search(pattern2, text, re.DOTALL)
            if match2:
                branches.append(match2.group(1).strip())

    # If we didn't get enough, split by newlines
    if len(branches) < num_expected:
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.strip().startswith("#")]
        if len(lines) >= num_expected:
            branches = lines[:num_expected]

    return branches[:num_expected]


class ThoughtNode:
    """A node in the ToT tree."""

    def __init__(self, step_desc: str, parent=None):
        self.step_desc = step_desc
        self.parent = parent
        self.children: List["ThoughtNode"] = []
        self.score: float = 0.0
        self.result: str = ""
        self.depth: int = parent.depth + 1 if parent else 0

    def path(self) -> List[str]:
        """Return the full path from root to this node."""
        if self.parent is None:
            return [self.step_desc]
        return self.parent.path() + [self.step_desc]

    def to_dict(self) -> dict:
        return {
            "step": self.step_desc,
            "score": self.score,
            "result": self.result,
            "depth": self.depth,
            "children": [c.to_dict() for c in self.children],
        }


class ToTStrategy(Strategy):
    """Tree-of-Thoughts with beam search and shared calculator."""

    name = "tot"

    def __init__(self):
        self.tracer = Tracer.get()
        self.beam_width = CONFIG.tot_beam_width
        self.max_depth = CONFIG.tot_max_depth

    def _evaluate_step(self, problem: str, state: str, step: str) -> float:
        """Score a proposed step 1-10."""
        resp = chat(
            [
                {"role": "user", "content": EVALUATE_PROMPT.format(
                    problem=problem, state=state, step=step
                )},
            ],
            temperature=0.0,
            max_tokens=16,
        )
        try:
            score = float(re.search(r"[\d.]+", resp["content"]).group(0))
            return min(10, max(1, score))
        except (ValueError, AttributeError):
            return 5.0  # Neutral default

    def _compute_step(self, step_desc: str) -> str:
        """Execute a computational step."""
        # Try to extract an expression
        # Look for patterns like "compute 3*4", "calculate 5+6"
        calc_match = re.search(r"calc(?:ulate)?\s*[:]?\s*(.+?)(?:$|\.|\n)", step_desc, re.IGNORECASE)
        if calc_match:
            expr = calc_match.group(1).strip()
            res = calculator(expr)
            return res["result"] if res["result"] is not None else f"ERROR: {res['error']}"

        # Look for arithmetic expression
        expr_match = re.search(r"([\d\s+\-*/%().^\s]{3,})", step_desc)
        if expr_match:
            expr = expr_match.group(1).strip()
            # Only if it contains operators
            if any(op in expr for op in "+-*/"):
                res = calculator(expr)
                return res["result"] if res["result"] is not None else "0"

        # Use LLM to compute
        resp = chat(
            [
                {"role": "system", "content": "You are a calculator. Output ONLY the number."},
                {"role": "user", "content": f"Compute: {step_desc}\nOutput ONLY the number."},
            ],
            temperature=0.0,
            max_tokens=32,
        )
        num_match = re.search(r"-?[\d.]+", resp["content"])
        return num_match.group(0) if num_match else "0"

    def solve(self, problem: str, problem_id: str = "", ground_truth: str = "") -> Trace:
        trace = self.tracer.new_trace(
            problem_id=problem_id,
            strategy=self.name,
            problem_text=problem,
            ground_truth=ground_truth,
        )

        # Root node (empty start state)
        root = ThoughtNode("Start", parent=None)
        root.score = 10.0
        beam = [root]

        total_nodes = 1
        tree_log = []

        for depth in range(self.max_depth):
            all_candidates = []

            for node in beam:
                state_summary = " -> ".join(node.path())
                if state_summary == "Start":
                    state_summary = "(beginning)"

                # Generate branches
                gen_resp = chat(
                    [
                        {"role": "user", "content": GENERATE_PROMPT.format(
                            problem=problem,
                            state_summary=state_summary,
                            num_branches=self.beam_width,
                        )},
                    ],
                    temperature=0.7,
                    max_tokens=256,
                )

                branches = _parse_branches(gen_resp["content"], self.beam_width)

                event = make_event(
                    strategy=self.name,
                    problem_id=problem_id,
                    step_type="branch_generation",
                    inputs={"depth": depth, "state": state_summary},
                    outputs={"branches": branches, "raw": gen_resp["content"]},
                    token_usage={
                        "input": gen_resp["input_tokens"],
                        "output": gen_resp["output_tokens"],
                    },
                    latency_ms=gen_resp["latency_ms"],
                )
                trace.add_event(event)
                trace.total_input_tokens += gen_resp["input_tokens"]
                trace.total_output_tokens += gen_resp["output_tokens"]
                trace.total_latency_ms += gen_resp["latency_ms"]

                for branch in branches:
                    if not branch.strip():
                        continue
                    child = ThoughtNode(branch, parent=node)
                    total_nodes += 1

                    # Evaluate
                    score = self._evaluate_step(problem, state_summary, branch)
                    child.score = score

                    # Compute result
                    result = self._compute_step(branch)
                    child.result = result

                    node.children.append(child)
                    all_candidates.append(child)

            if not all_candidates:
                break

            # Beam search: keep top beam_width
            all_candidates.sort(key=lambda n: n.score, reverse=True)
            beam = all_candidates[:self.beam_width]

            # Log tree at this depth
            depth_log = {
                "depth": depth + 1,
                "num_candidates": len(all_candidates),
                "selected": [{"step": n.step_desc, "score": n.score, "result": n.result} for n in beam],
            }
            tree_log.append(depth_log)

            # Check if any has reached a final answer
            for node in beam:
                if any(kw in node.step_desc.lower() for kw in ["final", "answer is", "result is"]):
                    # Extract answer from this node
                    num_match = re.search(r"-?\d+[.,\d]*", node.result or node.step_desc)
                    if num_match:
                        final_answer = num_match.group(0).replace(",", "")
                        trace.final_answer = final_answer
                        trace.extra["tree"] = root.to_dict()
                        trace.extra["tree_log"] = tree_log
                        trace.extra["total_nodes"] = total_nodes
                        trace.extra["final_depth"] = depth + 1

                        event = make_event(
                            strategy=self.name,
                            problem_id=problem_id,
                            step_type="final_answer",
                            inputs={"path": node.path()},
                            outputs={"final_answer": final_answer, "node_score": node.score},
                        )
                        trace.add_event(event)
                        self.tracer.save_trace(trace)
                        return trace

        # If no explicit final answer, use best beam node
        if beam:
            best = beam[0]
            # Compute final answer from best path
            path_text = " -> ".join(best.path())
            results_text = "; ".join([f"{n.step_desc} => {n.result}" for n in beam])

            final_resp = chat(
                [
                    {"role": "user", "content": EXTRACT_ANSWER_PROMPT.format(
                        problem=problem,
                        path=f"{path_text}\n\nResults: {results_text}",
                    )},
                ],
                temperature=0.0,
                max_tokens=64,
            )

            num_match = re.search(r"-?[\d.]+", final_resp["content"])
            final_answer = num_match.group(0) if num_match else best.result

            trace.total_input_tokens += final_resp["input_tokens"]
            trace.total_output_tokens += final_resp["output_tokens"]
            trace.total_latency_ms += final_resp["latency_ms"]
        else:
            final_answer = "NO_ANSWER"

        trace.final_answer = final_answer
        trace.extra["tree"] = root.to_dict()
        trace.extra["tree_log"] = tree_log
        trace.extra["total_nodes"] = total_nodes
        trace.extra["final_depth"] = self.max_depth

        event = make_event(
            strategy=self.name,
            problem_id=problem_id,
            step_type="final_answer",
            inputs={"beam_scores": [n.score for n in beam] if beam else []},
            outputs={"final_answer": final_answer},
        )
        trace.add_event(event)
        self.tracer.save_trace(trace)
        return trace