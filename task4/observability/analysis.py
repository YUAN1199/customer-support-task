"""Cost and latency analysis for strategy traces.

Reads stored JSONL traces and computes per-strategy totals for:
  - tokens in, tokens out
  - wall-clock time (latency sum)
  - cost per correct answer
  - cost per problem

Outputs a Markdown table suitable for the README.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


TRACES_DIR = Path(__file__).parent.parent / "data" / "traces"

# Approximate pricing (OpenRouter free-tier models — adjust as needed)
# Using conservative estimates for a ~7B model
PRICE_PER_1K_INPUT = 0.000_055  # $0.055 / 1M tokens
PRICE_PER_1K_OUTPUT = 0.000_220  # $0.22 / 1M tokens


def compute_cost(input_tokens: int, output_tokens: int) -> float:
    """Compute dollar cost from token counts."""
    cost_in = (input_tokens / 1000) * PRICE_PER_1K_INPUT
    cost_out = (output_tokens / 1000) * PRICE_PER_1K_OUTPUT
    return cost_in + cost_out


def analyze_traces() -> Dict:
    """Analyze all stored traces and produce per-strategy stats.

    Returns:
        Dict with per-strategy cost/latency/accuracy data.
    """
    if not TRACES_DIR.exists():
        return {"error": "No traces directory found. Run eval first."}

    strategy_data = defaultdict(lambda: {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_latency_ms": 0,
        "total_problems": 0,
        "correct_problems": 0,
        "traces": [],
    })

    for fname in os.listdir(TRACES_DIR):
        if not fname.endswith(".jsonl"):
            continue
        strategy = fname.replace(".jsonl", "")
        filepath = TRACES_DIR / fname

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                trace = json.loads(line)
                sd = strategy_data[strategy]
                sd["total_input_tokens"] += trace.get("total_input_tokens", 0)
                sd["total_output_tokens"] += trace.get("total_output_tokens", 0)
                sd["total_latency_ms"] += trace.get("total_latency_ms", 0)
                sd["total_problems"] += 1
                if trace.get("is_correct", False):
                    sd["correct_problems"] += 1
                sd["traces"].append(trace)

    results = {}
    for strategy, sd in strategy_data.items():
        total_cost = compute_cost(sd["total_input_tokens"], sd["total_output_tokens"])
        correct = sd["correct_problems"]
        total = sd["total_problems"]
        cost_per_correct = total_cost / correct if correct > 0 else float("inf")
        cost_per_problem = total_cost / total if total > 0 else 0
        avg_latency_s = (sd["total_latency_ms"] / total / 1000) if total > 0 else 0
        accuracy = correct / total if total > 0 else 0

        results[strategy] = {
            "total_input_tokens": sd["total_input_tokens"],
            "total_output_tokens": sd["total_output_tokens"],
            "total_tokens": sd["total_input_tokens"] + sd["total_output_tokens"],
            "total_latency_ms": sd["total_latency_ms"],
            "total_latency_s": sd["total_latency_ms"] / 1000,
            "total_cost": total_cost,
            "total_problems": total,
            "correct": correct,
            "accuracy": accuracy,
            "cost_per_correct": cost_per_correct,
            "cost_per_problem": cost_per_problem,
            "avg_latency_s": avg_latency_s,
            "avg_input_tokens": sd["total_input_tokens"] / total if total > 0 else 0,
            "avg_output_tokens": sd["total_output_tokens"] / total if total > 0 else 0,
        }

    return results


def format_cost_table(results: Dict) -> str:
    """Format the cost/latency analysis as a Markdown table."""
    lines = [
        "## Cost / Latency Table",
        "",
        "| Strategy | Problems | Correct | Accuracy | Tokens In | Tokens Out | Latency (s) | Cost ($) | Cost/Correct ($) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for name, r in sorted(results.items()):
        lines.append(
            f"| {name} | {r['total_problems']} | {r['correct']} | "
            f"{r['accuracy']:.1%} | {r['total_input_tokens']:,} | {r['total_output_tokens']:,} | "
            f"{r['total_latency_s']:.1f} | ${r['total_cost']:.4f} | ${r['cost_per_correct']:.4f} |"
        )

    return "\n".join(lines)


def compute_failure_taxonomy(traces: List[Dict]) -> Dict:
    """Hand-classify failures from trace data.

    Categories:
      - wrong_answer: correct process, wrong arithmetic
      - tool_error: calculator returned error or malformed output
      - plan_abandoned: plan-execute didn't complete all steps
      - parse_error: couldn't parse the model's output
      - infinite_loop: hit max steps without answer
      - judge_disagreement: programmatic says wrong but judge says right (or vice versa)
      - wrong_reasoning: flawed logic, not just arithmetic
      - no_answer: model produced no extractable answer

    Returns dict with category counts.
    """
    categories = defaultdict(int)
    for t in traces:
        if t.get("is_correct", False):
            continue

        events = t.get("events", [])
        final_answer = t.get("final_answer", "")

        if final_answer == "NO_ANSWER":
            categories["no_answer"] += 1
            continue

        # Check for tool errors
        tool_errors = [
            e for e in events
            if e.get("step_type") == "tool_call" and e.get("outputs", {}).get("error")
        ]
        if tool_errors:
            categories["tool_error"] += 1
            continue

        # Check for abandoned plans
        if t.get("strategy") == "plan_execute":
            extra = t.get("extra", {})
            step_results = extra.get("step_results", {})
            if len(step_results) == 0:
                categories["plan_abandoned"] += 1
                continue

        # Check for max steps / loop
        max_step_events = [
            e for e in events
            if e.get("meta", {}).get("reason") == "max_steps_exceeded"
        ]
        if max_step_events:
            categories["infinite_loop"] += 1
            continue

        # Default: wrong reasoning or arithmetic
        categories["wrong_answer"] += 1

    return dict(categories)


if __name__ == "__main__":
    results = analyze_traces()
    if "error" in results:
        print(results["error"])
    else:
        print(format_cost_table(results))