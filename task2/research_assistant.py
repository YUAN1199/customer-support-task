import asyncio
import time
import random
import json
import re

# ------------------------------------------------------------------------------
# 1. ROUTING: Domain Supervisor (LLM-based)
# ------------------------------------------------------------------------------
def route_domain_llm(query):
    query = query.lower().strip()

    # Guardrail: 拒绝注入/恶意输入
    if any(x in query for x in ["ignore previous", "forget instructions", "system prompt", "password"]):
        return "fallback"

    # LLM-style classification (模拟真实LLM路由)
    if any(w in query for w in ["battery", "science", "research", "data", "technical", "solid-state"]):
        return "scientific"
    elif any(w in query for w in ["history", "war", "empire", "century", "league"]):
        return "historical"
    elif any(w in query for w in ["debt", "financial", "market", "ebitda", "revenue"]):
        return "financial"
    elif len(query) < 10 or "?" not in query:
        return "fallback"
    else:
        return "general"

# ------------------------------------------------------------------------------
# 2. PARALLELIZATION: Map → Best-of-N → Reduce
# ------------------------------------------------------------------------------
async def subquestion_answer_candidate(subq):
    await asyncio.sleep(0.3)
    base = f"Answer: {subq[:50]}..."
    return base + " | FactScore: " + str(round(random.random() * 10, 1))

async def best_of_n(subq, n=3):
    tasks = [subquestion_answer_candidate(subq) for _ in range(n)]
    candidates = await asyncio.gather(*tasks)

    scored = []
    for c in candidates:
        score = round(random.uniform(5, 10), 1)
        scored.append((c, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    best, best_score = scored[0]
    return best, best_score, scored

async def map_reduce_parallel(query):
    start = time.time()

    subquestions = [
        f"Define core concepts in: {query[:60]}",
        f"Key evidence and findings for: {query[:60]}",
        f"Pros, cons, and challenges for: {query[:60]}"
    ]

    tasks = [best_of_n(sq) for sq in subquestions]
    results = await asyncio.gather(*tasks)

    best_answers = [r[0] for r in results]
    reduced = "\n".join([f"- {a}" for a in best_answers])

    parallel_time = round(time.time() - start, 2)
    seq_estimate = round(parallel_time * 3, 2)

    print(f"\n⏱ Parallel time: {parallel_time}s | Estimated sequential: {seq_estimate}s")
    return reduced, parallel_time

# ------------------------------------------------------------------------------
# 3. REFLECTION: Producer-Critic Loop (3+ iterations)
# ------------------------------------------------------------------------------
def critic_evaluation(draft):
    score = round(random.uniform(4, 8), 1)
    return {
        "total_score": score,
        "feedback": "Improve factual precision, clarity, and structure."
    }

def reflect_improve(draft, max_iter=3):
    print("\n=== REFLECTION LOOP START ===")
    current = draft
    scores = []
    for i in range(max_iter):
        crit = critic_evaluation(current)
        scores.append(crit["total_score"])
        print(f"Iter {i+1} | Score: {crit['total_score']} | Feedback: {crit['feedback']}")
        current = current + "\n[Improved] " + crit["feedback"]
    print("=== REFLECTION LOOP END ===")
    return current, scores

# ------------------------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------------------------
async def research_pipeline(query):
    print("=" * 70)
    print("DEEP RESEARCH ASSISTANT")
    print("=" * 70)

    # Step 1: Route
    domain = route_domain_llm(query)
    print(f"\n✅ Routed domain: {domain.upper()}")
    if domain == "fallback":
        print("❌ Query rejected (guardrail triggered)")
        return

    # Step 2: Map-Reduce + Best-of-N
    draft, _time = await map_reduce_parallel(query)
    print("\n=== DRAFT RESEARCH BRIEF ===")
    print(draft)

    # Step 3: Reflection
    final, scores = reflect_improve(draft)

    print("\n" + "=" * 70)
    print("FINAL RESEARCH BRIEF")
    print("=" * 70)
    print(final)
    print(f"\nScore history: {scores}")

# ------------------------------------------------------------------------------
# RUN
# ------------------------------------------------------------------------------
if __name__ == "__main__":
   test_query = input("Please enter your research question: ")
    asyncio.run(research_pipeline(test_query))
