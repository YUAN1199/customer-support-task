Task 1: Foundation Patterns
Automated Customer Support Ticket Processor
This task implements an end-to-end automated customer support system using four core LLM pipeline patterns covered in the course:
Implemented Patterns
Prompt Chaining
Step 1: Query preprocessing & cleaning
Step 2: Intent classification
Step 3: Dynamic response generation
Dynamic Routing
Technical support
Billing & refund inquiries
Complaints & escalation
General information
Fallback for out-of-scope / ambiguous questions
Parallelization
Concurrent sub-task execution using asyncio.gather()
Parallel sentiment analysis and keyword extraction
Timing logs comparing parallel vs sequential execution
Producer–Critic Reflection Loop
Producer: Generates a draft response
Critic: Evaluates clarity, politeness, completeness, and tone
Two rounds of revision with measurable improvement
Before/after output comparison

### How to Run
```bash
python task1/support_system.py

### Example Input
My app is not working. What should I do?

### Example Output
The system shows a full pipeline log:
- Preprocessing result
- Classification and routing decision
- Parallel task results
- Reflection before/after comparison
- Final customer response
