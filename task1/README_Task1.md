# Task 1: Foundation Patterns
## Automated Customer Support Ticket Processor
This task implements an end-to-end automated customer support system using four core LLM pipeline patterns covered in the course:

## Implemented Patterns
### 1. Prompt Chaining
- Step 1: Query preprocessing & cleaning
- Step 2: Intent classification
- Step 3: Dynamic response generation

### 2. Dynamic Routing
- Technical support
- Billing & refund inquiries
- Complaints & escalation
- General information
- Fallback for out-of-scope / ambiguous questions

### 3. Parallelization
- Concurrent sub-task execution using `asyncio.gather()`
- Parallel sentiment analysis and keyword extraction

### 4. Producer–Critic Reflection Loop
- Producer: Generates a draft response
- Critic: Evaluates clarity, politeness, completeness, and tone
- Before/after output comparison

---

## How to Run
```bash
python task1/support_system.py

Example Input
My app is not working. What should I do?
Example Output
Please enter your customer support question: My app is not working. What should I do?============================================================Starting Customer Support Ticket Processor============================================================
--- Prompt Chaining Completed ---Category: technical
--- Routing to branch: TECHNICAL ---
--- Starting parallel tasks ---✅ Parallel tasks completedSentiment: Negative (frustrated user)Keywords: app, issue, problem
--- Reflection Loop ---Original draft:Draft: Please restart your app and check for updates.
Evaluation: Critique: Too short, not empathetic enough.
Improved version:Draft: Please restart your app and check for updates. We understand your frustration and will respond within 4 hours.
============================================================FINAL RESPONSE:Draft: Please restart your app and check for updates. We understand your frustration and will respond within 4 hours.
- Final customer response
