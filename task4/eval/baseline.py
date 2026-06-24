"""Baseline recording and diff tool.

Records accuracy numbers to data/baselines/baseline.json so future
runs can be diff'd against them. Supports make eval delta reporting.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict
from pathlib import Path


BASELINE_DIR = Path(__file__).parent.parent / "data" / "baselines"
BASELINE_FILE = BASELINE_DIR / "baseline.json"


def record_baseline(stats: Dict[str, Dict]) -> bool:
    """Save current accuracy stats as the baseline.

    Args:
        stats: Per-strategy stats from comparison.compute_per_strategy_stats().

    Returns:
        True if baseline was created/overwritten successfully.
    """
    os.makedirs(BASELINE_DIR, exist_ok=True)

    baseline = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strategies": {},
    }

    for name, s in stats.items():
        baseline["strategies"][name] = {
            "accuracy": s["accuracy"],
            "wilson_ci": list(s["wilson_ci"]),
            "bootstrap_ci": list(s["bootstrap_ci"]),
            "correct": s["correct"],
            "total": s["total"],
        }

    with open(BASELINE_FILE, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)

    return True


def load_baseline() -> Dict | None:
    """Load the saved baseline, or None if not found."""
    if not BASELINE_FILE.exists():
        return None
    with open(BASELINE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_delta(current_stats: Dict[str, Dict]) -> Dict:
    """Compute the delta between current stats and the saved baseline.

    Returns:
        Dict with per-strategy accuracy deltas.
    """
    baseline = load_baseline()
    if baseline is None:
        return {"error": "No baseline found. Run with --record-baseline first.", "deltas": {}}

    deltas = {}
    for name, s in current_stats.items():
        if name in baseline["strategies"]:
            prev = baseline["strategies"][name]["accuracy"]
            curr = s["accuracy"]
            delta = curr - prev
            deltas[name] = {
                "previous": prev,
                "current": curr,
                "delta": delta,
                "delta_pct": delta * 100,
            }
        else:
            deltas[name] = {
                "previous": None,
                "current": s["accuracy"],
                "delta": None,
                "delta_pct": None,
                "note": "New strategy (not in baseline)",
            }

    return {
        "baseline_timestamp": baseline.get("timestamp", "unknown"),
        "deltas": deltas,
    }


def format_delta_report(delta: Dict) -> str:
    """Format the delta report as a readable string."""
    lines = ["## Baseline Delta Report", ""]

    if "error" in delta:
        lines.append(f"**{delta['error']}**")
        return "\n".join(lines)

    lines.append(f"Baseline timestamp: {delta['baseline_timestamp']}")
    lines.append("")
    lines.append("| Strategy | Previous | Current | Delta | % |")
    lines.append("| --- | --- | --- | --- | --- |")

    for name, d in delta["deltas"].items():
        prev_s = f"{d['previous']:.3f}" if d['previous'] is not None else "N/A"
        curr_s = f"{d['current']:.3f}"
        delta_s = f"{d['delta']:+.3f}" if d['delta'] is not None else "N/A"
        pct_s = f"{d['delta_pct']:+.1f}%" if d['delta_pct'] is not None else "N/A"
        lines.append(f"| {name} | {prev_s} | {curr_s} | {delta_s} | {pct_s} |")

    return "\n".join(lines)