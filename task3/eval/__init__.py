"""Evaluation module: retrieval metrics and red-team testing."""

from eval.retrieval_eval import RetrievalEvaluator, LabeledQuery
from eval.red_team import RedTeamTester, AdversarialPrompt

__all__ = [
    "RetrievalEvaluator",
    "LabeledQuery",
    "RedTeamTester",
    "AdversarialPrompt",
]