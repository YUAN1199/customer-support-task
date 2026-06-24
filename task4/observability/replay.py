"""Replay tool — re-run a single problem from a stored trace.

Given a trace ID, loads the original trace and re-runs the same problem,
optionally with a different strategy or model.  Outputs a diff against
the original trace (as a bonus).

Usage:
    python -m observability.replay --trace-id <TRACE_ID> [--strategy <name>] [--model <model>]
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from observability.tracer import Tracer


def _get_strategy_registry():
    from strategies.react_strategy import ReActStrategy
    from strategies.plan_execute_strategy import PlanExecuteStrategy
    from strategies.self_consistency_strategy import SelfConsistencyStrategy
    from strategies.tot_strategy import ToTStrategy
    return {
        "react": ReActStrategy,
        "plan_execute": PlanExecuteStrategy,
        "self_consistency": SelfConsistencyStrategy,
        "tot": ToTStrategy,
    }


def replay_from_trace(
    trace_id: str,
    strategy_name: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """Replay a problem from a stored trace.

    Args:
        trace_id: The trace to replay.
        strategy_name: Override the strategy (optional).
        model: Override the model (optional).

    Returns:
        Dict with original_trace, new_trace, and diff.
    """
    tracer = Tracer.get()
    original = tracer.get_trace_by_id(trace_id)

    if original is None:
        return {"error": f"Trace not found: {trace_id}"}

    problem = original.get("problem", "")
    problem_id = original.get("problem_id", "")
    ground_truth = original.get("ground_truth", "")
    orig_strategy = original.get("strategy", "")
    orig_answer = original.get("final_answer", "")

    use_strategy = strategy_name or orig_strategy

    registry = _get_strategy_registry()
    if use_strategy not in registry:
        return {"error": f"Unknown strategy: {use_strategy}. Available: {list(registry.keys())}"}

    # Run with (possibly different) strategy
    strategy_cls = registry[use_strategy]
    strategy = strategy_cls()

    # If model override, we'd set it on the llm_client — skip for now
    trace = strategy.solve(
        problem=problem,
        problem_id=problem_id,
        ground_truth=ground_truth,
    )

    new_trace = trace.to_dict()

    diff = {
        "original_strategy": orig_strategy,
        "replay_strategy": use_strategy,
        "original_answer": orig_answer,
        "replay_answer": trace.final_answer,
        "answer_match": _normalize(orig_answer) == _normalize(trace.final_answer),
        "same_strategy": orig_strategy == use_strategy,
        "original_input_tokens": original.get("total_input_tokens", 0),
        "replay_input_tokens": trace.total_input_tokens,
        "original_output_tokens": original.get("total_output_tokens", 0),
        "replay_output_tokens": trace.total_output_tokens,
    }

    return {
        "original_trace": original,
        "new_trace": new_trace,
        "diff": diff,
    }


def _normalize(ans: str) -> str:
    ans = ans.replace("$", "").replace(",", "").strip()
    try:
        f = float(ans)
        if f == int(f):
            return str(int(f))
        return str(round(f, 6))
    except ValueError:
        return ans.lower().strip()


def main():
    parser = argparse.ArgumentParser(description="Replay a problem from a stored trace")
    parser.add_argument("--trace-id", required=True, help="Trace ID to replay")
    parser.add_argument("--strategy", default=None, help="Override strategy name")
    parser.add_argument("--model", default=None, help="Override model (not yet implemented)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = replay_from_trace(args.trace_id, args.strategy, args.model)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        if "error" in result:
            print(f"ERROR: {result['error']}")
            return

        diff = result["diff"]
        print("=" * 60)
        print("REPLAY RESULT")
        print("=" * 60)
        print(f"Original trace:  {args.trace_id}")
        print(f"Original strategy: {diff['original_strategy']}  →  Replay strategy: {diff['replay_strategy']}")
        print(f"Original answer:  {diff['original_answer']}")
        print(f"Replay answer:    {diff['replay_answer']}")
        print(f"Answer match:     {diff['answer_match']}")
        print(f"Same strategy:    {diff['same_strategy']}")
        print(f"Original tokens:  in={diff['original_input_tokens']}, out={diff['original_output_tokens']}")
        print(f"Replay tokens:    in={diff['replay_input_tokens']}, out={diff['replay_output_tokens']}")
        print("=" * 60)


if __name__ == "__main__":
    main()