"""Pairwise comparison, win matrix, and confidence intervals.

Produces a strategy × strategy win matrix and per-strategy
accuracy with 95% bootstrap confidence intervals.
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict


def wilson_confidence_interval(correct: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score confidence interval for a proportion.

    Args:
        correct: Number of correct answers.
        total: Total number of problems.
        z: Z-score for the confidence level (1.96 for 95%).

    Returns:
        (lower_bound, upper_bound) as proportions in [0, 1].
    """
    if total == 0:
        return 0.0, 0.0

    p = correct / total
    denominator = 1 + z ** 2 / total
    center = (p + z ** 2 / (2 * total)) / denominator
    margin = z * np.sqrt((p * (1 - p) + z ** 2 / (4 * total)) / total) / denominator
    return max(0, center - margin), min(1, center + margin)


def bootstrap_confidence_interval(
    outcomes: List[bool], n_bootstrap: int = 1000, confidence: float = 0.95
) -> Tuple[float, float]:
    """Bootstrap confidence interval for accuracy.

    Args:
        outcomes: List of bools (True=correct, False=incorrect).
        n_bootstrap: Number of bootstrap samples.
        confidence: Confidence level (e.g., 0.95).

    Returns:
        (lower_bound, upper_bound) as proportions.
    """
    if not outcomes:
        return 0.0, 0.0

    outcomes = np.array(outcomes, dtype=float)
    n = len(outcomes)
    means = []
    rng = np.random.RandomState(42)
    for _ in range(n_bootstrap):
        sample = rng.choice(outcomes, size=n, replace=True)
        means.append(sample.mean())
    means = np.array(means)

    alpha = (1 - confidence) / 2
    lower = np.percentile(means, alpha * 100)
    upper = np.percentile(means, (1 - alpha) * 100)
    return float(lower), float(upper)


def build_win_matrix(
    strategy_results: Dict[str, Dict[str, bool]],
    problem_ids: List[str],
) -> Dict[str, Dict[str, Dict]]:
    """Build a strategy × strategy win matrix.

    For each pair (A, B), counts:
      - A_wins: problems where A was correct and B was incorrect
      - B_wins: problems where B was correct and A was incorrect
      - ties_correct: both correct
      - ties_incorrect: both incorrect

    Returns nested dict: result[A][B] = {"A_wins": N, "B_wins": N, "ties_correct": N, "ties_incorrect": N}
    """
    strategy_names = list(strategy_results.keys())
    matrix = {}

    for a in strategy_names:
        matrix[a] = {}
        for b in strategy_names:
            if a == b:
                matrix[a][b] = {"A_wins": 0, "B_wins": 0, "ties_correct": 0, "ties_incorrect": 0, "same": True}
                continue

            a_wins = 0
            b_wins = 0
            ties_correct = 0
            ties_incorrect = 0

            for pid in problem_ids:
                a_correct = strategy_results[a].get(pid, False)
                b_correct = strategy_results[b].get(pid, False)

                if a_correct and not b_correct:
                    a_wins += 1
                elif b_correct and not a_correct:
                    b_wins += 1
                elif a_correct and b_correct:
                    ties_correct += 1
                else:
                    ties_incorrect += 1

            matrix[a][b] = {
                "A_wins": a_wins,
                "B_wins": b_wins,
                "ties_correct": ties_correct,
                "ties_incorrect": ties_incorrect,
            }

    return matrix


def compute_per_strategy_stats(
    strategy_results: Dict[str, Dict[str, bool]],
) -> Dict[str, Dict]:
    """Compute accuracy, 95% CI (Wilson and bootstrap) per strategy.

    Returns:
        Dict[str, {"accuracy": float, "wilson_ci": (lo, hi), "bootstrap_ci": (lo, hi), "correct": int, "total": int}]
    """
    stats = {}
    for name, results in strategy_results.items():
        outcomes = list(results.values())
        correct = sum(outcomes)
        total = len(outcomes)

        wilson_ci = wilson_confidence_interval(correct, total)
        boot_ci = bootstrap_confidence_interval(outcomes)

        stats[name] = {
            "accuracy": correct / total if total > 0 else 0.0,
            "wilson_ci": wilson_ci,
            "bootstrap_ci": boot_ci,
            "correct": correct,
            "total": total,
        }

    return stats


def format_win_matrix_text(matrix: Dict[str, Dict[str, Dict]]) -> str:
    """Format the win matrix as a readable Markdown table."""
    strategies = list(matrix.keys())
    n = len(strategies)

    lines = []
    # Header
    header = "| Strategy | " + " | ".join(strategies) + " |"
    sep = "|" + "---|" * (n + 1)
    lines.append(header)
    lines.append(sep)

    for a in strategies:
        row = f"| {a} | "
        cells = []
        for b in strategies:
            entry = matrix[a][b]
            if a == b:
                cells.append("—")
            else:
                cells.append(f"W:{entry['A_wins']} L:{entry['B_wins']} T:{entry['ties_correct']+entry['ties_incorrect']}")
        row += " | ".join(cells) + " |"
        lines.append(row)

    return "\n".join(lines)