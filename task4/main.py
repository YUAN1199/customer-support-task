"""Agentic Reasoning Lab — Main Eval Harness.

Runs all reasoning strategies against the golden test set,
computes metrics, confidence intervals, win matrix, LLM judge
sanity check, records baseline, and outputs a full report.

Usage:
    python main.py                    # Run all strategies on all problems
    python main.py --strategy react   # Run only ReAct
    python main.py --demo             # Run one example per strategy
    python main.py --record-baseline  # Record current results as baseline
    python main.py --delta            # Show delta vs baseline
    python main.py --judge-sanity     # Run judge sanity check
"""

import json
import sys
import argparse
import time
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

# Import strategy implementations
from strategies.react_strategy import ReActStrategy
from strategies.plan_execute_strategy import PlanExecuteStrategy
from strategies.self_consistency_strategy import SelfConsistencyStrategy
from strategies.tot_strategy import ToTStrategy

from eval.metrics import exact_match, extract_number
from eval import comparison
from eval.baseline import record_baseline, compute_delta, format_delta_report
from eval.judge import LLMJudge
from observability.analysis import analyze_traces, format_cost_table, compute_failure_taxonomy
from observability.tracer import Tracer

from config import CONFIG


STRATEGY_REGISTRY = {
    "react": ReActStrategy,
    "plan_execute": PlanExecuteStrategy,
    "self_consistency": SelfConsistencyStrategy,
    "tot": ToTStrategy,
}


def load_golden_set(path: str = None) -> List[Dict]:
    """Load the golden test set from JSONL."""
    path = path or CONFIG.golden_set_path
    problems = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                problems.append(json.loads(line))
    return problems


def run_strategies_on_problem(
    problem: Dict,
    strategies: List[str],
) -> Dict[str, bool]:
    """Run all strategies on one problem, return {strategy_name: is_correct}."""
    results = {}
    for s_name in strategies:
        strat_cls = STRATEGY_REGISTRY[s_name]
        strategy = strat_cls()
        print(f"  [{s_name}] Running...", end=" ", flush=True)
        t0 = time.time()
        trace = strategy.solve(
            problem=problem["problem"],
            problem_id=problem["id"],
            ground_truth=problem["answer"],
        )
        elapsed = time.time() - t0

        # Evaluate correctness
        correct = exact_match(trace.final_answer, problem["answer"])
        trace.is_correct = correct

        # Save trace (update the stored one)
        tracer = Tracer.get()
        # Find and update the trace
        stored = tracer.get_trace_by_id(trace.trace_id)
        if stored:
            stored["is_correct"] = correct
            # Re-save
            filepath = Path(CONFIG.traces_dir) / f"{s_name}.jsonl"
            # Read all, update, rewrite
            lines = []
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        d = json.loads(line)
                        if d.get("trace_id") == trace.trace_id:
                            d["is_correct"] = correct
                        lines.append(json.dumps(d, ensure_ascii=False))
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

        status = "✓" if correct else "✗"
        print(f"{status} (answer: {trace.final_answer}, truth: {problem['answer']}, {elapsed:.1f}s)")

        results[s_name] = correct

    return results


def run_eval(strategies: List[str], problems: List[Dict]) -> Dict:
    """Run full eval across all strategies and problems.

    Returns:
        Dict with per-strategy results, stats, win matrix, etc.
    """
    # strategy_results[s_name][problem_id] = bool
    strategy_results: Dict[str, Dict[str, bool]] = defaultdict(dict)

    total = len(problems)
    print(f"\n{'='*60}")
    print(f"Running evaluation: {len(strategies)} strategies × {total} problems")
    print(f"{'='*60}\n")

    for i, problem in enumerate(problems):
        pid = problem["id"]
        print(f"[{i+1}/{total}] Problem {pid}: {problem['problem'][:60]}...")

        try:
            per_problem_results = run_strategies_on_problem(problem, strategies)
        except Exception as e:
            print(f"  ERROR: {e}")
            per_problem_results = {s: False for s in strategies}

        for s_name, correct in per_problem_results.items():
            strategy_results[s_name][pid] = correct

    print(f"\n{'='*60}")
    print("EVALUATION COMPLETE")
    print(f"{'='*60}\n")

    # Compute stats
    stats = comparison.compute_per_strategy_stats(strategy_results)
    problem_ids = [p["id"] for p in problems]
    win_matrix = comparison.build_win_matrix(strategy_results, problem_ids)

    return {
        "strategy_results": dict(strategy_results),
        "stats": stats,
        "win_matrix": win_matrix,
        "problem_ids": problem_ids,
        "total_problems": total,
    }


def run_demo(strategies: List[str], problem: Dict):
    """Run one example problem with all strategies and show outputs."""
    print(f"\n{'='*60}")
    print(f"DEMO: Single Example with All Strategies")
    print(f"{'='*60}")
    print(f"Problem ({problem['id']}): {problem['problem']}")
    print(f"Ground Truth: {problem['answer']}")
    print(f"{'='*60}\n")

    for s_name in strategies:
        strat_cls = STRATEGY_REGISTRY[s_name]
        strategy = strat_cls()
        print(f"\n--- {s_name.upper()} ---")
        trace = strategy.solve(
            problem=problem["problem"],
            problem_id=problem["id"],
            ground_truth=problem["answer"],
        )
        correct = exact_match(trace.final_answer, problem["answer"])
        trace.is_correct = correct
        print(f"Raw answer: {trace.final_answer}")
        print(f"Correct: {correct}")
        print(f"Events: {len(trace.events)}")
        for ev in trace.events[-3:]:
            print(f"  [{ev.step_type}] → {str(ev.outputs)[:80]}")

        # Show tree for ToT
        if s_name == "tot" and trace.extra.get("tree_log"):
            print(f"\n  Search tree log:")
            for depth_log in trace.extra["tree_log"]:
                print(f"    Depth {depth_log['depth']}: {depth_log['num_candidates']} candidates")
                for node in depth_log["selected"][:3]:
                    print(f"      Step: {node['step'][:50]} | Score: {node['score']} | Result: {node['result']}")


def run_judge_sanity():
    """Run LLM judge sanity check on 8+ examples."""
    print("\n=== LLM Judge Sanity Check ===\n")
    judge = LLMJudge()
    problems = load_golden_set()

    # Take first 8 problems and create pseudo-predictions
    # Mix of correct and incorrect answers to test judge
    examples = []
    human_labels = []

    for i, p in enumerate(problems[:10]):
        # Create a known correct answer
        examples.append({
            "id": p["id"],
            "problem": p["problem"],
            "predicted": p["answer"],
            "ground_truth": p["answer"],
        })
        human_labels.append("CORRECT")

        # Create a slightly wrong answer
        import random
        wrong_ans = str(int(p["answer"]) + random.randint(1, 10))
        examples.append({
            "id": f"{p['id']}_wrong",
            "problem": p["problem"],
            "predicted": wrong_ans,
            "ground_truth": p["answer"],
        })
        human_labels.append("INCORRECT")

        if len(examples) >= 16:
            break

    result = judge.sanity_check(examples[:16], human_labels[:16])
    print(f"Judge-Human Agreement: {result['agreement_rate']:.1%}")
    print(f"Matches: {result['matches']}/{result['total']}")
    print()

    for r in result["results"]:
        status = "✓" if r["agreement"] else "✗"
        print(f"  {status} {r['problem_id']}: human={r['human']}, judge={r['judge']} | ans={r['predicted']} (truth={r['ground_truth']})")

    return result


def print_full_report(eval_results: Dict):
    """Print the full evaluation report."""
    stats = eval_results["stats"]
    win_matrix = eval_results["win_matrix"]

    # Accuracy table with CIs
    print("\n" + "="*60)
    print("ACCURACY RESULTS (with 95% Confidence Intervals)")
    print("="*60)
    print(f"| {'Strategy':<20} | {'Correct':>8} | {'Total':>6} | {'Accuracy':>9} | {'Wilson 95% CI':<20} | {'Bootstrap 95% CI':<22} |")
    print(f"| {'-'*20} | {'-'*8} | {'-'*6} | {'-'*9} | {'-'*20} | {'-'*22} |")

    for name, s in sorted(stats.items()):
        w_lo, w_hi = s["wilson_ci"]
        b_lo, b_hi = s["bootstrap_ci"]
        print(f"| {name:<20} | {s['correct']:>8} | {s['total']:>6} | {s['accuracy']:>8.1%} | [{w_lo:.3f}, {w_hi:.3f}] | [{b_lo:.3f}, {b_hi:.3f}] |")

    # Win matrix
    print("\n" + "="*60)
    print("WIN MATRIX (Strategy × Strategy)")
    print("="*60)
    print(comparison.format_win_matrix_text(win_matrix))

    # Cost table
    print("\n" + "="*60)
    print("COST / LATENCY TABLE")
    print("="*60)
    cost_results = analyze_traces()
    if "error" not in cost_results:
        print(format_cost_table(cost_results))


def main():
    parser = argparse.ArgumentParser(description="Agentic Reasoning Lab — Eval Harness")
    parser.add_argument("--strategy", default=None, help="Run only one strategy (react, plan_execute, self_consistency, tot)")
    parser.add_argument("--demo", action="store_true", help="Run one example with all strategies")
    parser.add_argument("--record-baseline", action="store_true", help="Record current results as baseline")
    parser.add_argument("--delta", action="store_true", help="Show delta vs baseline")
    parser.add_argument("--judge-sanity", action="store_true", help="Run judge sanity check")
    parser.add_argument("--problems", type=int, default=0, help="Limit to first N problems")
    args = parser.parse_args()

    # Determine strategies to run
    if args.strategy:
        if args.strategy not in STRATEGY_REGISTRY:
            print(f"Unknown strategy: {args.strategy}. Available: {list(STRATEGY_REGISTRY.keys())}")
            sys.exit(1)
        strategies = [args.strategy]
    else:
        strategies = list(STRATEGY_REGISTRY.keys())

    # Load golden set
    problems = load_golden_set()
    if args.problems:
        problems = problems[:args.problems]

    # Judge sanity check
    if args.judge_sanity:
        run_judge_sanity()
        return

    # Demo mode
    if args.demo:
        run_demo(strategies, problems[0])
        return

    # Delta mode
    if args.delta:
        delta = compute_delta({})  # Need to load current stats first
        # For delta, we just load the baseline and compare
        from eval.baseline import load_baseline
        baseline = load_baseline()
        if baseline is None:
            print("No baseline found. Run with --record-baseline first.")
            return
        print(f"Baseline recorded: {baseline['timestamp']}")
        print()
        # We still need current stats, so run eval
        eval_results = run_eval(strategies, problems)
        stats = eval_results["stats"]
        delta = compute_delta(stats)
        print(format_delta_report(delta))
        return

    # Full eval run
    eval_results = run_eval(strategies, problems)

    # Record baseline if requested
    if args.record_baseline:
        record_baseline(eval_results["stats"])
        print("\nBaseline recorded to data/baselines/baseline.json")

    # Check delta
    delta = compute_delta(eval_results["stats"])
    if "error" not in delta:
        print(format_delta_report(delta))
        print()

    # Print full report
    print_full_report(eval_results)

    # Save trace analysis (failure taxonomy)
    print("\n" + "="*60)
    print("FAILURE TAXONOMY")
    print("="*60)
    all_traces = Tracer.get().load_traces()
    taxonomy = compute_failure_taxonomy(all_traces)
    for cat, count in sorted(taxonomy.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()