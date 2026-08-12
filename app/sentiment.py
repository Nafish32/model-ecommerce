"""Rule-based sentiment. ponytail: keyword lexicon, deterministic, zero deps.
Swap classify() for VADER or the LLM if accuracy on real reviews falls short."""

POSITIVE = {
    "love", "loved", "great", "excellent", "perfect", "amazing", "awesome",
    "good", "happy", "best", "comfortable", "fast", "recommend", "recommended",
    "quality", "works", "nice", "fantastic", "satisfied", "durable", "worth",
    "wonderful", "pleased", "impressed", "solid", "reliable", "beautiful",
}
NEGATIVE = {
    "bad", "poor", "terrible", "awful", "broke", "broken", "disappointed",
    "disappointing", "waste", "slow", "hate", "hated", "worst", "defective",
    "cheaply", "stopped", "uncomfortable", "flimsy", "useless", "annoying",
    "return", "returned", "refund", "faulty", "overpriced", "junk",
}


def classify(text: str) -> str:
    words = {w.strip(".,!?;:'\"()").lower() for w in text.split()}
    pos = len(words & POSITIVE)
    neg = len(words & NEGATIVE)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def demo():
    assert classify("I love this, works great and great quality") == "positive"
    assert classify("terrible, broke in a week, waste of money") == "negative"
    assert classify("it is a mug") == "neutral"
    print("sentiment demo OK")


if __name__ == "__main__":
    demo()
