"""Shared calculator tool used by all reasoning strategies.

Implements a safe evaluator that handles basic arithmetic expressions.
This is a deterministic tool so comparisons between strategies are fair.
"""

import re
import math
from typing import Dict, Any


def calculator(expression: str) -> Dict[str, Any]:
    """Evaluate a mathematical expression safely.

    Allowed: numbers, +, -, *, /, //, %, **, parentheses, math.sqrt, math.pow,
             math.sin, math.cos, math.tan, math.log, math.log10, math.exp, math.pi, math.e, abs,
             round, sum, min, max.

    Args:
        expression: A string like "3 * (4 + 5)" or "sqrt(144)".

    Returns:
        {"result": value, "error": None} or {"result": None, "error": "message"}.
    """
    # Parse comma-separated expressions for batch evaluation
    expressions = [e.strip() for e in expression.split(";") if e.strip()]
    results = []

    for expr in expressions:
        try:
            # Basic safety: only allow safe characters
            if not re.match(r'^[\d\s+\-*/%().,^<>=!&|sqrtadighnpwoeicxSbR]+$', expr):
                return {"result": None, "error": f"Disallowed characters in: {expr}"}

            # Replace ^ with ** for exponentiation
            expr_clean = expr.replace("^", "**")

            # Build safe namespace
            safe_names = {
                "sqrt": math.sqrt,
                "pow": math.pow,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
                "abs": abs,
                "round": round,
                "sum": sum,
                "min": min,
                "max": max,
                "int": int,
                "float": float,
            }

            result = eval(expr_clean, {"__builtins__": {}}, safe_names)

            # Format numbers nicely
            if isinstance(result, float):
                if abs(result) < 1e-10:
                    result = 0.0
                elif abs(result - round(result)) < 1e-10:
                    result = int(round(result))
                else:
                    result = round(result, 6)

            results.append(str(result))
        except Exception as e:
            return {"result": None, "error": f"Error evaluating '{expr}': {str(e)}"}

    return {"result": " ; ".join(results), "error": None}


# For direct inline computation (used by Program-of-Thought style strategies)
def safe_eval(expression: str) -> str:
    """Evaluate and return just the result string."""
    res = calculator(expression)
    if res["error"]:
        return f"ERROR: {res['error']}"
    return res["result"]