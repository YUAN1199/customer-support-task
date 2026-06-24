"""Programmatic evaluation metrics for the Agentic Reasoning Lab.

For GSM8K-style math word problems we use numerical-exact-match:
we normalize both the predicted and ground-truth answers to comparable
numeric values and compare with tolerance.
"""

import re
import math
from fractions import Fraction
from typing import Optional, Tuple


def _normalize(answer: str) -> Optional[str]:
    """Normalize an answer string to a canonical numeric form.

    Handles:
      - Plain numbers: "18", "3", "70000"
      - Dollar amounts: "$18", "18 dollars"
      - Fractions: "1/4", "1/2"
      - Decimals: "0.25", "30.0"
      - Percentages: "50%"
      - Time: "12:00 PM"
      - Units: "540 meters", "15 gallons"
      - Comma-separated thousands: "1,150"

    Returns a string that can be compared for exact match,
    or None if normalization fails.
    """
    if not answer or not isinstance(answer, str):
        return None

    cleaned = answer.strip()

    # Try to extract numeric value
    # Remove currency symbols and commas
    cleaned_no_dollar = cleaned.replace("$", "").replace(",", "").strip()

    # Handle time format like "12:00 PM" or "12:00PM"
    time_match = re.match(
        r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?", cleaned_no_dollar
    )
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        ampm = (time_match.group(3) or "").upper()
        return f"{hour:02d}:{minute:02d} {ampm}".strip() if ampm else f"{hour:02d}:{minute:02d}"

    # Try fraction like "1/4"
    frac_match = re.match(r"^(-?\d+)/(\d+)$", cleaned_no_dollar)
    if frac_match:
        num = int(frac_match.group(1))
        den = int(frac_match.group(2))
        if den != 0:
            f = Fraction(num, den)
            # Return as decimal string for comparison
            return str(float(f))

    # Try percentage
    pct_match = re.match(r"^(-?[\d.]+)\s*%$", cleaned_no_dollar)
    if pct_match:
        return pct_match.group(1)

    # Try to extract just the number (first numeric sequence)
    num_match = re.search(r"-?[\d.]+", cleaned_no_dollar)
    if num_match:
        try:
            value = float(num_match.group(0))
            # If it's an integer, format as such
            if value == int(value):
                return str(int(value))
            return str(value)
        except ValueError:
            pass

    # Fallback: return as-is
    return cleaned.lower()


def _numbers_equal(a: str, b: str, tolerance: float = 1e-6) -> bool:
    """Check if two normalized answer strings represent the same number."""
    if a == b:
        return True
    try:
        fa = float(a)
        fb = float(b)
        return abs(fa - fb) < tolerance
    except ValueError:
        return False


def exact_match(predicted: str, ground_truth: str) -> bool:
    """Numerical-exact-match for math word problems.

    Normalizes both strings and compares.  For GSM8K this works well because
    answers are always numeric (numbers, dollar amounts, fractions, percentages).
    """
    norm_pred = _normalize(predicted)
    norm_gt = _normalize(ground_truth)

    if norm_pred is None or norm_gt is None:
        return predicted.strip().lower() == ground_truth.strip().lower()

    return _numbers_equal(norm_pred, norm_gt)


def passes_k(results: list[bool], k: int = 1) -> bool:
    """Pass@k: True if at least one of the k results is correct."""
    return any(results[:k])