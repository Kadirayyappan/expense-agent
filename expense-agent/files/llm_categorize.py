"""
PHASE 2 - Step A: Categorization using Google's Gemini API.

Why this matters: the old version (categorize.py) only works for merchants
you hardcoded. This version can categorize ANY merchant name correctly,
because it actually understands language - that's the "AI" part.
"""

import os
from google import genai
from dotenv import load_dotenv

load_dotenv()  # reads your .env file and loads GEMINI_API_KEY

# The client automatically picks up GEMINI_API_KEY from your environment
client = genai.Client()

MODEL_NAME = "gemini-3.5-flash-lite"  # current fast/cheap model as of late 2026

VALID_CATEGORIES = ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Other"]


def categorize_with_llm(merchant: str) -> str:
    """Ask Gemini to categorize a single merchant name."""
    prompt = f"""Classify this merchant into exactly ONE of these categories:
{", ".join(VALID_CATEGORIES)}

Merchant: "{merchant}"

Reply with ONLY the category name, nothing else."""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    category = response.text.strip()

    # Safety check: if the LLM returns something unexpected, fall back to "Other"
    if category not in VALID_CATEGORIES:
        return "Other"
    return category


def categorize_batch(merchants: list[str]) -> dict[str, str]:
    """
    IMPORTANT: Categorizing one-by-one is slow and costs more API calls.
    This sends ALL unique merchants in ONE request instead - much cheaper/faster.
    Returns a dict like {"Swiggy": "Food", "Uber": "Transport"}
    """
    unique_merchants = list(set(merchants))

    prompt = f"""Classify each merchant below into exactly ONE category from this list:
{", ".join(VALID_CATEGORIES)}

Merchants:
{chr(10).join(unique_merchants)}

Reply in this EXACT format, one per line, nothing else:
MerchantName: Category"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    result_text = response.text.strip()

    # Parse the "MerchantName: Category" lines into a dictionary
    mapping = {}
    for line in result_text.split("\n"):
        if ":" in line:
            merchant, category = line.split(":", 1)
            merchant = merchant.strip()
            category = category.strip()
            mapping[merchant] = category if category in VALID_CATEGORIES else "Other"

    return mapping


if __name__ == "__main__":
    # Quick test
    test_merchants = ["Starbucks", "IRCTC", "Cred", "Decathlon"]
    result = categorize_batch(test_merchants)
    for merchant, category in result.items():
        print(f"{merchant} -> {category}")
