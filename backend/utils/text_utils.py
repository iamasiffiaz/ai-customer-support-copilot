"""Support-ticket text heuristics for hybrid AI analysis."""

from __future__ import annotations

import re
from typing import Iterable


URGENT_KEYWORDS = [
    "cancel",
    "cancellation",
    "legal",
    "lawyer",
    "attorney",
    "lawsuit",
    "security",
    "breach",
    "hacked",
    "fraud",
    "data leak",
    "gdpr",
    "payment failed",
    "failed payment",
    "charged twice",
    "enterprise",
    "business operations",
]

HIGH_KEYWORDS = [
    "repeated",
    "again",
    "still not",
    "third time",
    "second time",
    "blocked",
    "can't work",
    "cannot work",
    "can't login",
    "cannot login",
    "major bug",
    "production",
    "outage",
    "locked",
]

ESCALATION_KEYWORDS = [
    *URGENT_KEYWORDS,
    "refund",
    "angry",
    "furious",
    "unacceptable",
    "outraged",
    "threat",
    "attorney",
]

FRUSTRATED_KEYWORDS = [
    "frustrated",
    "angry",
    "ridiculous",
    "worst",
    "hate",
    "furious",
    "unacceptable",
    "terrible",
    "useless",
    "fed up",
    "outraged",
    "this is absurd",
    "absolutely unacceptable",
]

NEGATIVE_KEYWORDS = [
    "problem",
    "issue",
    "not working",
    "broken",
    "error",
    "failed",
    "disappointed",
    "unhappy",
    "can't",
    "cannot",
    "unable",
    "bug",
    "crash",
]

POSITIVE_KEYWORDS = [
    "thank",
    "thanks",
    "great",
    "love",
    "appreciate",
    "awesome",
    "helpful",
    "excellent",
    "perfect",
    "resolved",
]

CATEGORY_PATTERNS = {
    "Billing": [r"refund", r"invoice", r"payment", r"charge", r"billing", r"subscription.*cost", r"prorat"],
    "Technical Issue": [r"bug", r"error", r"crash", r"not working", r"timeout", r"api", r"integration", r"webhook"],
    "Account": [r"login", r"password", r"account", r"access", r"2fa", r"sign.?in", r"mfa", r"sso"],
    "Feature Request": [r"feature", r"request", r"would be nice", r"suggestion", r"roadmap", r"can you add"],
    "Bug Report": [r"bug", r"reproduce", r"stack trace", r"exception", r"broken", r"regression"],
    "General Question": [r"how do", r"what is", r"question", r"help me understand", r"policy"],
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    lowered = normalize_text(text)
    return any(k.lower() in lowered for k in keywords)


def extract_matched_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    lowered = normalize_text(text)
    return [k for k in keywords if k.lower() in lowered]


def detect_category(text: str) -> str:
    lowered = normalize_text(text)
    scores: dict[str, int] = {}
    for category, patterns in CATEGORY_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, lowered))
        if score:
            scores[category] = score
    if not scores:
        return "General Question"
    return max(scores, key=scores.get)


def truncate(text: str, max_len: int = 280) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def priority_explanation(priority: str, matches: list[str], sentiment: str) -> str:
    signals = ", ".join(matches[:4]) if matches else "tone and issue type"
    mapping = {
        "Urgent": f"Marked Urgent because of high-risk signals ({signals}) and/or {sentiment.lower()} customer tone.",
        "High": f"Marked High due to customer impact signals ({signals}) that block work or indicate a repeating failure.",
        "Medium": "Marked Medium as a standard support issue that needs a clear next step within SLA.",
        "Low": "Marked Low as a general question or non-blocking feature request.",
    }
    return mapping.get(priority, "Priority derived from hybrid rules + analysis.")
