"""Retrieval evaluation: Recall@5 and MRR on a hand-labeled set of 8+ queries.

Each labeled query maps to the chunk IDs that SHOULD be retrieved.
We compute Recall@5 (how many relevant chunks appear in top-5 results)
and MRR (Mean Reciprocal Rank of the first relevant chunk).
"""

import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from rag.retrieval import HybridRetriever, ScoredChunk


# ======================================================================
# Labeled Query Set (8+ questions with expected chunk IDs)
# ======================================================================

LABELED_QUERIES: List[Dict] = [
    {
        "query": "What are the password requirements at AcmeCorp?",
        "relevant_chunks": [
            "CORP-1_chunk3",  # Password policy - Password Requirements section
            "CORP-1_chunk4",  # Password policy - MFA section
        ],
    },
    {
        "query": "How do I set up my development environment?",
        "relevant_chunks": [
            "CORP-10_chunk24",  # Development Environment Setup
            "CORP-10_chunk25",  # Required tools section
        ],
    },
    {
        "query": "What is the vacation policy for managers vs interns?",
        "relevant_chunks": [
            "CORP-3_chunk8",  # Vacation policy with tier table
        ],
    },
    {
        "query": "How do I deploy an application to Kubernetes?",
        "relevant_chunks": [
            "CORP-9_chunk21",  # Deploying to Kubernetes main content
            "CORP-9_chunk22",  # K8s deployment manifest section
        ],
    },
    {
        "query": "Tell me about the performance review cycle and rating scale",
        "relevant_chunks": [
            "CORP-8_chunk19",  # Performance Review Policy
            "CORP-8_chunk20",  # Rating scale section
        ],
    },
    {
        "query": "What security training is required for new hires?",
        "relevant_chunks": [
            "CORP-20_chunk47",  # Security Awareness Training
        ],
    },
    {
        "query": "How are incidents handled at P1 severity?",
        "relevant_chunks": [
            "CORP-12_chunk28",  # Incident Response Plan - severity levels
            "CORP-12_chunk29",  # Response process
        ],
    },
    {
        "query": "What's the company policy on expense reimbursement for international travel?",
        "relevant_chunks": [
            "CORP-4_chunk10",  # Expense Policy - travel section
        ],
    },
    {
        "query": "How does Istio service mesh authorization work?",
        "relevant_chunks": [
            "CORP-15_chunk34",  # Istio Service Mesh config
            "CORP-15_chunk35",  # Authorization policies section
        ],
    },
    {
        "query": "What are all the office locations and addresses?",
        "relevant_chunks": [
            "CORP-17_chunk39",  # Welcome - office locations table
        ],
    },
]


@dataclass
class EvalResult:
    """Results for a single evaluation run."""
    query: str
    retrieved_ids: List[str]
    relevant_ids: List[str]
    recall5: float
    reciprocal_rank: float
    num_retrieved: int


class RetrievalEvaluator:
    """Runs retrieval evaluation and reports metrics."""

    def __init__(self, retriever: HybridRetriever, top_k: int = 5):
        self.retriever = retriever
        self.top_k = top_k

    def _compute_recall_at_k(
        self, retrieved_ids: List[str], relevant_ids: List[str], k: int = 5
    ) -> float:
        """Compute Recall@k: proportion of relevant chunks found in top-k results."""
        if not relevant_ids:
            return 0.0
        top_k_ids = set(retrieved_ids[:k])
        relevant_set = set(relevant_ids)
        intersection = top_k_ids & relevant_set
        return len(intersection) / len(relevant_set)

    def _compute_reciprocal_rank(
        self, retrieved_ids: List[str], relevant_ids: List[str]
    ) -> float:
        """Compute Reciprocal Rank: 1 / rank of first relevant chunk."""
        relevant_set = set(relevant_ids)
        for rank, rid in enumerate(retrieved_ids, 1):
            if rid in relevant_set:
                return 1.0 / rank
        return 0.0

    def evaluate_single(self, query_data: Dict) -> EvalResult:
        """Evaluate a single labeled query."""
        query = query_data["query"]
        relevant_ids = query_data["relevant_chunks"]

        t0 = time.time()
        scored_chunks = self.retriever.retrieve(
            query=query,
            top_k=self.top_k,
            user_role="employee",
        )

        retrieved_ids = [sc.chunk.chunk_id for sc in scored_chunks]
        recall5 = self._compute_recall_at_k(retrieved_ids, relevant_ids, k=5)
        rr = self._compute_reciprocal_rank(retrieved_ids, relevant_ids)

        return EvalResult(
            query=query,
            retrieved_ids=retrieved_ids,
            relevant_ids=relevant_ids,
            recall5=recall5,
            reciprocal_rank=rr,
            num_retrieved=len(retrieved_ids),
        )

    def evaluate_all(self) -> List[EvalResult]:
        """Run evaluation on all labeled queries."""
        results = []
        print("\n" + "=" * 70)
        print("RETRIEVAL EVALUATION")
        print("=" * 70)
        for i, qd in enumerate(LABELED_QUERIES, 1):
            print(f"\n[{i}/{len(LABELED_QUERIES)}] Query: {qd['query'][:80]}...")
            result = self.evaluate_single(qd)
            results.append(result)
            print(f"  Relevant: {result.relevant_ids}")
            print(f"  Retrieved: {result.retrieved_ids}")
            print(f"  Recall@5: {result.recall5:.2f}")
            print(f"  Reciprocal Rank: {result.reciprocal_rank:.3f}")
        return results

    def report_summary(self, results: List[EvalResult]) -> Dict:
        """Compute aggregate metrics and return as dict."""
        if not results:
            return {}

        avg_recall5 = sum(r.recall5 for r in results) / len(results)
        avg_mrr = sum(r.reciprocal_rank for r in results) / len(results)

        print("\n" + "-" * 70)
        print("SUMMARY METRICS")
        print("-" * 70)
        print(f"  Number of queries: {len(results)}")
        print(f"  Average Recall@5:  {avg_recall5:.3f}")
        print(f"  Average MRR:       {avg_mrr:.3f}")
        print("-" * 70 + "\n")

        return {
            "num_queries": len(results),
            "recall_at_5": round(avg_recall5, 3),
            "mrr": round(avg_mrr, 3),
        }