import json
import random
import time
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any
from collections import Counter

# ==========================================
# ==========================================
class CalculatorTool:
    @staticmethod
    def calculate(expression: str) -> str:
        try:
            return str(eval(expression))
        except:
            return "error"

# ==========================================
# ==========================================
@dataclass
class ReasonTrace:
    problem_id: str
    strategy: str
    steps: List[Dict[str, Any]]
    final_answer: str
    correct: bool
    tokens_in: int
    tokens_out: int
    latency: float
    timestamp: float

class BaseReasonStrategy(ABC):
    name: str

    @abstractmethod
    def solve(self, problem: str, problem_id: str) -> ReasonTrace:
        pass

# ==========================================
# ==========================================
class ReAct(BaseReasonStrategy):
    name = "ReAct"

    def __init__(self):
        self.calc = CalculatorTool()

    def solve(self, problem: str, problem_id: str) -> ReasonTrace:
        start = time.time()
        steps = []
        steps.append({"step": "think", "content": "I need to compute 20 + 27"})
        steps.append({"step": "act", "content": "calculate(20+27)"})
        res = self.calc.calculate("20+27")
        steps.append({"step": "observe", "content": res})
        answer = random.choice(["47", "48", "47"])
        return ReasonTrace(
            problem_id=problem_id, strategy=self.name, steps=steps,
            final_answer=answer, correct=answer == "47",
            tokens_in=190, tokens_out=75, latency=time.time() - start,
            timestamp=time.time()
        )

# ==========================================
# ==========================================
class PlanAndExecute(BaseReasonStrategy):
    name = "Plan-and-Execute"

    def __init__(self):
        self.calc = CalculatorTool()

    def solve(self, problem: str, problem_id: str) -> ReasonTrace:
        start = time.time()
        steps = []
        steps.append({"step": "plan", "content": ["1. Calculate 20+27", "2. Return result"]})
        res = self.calc.calculate("20+27")
        steps.append({"step": "execute", "content": res})
        answer = random.choice(["47", "49", "47"])
        return ReasonTrace(
            problem_id=problem_id, strategy=self.name, steps=steps,
            final_answer=answer, correct=answer == "47",
            tokens_in=230, tokens_out=95, latency=time.time() - start,
            timestamp=time.time()
        )

# ==========================================
# ==========================================
class SelfConsistency(BaseReasonStrategy):
    name = "Self-Consistency"

    def __init__(self, n=4):
        self.n = n

    def solve(self, problem: str, problem_id: str) -> ReasonTrace:
        start = time.time()
        paths = [random.choice(["47", "48", "47"]) for _ in range(self.n)]
        answer = Counter(paths).most_common(1)[0][0]
        steps = [{"step": f"path_{i}", "content": p} for i, p in enumerate(paths)]
        return ReasonTrace(
            problem_id=problem_id, strategy=self.name, steps=steps,
            final_answer=answer, correct=answer == "47",
            tokens_in=400, tokens_out=170, latency=time.time() - start,
            timestamp=time.time()
        )

# ==========================================
# ==========================================
GOLDEN_DATASET = [
    {"id": f"q{i}", "problem": f"Question {i}: 20 + 27 = ?", "answer": "47"}
    for i in range(25)
]

# ==========================================
# ==========================================
def exact_match(pred: str, true: str) -> bool:
    return pred.strip() == true.strip()

def wilson_95(correct: int, total: int) -> tuple[float, float, float]:
    if total == 0:
        return 0.0, 0.0, 0.0
    p = correct / total
    z = 1.96
    denom = 1 + z ** 2 / total
    mid = (p + z ** 2 / (2 * total)) / denom
    margin = z * math.sqrt(p * (1 - p) / total + z ** 2 / (4 * total ** 2)) / denom
    return round(mid, 3), round(max(0, mid - margin), 3), round(min(1, mid + margin), 3)

def run_evaluation(strategies: List[BaseReasonStrategy]):
    results = {s.name: {"correct": 0, "total": 0, "traces": []} for s in strategies}

    for item in GOLDEN_DATASET:
        pid, prob, ans = item["id"], item["problem"], item["answer"]
        for strategy in strategies:
            trace = strategy.solve(prob, pid)
            trace.correct = exact_match(trace.final_answer, ans)
            if trace.correct:
                results[strategy.name]["correct"] += 1
            results[strategy.name]["total"] += 1
            results[strategy.name]["traces"].append(trace)

    print("\n===== Evaluation Results =====")
    for name, data in results.items():
        acc, low, high = wilson_95(data["correct"], data["total"])
        print(f"{name:20s} | acc={acc} | 95%CI=[{low},{high}]")

    print("\n===== Win Matrix =====")
    names = [s.name for s in strategies]
    for n1 in names:
        line = ""
        for n2 in names:
            if n1 == n2:
                line += "—  "
            else:
                line += "W  " if results[n1]["correct"] > results[n2]["correct"] else "L  "
        print(f"{n1:20s} | {line}")

    with open("baseline.json", "w", encoding="utf-8") as f:
        json.dump(results, f, default=lambda x: x.__dict__, indent=2, ensure_ascii=False)

    with open("traces.jsonl", "w", encoding="utf-8") as f:
        for s in strategies:
            for t in results[s.name]["traces"]:
                f.write(json.dumps(t.__dict__, ensure_ascii=False) + "\n")

    return results

# ==========================================
# ==========================================
def replay_problem(problem_id: str):
    print(f"\n===== Replay: {problem_id} =====")
    with open("traces.jsonl", encoding="utf-8") as f:
        for line in f:
            trace = json.loads(line)
            if trace["problem_id"] == problem_id:
                print(json.dumps(trace, indent=2, ensure_ascii=False))

# ==========================================
# ==========================================
if __name__ == "__main__":
    strategies = [ReAct(), PlanAndExecute(), SelfConsistency()]
    run_evaluation(strategies)
    replay_problem("q0")
