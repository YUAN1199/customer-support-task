import asyncio
import re

# ------------------------------------------------------------------------------
# 1. Prompt Chaining – 3-step sequential pipeline
# ------------------------------------------------------------------------------
def preprocess_user_message(text):
    """Step 1: Clean and normalize input"""
    text = re.sub(r'\s+', ' ', text).strip()
    return f"Cleaned message: {text}"

def classify_ticket(cleaned_text):
    """Step 2: Classify ticket type"""
    if any(w in cleaned_text.lower() for w in ["broken", "error", "crash", "not working"]):
        return "technical"
    elif any(w in cleaned_text.lower() for w in ["bill", "refund", "charge", "payment"]):
        return "billing"
    elif any(w in cleaned_text.lower() for w in ["complain", "worse", "terrible", "escalate"]):
        return "complaint"
    else:
        return "general"

def generate_draft_response(category, cleaned_text):
    """Step 3: Generate draft based on category"""
    if category == "technical":
        return "Draft: Please restart your app and check for updates."
    elif category == "billing":
        return "Draft: We will review your payment and refund request."
    elif category == "complaint":
        return "Draft: We apologize for the bad experience."
    else:
        return "Draft: Thank you for your question! We will assist you shortly."

# ------------------------------------------------------------------------------
# 2. Routing – Dynamic branching logic
# ------------------------------------------------------------------------------
def route_ticket(category):
    print(f"\n--- Routing to branch: {category.upper()} ---")
    return category

# ------------------------------------------------------------------------------
# 3. Parallelization – Async concurrent tasks
# ------------------------------------------------------------------------------
async def analyze_sentiment(text):
    await asyncio.sleep(0.5)
    return "Sentiment: Negative (frustrated user)"

async def extract_keywords(text):
    await asyncio.sleep(0.5)
    return "Keywords: app, issue, problem"

async def run_parallel_tasks(text):
    print("\n--- Starting parallel tasks ---")
    sentiment, keywords = await asyncio.gather(
        analyze_sentiment(text),
        extract_keywords(text)
    )
    print("✅ Parallel tasks completed")
    return sentiment, keywords

# ------------------------------------------------------------------------------
# 4. Reflection – Self-evaluation loop (2 iterations)
# ------------------------------------------------------------------------------
def reflect_and_improve(draft):
    print("\n--- Reflection Loop ---")
    print(f"Original draft:\n{draft}")

    critique = "Critique: Too short, not empathetic enough."
    print(f"\nEvaluation: {critique}")

    improved = draft + " We understand your frustration and will respond within 4 hours."
    print(f"\nImproved version:\n{improved}")
    return improved

# ------------------------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------------------------
async def support_pipeline(user_input):
    print("=" * 60)
    print("Starting Customer Support Ticket Processor")
    print("=" * 60)

    # Step 1: Prompt Chaining
    cleaned = preprocess_user_message(user_input)
    category = classify_ticket(cleaned)
    draft = generate_draft_response(category, cleaned)

    print("\n--- Prompt Chaining Completed ---")
    print(f"Category: {category}")

    # Step 2: Routing
    route_ticket(category)

    # Step 3: Parallel tasks
    sentiment, keywords = await run_parallel_tasks(user_input)
    print(sentiment)
    print(keywords)

    # Step 4: Reflection
    final_response = reflect_and_improve(draft)

    print("\n" + "=" * 60)
    print("FINAL RESPONSE:")
    print(final_response)
    print("=" * 60)

# ------------------------------------------------------------------------------
# RUN
# ------------------------------------------------------------------------------
if __name__ == "__main__":
     test_input = input("Please enter your customer support question: ")
    asyncio.run(support_pipeline(test_input))
