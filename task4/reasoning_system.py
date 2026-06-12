
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
