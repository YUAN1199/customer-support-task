"""LLM-as-Judge for cases where programmatic match is too brittle.

For GSM8K we primarily use numerical-exact-match, but the judge provides
a second opinion and is useful for free-form answers or sanity-checking.

Implements judge-human agreement sanity check per requirements.
"""

import json
import re
from typing import List, Dict, Tuple, Optional

from llm_client import chat
from config import CONFIG
from eval.metrics import exact_match


JUDGE_PROMPT = """You are an impartial math answer evaluator.

Compare the student's answer to the ground truth answer.
Both are answers to the same math word problem.

Problem: {problem}
Ground Truth: {ground_truth}
Student Answer: {predicted}

Is the student's answer correct? Consider:
- Are they numerically equivalent? (e.g., "18" = "$18" = "18 dollars")
- If it's a fraction, is it equivalent? (e.g., "1/4" = "0.25")
- If it's a percentage, is it equivalent? (e.g., "50" = "50%")
- Minor formatting differences are OK.

Answer with EXACTLY one word: CORRECT or INCORRECT
"""


class LLMJudge:
    """LLM-based judge for math answer evaluation."""

    def __init__(self, model: str = None):
        self.model = model or CONFIG.judge_model
        self._agreement_cache: List[Dict] = []

    def judge(self, problem: str, predicted: str, ground_truth: str) -> dict:
        """Return dict with 'verdict' ('CORRECT'/'INCORRECT') and 'confidence'."""
        prompt = JUDGE_PROMPT.format(
            problem=problem,
            ground_truth=ground_truth,
            predicted=predicted,
        )
        resp = chat(
            [{"role": "user", "content": prompt}],
            model=self.model,
            temperature=0.0,
            max_tokens=16,
        )
        verdict_text = resp["content"].strip().upper()
        if "CORRECT" in verdict_text:
            verdict = "CORRECT"
        elif "INCORRECT" in verdict_text:
            verdict = "INCORRECT"
        else:
            verdict = "INCORRECT"

        return {
            "verdict": verdict,
            "raw_response": resp["content"],
            "input_tokens": resp["input_tokens"],
            "output_tokens": resp["output_tokens"],
            "latency_ms": resp["latency_ms"],
        }

    def sanity_check(
        self, examples: List[Dict], human_labels: List[str]
    ) -> Dict:
        """Compute judge-human agreement.

        Args:
            examples: List of dicts with keys 'problem', 'predicted', 'ground_truth'.
            human_labels: List of 'CORRECT'/'INCORRECT' labels from human.

        Returns:
            Dict with agreement metrics.
        """
        matches = 0
        results = []
        for i, (ex, human) in enumerate(zip(examples, human_labels)):
            judge_result = self.judge(
                ex["problem"], ex["predicted"], ex["ground_truth"]
            )
            agreement = judge_result["verdict"] == human.upper()
            if agreement:
                matches += 1
            results.append({
                "problem_id": ex.get("id", i),
                "problem": ex["problem"],
                "predicted": ex["predicted"],
                "ground_truth": ex["ground_truth"],
                "human": human,
                "judge": judge_result["verdict"],
                "agreement": agreement,
            })

        agreement_rate = matches / len(examples) if examples else 0
        return {
            "agreement_rate": agreement_rate,
            "matches": matches,
            "total": len(examples),
            "results": results,
        }