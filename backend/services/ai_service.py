"""AI service with OpenAI-compatible API and realistic mock fallbacks."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

import httpx

from config import get_settings
from utils.text_utils import (
    ESCALATION_KEYWORDS,
    FRUSTRATED_KEYWORDS,
    HIGH_KEYWORDS,
    NEGATIVE_KEYWORDS,
    POSITIVE_KEYWORDS,
    URGENT_KEYWORDS,
    contains_any,
    detect_category,
    extract_matched_keywords,
    normalize_text,
    priority_explanation,
    truncate,
)

logger = logging.getLogger(__name__)
settings = get_settings()

PRIORITY_RANK = {"Low": 0, "Medium": 1, "High": 2, "Urgent": 3}


def _has_api_key() -> bool:
    return bool(settings.openai_api_key and settings.openai_api_key.strip())


def _chat_completion(messages: list[dict[str, str]], temperature: float = 0.4) -> Optional[str]:
    if not _has_api_key():
        return None
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{settings.openai_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.chat_model,
                    "messages": messages,
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning("Chat completion failed; using mock fallback: %s", exc)
        return None


def _parse_json(content: Optional[str]) -> Optional[dict]:
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _rule_based_sentiment(text: str) -> str:
    if contains_any(text, FRUSTRATED_KEYWORDS):
        return "Frustrated"
    if contains_any(text, POSITIVE_KEYWORDS) and not contains_any(text, NEGATIVE_KEYWORDS + ESCALATION_KEYWORDS):
        return "Positive"
    if contains_any(text, NEGATIVE_KEYWORDS) or contains_any(text, ESCALATION_KEYWORDS):
        return "Negative"
    return "Neutral"


def _rule_based_priority(text: str, sentiment: str) -> tuple[str, list[str]]:
    lowered = normalize_text(text)
    urgent_hits = extract_matched_keywords(text, URGENT_KEYWORDS)
    high_hits = extract_matched_keywords(text, HIGH_KEYWORDS)

    # Refund + angry/frustrated language elevates to Urgent
    if "refund" in lowered and sentiment in ("Frustrated", "Negative"):
        urgent_hits = list(dict.fromkeys([*urgent_hits, "refund anger"]))

    if sentiment == "Frustrated" or urgent_hits:
        return "Urgent", urgent_hits or ["frustrated customer"]
    if high_hits or sentiment == "Negative":
        return "High", high_hits or ["negative sentiment"]
    if any(k in lowered for k in ["feature request", "feature", "how do", "what is your", "quick question"]):
        return "Low", ["general / feature"]
    return "Medium", ["standard issue"]


def _rule_based_escalation(text: str, sentiment: str, priority: str) -> tuple[bool, str, str]:
    matches = extract_matched_keywords(text, ESCALATION_KEYWORDS)
    lowered = normalize_text(text)
    escalate = priority in ("Urgent", "High") or sentiment == "Frustrated" or bool(matches)

    team = "Manager"
    if any(k in lowered for k in ["refund", "payment", "charge", "invoice", "billing"]):
        team = "Billing"
    elif any(k in lowered for k in ["security", "breach", "hacked", "fraud", "gdpr", "data leak"]):
        team = "Security"
    elif any(k in lowered for k in ["bug", "error", "login", "not working", "api", "webhook", "crash"]):
        team = "Technical"
    elif "feature" in lowered:
        team = "Product"

    if escalate:
        reason_parts = [f"{priority} priority", f"{sentiment} sentiment"]
        if matches:
            reason_parts.append(f"keywords: {', '.join(matches[:4])}")
        reason = "Escalate — " + "; ".join(reason_parts) + f". Route to {team}."
    else:
        reason = "No escalation needed — issue can be handled by a frontline agent with policy guidance."
    return escalate, reason, team


def generate_mock_ticket_analysis(ticket_data: dict[str, Any]) -> dict[str, Any]:
    text = f"{ticket_data.get('subject', '')} {ticket_data.get('message', '')}"
    sentiment = _rule_based_sentiment(text)
    priority, priority_hits = _rule_based_priority(text, sentiment)
    category = detect_category(text)
    escalate, esc_reason, team = _rule_based_escalation(text, sentiment, priority)
    key_issue = truncate(ticket_data.get("message", ""), 160)

    intent_map = {
        "Billing": "Resolve billing, refund, or payment concern",
        "Technical Issue": "Restore a blocked technical workflow",
        "Account": "Regain or manage account access",
        "Feature Request": "Request a product enhancement",
        "Bug Report": "Report a reproducible product defect",
        "General Question": "Clarify a product or policy question",
    }
    tone = "Apologetic" if sentiment in ("Frustrated", "Negative") else "Professional"
    if priority == "Urgent" or sentiment == "Frustrated":
        tone = "Empathetic"

    risk = {
        "Urgent": "Critical",
        "High": "High",
        "Medium": "Medium",
        "Low": "Low",
    }[priority]

    if escalate:
        next_action = (
            f"Contact the customer within SLA, apply {team} runbook, "
            f"and document the first response with an approved AI draft."
        )
    else:
        next_action = (
            f"Reply with a clear next step using the recommended {tone} tone, "
            "cite policy if needed, then update ticket status."
        )

    return {
        "summary": truncate(
            f"{ticket_data.get('customer_name', 'Customer')} needs help with "
            f"“{ticket_data.get('subject', 'a support issue')}”. "
            f"Primary category: {category}. Key concern: {key_issue}",
            340,
        ),
        "customer_intent": intent_map.get(category, "Seek support resolution"),
        "sentiment": sentiment,
        "priority": priority,
        "priority_reason": priority_explanation(priority, priority_hits, sentiment),
        "category": category,
        "escalate": escalate,
        "escalation_reason": esc_reason,
        "recommended_team": team,
        "suggested_reply_tone": tone,
        "key_issue": key_issue,
        "risk_level": risk,
        "suggested_next_action": next_action,
        "confidence": 0.86 if escalate or sentiment != "Neutral" else 0.76,
        "source": "mock_rules",
    }


def _merge_with_rules(parsed: dict, mock: dict) -> dict:
    """Keep LLM wording, but never under-classify critical tickets."""
    merged = {**mock, **parsed}
    if PRIORITY_RANK.get(mock["priority"], 0) > PRIORITY_RANK.get(str(merged.get("priority")), 0):
        merged["priority"] = mock["priority"]
        merged["priority_reason"] = mock.get("priority_reason")
    if mock["sentiment"] == "Frustrated":
        merged["sentiment"] = "Frustrated"
    if mock["escalate"]:
        merged["escalate"] = True
        merged["escalation_reason"] = mock.get("escalation_reason") or merged.get("escalation_reason")
        merged["recommended_team"] = mock.get("recommended_team") or merged.get("recommended_team")
    merged.setdefault("priority_reason", mock.get("priority_reason"))
    merged.setdefault("suggested_next_action", mock.get("suggested_next_action"))
    merged.setdefault("confidence", 0.8)
    return merged


def analyze_ticket(ticket_data: dict[str, Any], business_settings: Optional[dict] = None) -> dict[str, Any]:
    mock = generate_mock_ticket_analysis(ticket_data)
    business_name = (business_settings or {}).get("business_name", "our company")
    prompt = f"""You are a senior customer support AI analyst for {business_name}.
Analyze this support ticket and return JSON with keys:
summary, customer_intent, sentiment, priority, priority_reason, category, escalate, escalation_reason,
recommended_team, suggested_reply_tone, key_issue, risk_level, suggested_next_action, confidence.

Rules:
- sentiment: Positive | Neutral | Negative | Frustrated
- priority: Low | Medium | High | Urgent
  Urgent = legal, security, cancellation, refund anger, payment failure affecting business
  High = repeated issue, major bug, blocked customer
  Medium = standard account/technical issue
  Low = general question or feature request
- category: Billing | Technical Issue | Account | Feature Request | Bug Report | General Question
- escalate true for cancellation, legal, security, payment failure, angry/frustrated customers, repeated failures
- recommended_team: Billing | Technical | Manager | Security | Product
- priority_reason must explain why that priority was chosen
- suggested_next_action must be concrete for an agent
- confidence 0-1

Ticket:
Customer: {ticket_data.get('customer_name')}
Email: {ticket_data.get('customer_email')}
Company: {ticket_data.get('company')}
Subject: {ticket_data.get('subject')}
Message: {ticket_data.get('message')}
"""
    raw = _chat_completion(
        [
            {"role": "system", "content": "You are a precise customer support analysis engine. Return valid JSON only."},
            {"role": "user", "content": prompt},
        ]
    )
    parsed = _parse_json(raw)
    if not parsed:
        return mock
    result = _merge_with_rules(parsed, mock)
    result["source"] = "openai"
    return result


def generate_mock_reply(
    ticket_data: dict[str, Any],
    tone: str = "Professional",
    analysis_data: Optional[dict] = None,
    retrieved_context: Optional[list[dict]] = None,
) -> str:
    name = ticket_data.get("customer_name", "there").split()[0]
    subject = ticket_data.get("subject", "your request")
    analysis = analysis_data or generate_mock_ticket_analysis(ticket_data)
    sentiment = analysis.get("sentiment", "Neutral")
    escalate = analysis.get("escalate", False)
    team = analysis.get("recommended_team", "Manager")
    key_issue = analysis.get("key_issue") or ticket_data.get("message", "")[:120]
    category = analysis.get("category", "General Question")

    policy_block = ""
    if retrieved_context:
        top = retrieved_context[0]
        snippet = truncate(top.get("content") or "", 280)
        title = top.get("document_title") or "our knowledge base"
        policy_block = f"According to our {title}: {snippet}"
    else:
        policy_block = (
            "I reviewed your request against our support playbooks. "
            "If a specific policy clause applies, I will confirm it in a follow-up."
        )

    tone_openers = {
        "Professional": f"Hello {name},\n\nThank you for contacting support regarding {subject}.",
        "Friendly": f"Hi {name},\n\nThanks so much for reaching out about {subject} — happy to help.",
        "Empathetic": f"Hello {name},\n\nI'm sorry you've run into this with {subject}. I understand how disruptive this can be.",
        "Concise": f"Hi {name},\n\nThanks for your message about {subject}.",
        "Technical": f"Hello {name},\n\nThanks for the details on {subject}. I've reviewed the issue report.",
        "Apologetic": f"Hello {name},\n\nI sincerely apologize for the trouble with {subject}.",
    }
    opener = tone_openers.get(tone, tone_openers["Professional"])

    if sentiment in ("Frustrated", "Negative"):
        ack = f"I understand your frustration regarding: {truncate(key_issue, 140)}."
    else:
        ack = f"I've reviewed your request: {truncate(key_issue, 140)}."

    solutions = {
        "Billing": "Next step: I will verify the billing record and outline refund, credit, or correction options within one business day.",
        "Technical Issue": "Next step: please retry after a refresh/session reset and share timestamps plus any error codes so we can reproduce quickly.",
        "Account": "Next step: we can restore access securely — confirm the account email and whether recovery methods are available.",
        "Feature Request": "Next step: I've logged this as a product request with your use case for roadmap review.",
        "Bug Report": "Next step: this looks like a product defect. We'll escalate to engineering with your steps and prioritize an update.",
        "General Question": "Next step: here is the clearest guidance based on your question and our support policy.",
    }
    solution = f"{policy_block}\n\n{solutions.get(category, solutions['General Question'])}"

    escalation_note = ""
    if escalate:
        escalation_note = (
            f"\n\nBecause of the urgency, I'm escalating this to our {team} team "
            "so a specialist can follow up promptly."
        )

    closings = {
        "Professional": "Please reply with any additional details so we can resolve this quickly.\n\nBest regards,\nSupport Team",
        "Friendly": "Reply anytime with more details — we've got you.\n\nWarm regards,\nSupport Team",
        "Empathetic": "We'll stay with this until it's resolved. Thank you for your patience.\n\nKind regards,\nSupport Team",
        "Concise": "Reply if you need anything else.\n\nRegards,\nSupport Team",
        "Technical": "Share logs or error payloads if available and we'll continue triage.\n\nRegards,\nSupport Engineering",
        "Apologetic": "Again, sorry for the inconvenience — we appreciate your patience.\n\nSincerely,\nSupport Team",
    }
    return f"{opener}\n\n{ack}\n\n{solution}{escalation_note}\n\n{closings.get(tone, closings['Professional'])}"


def generate_reply(
    ticket_data: dict[str, Any],
    analysis_data: Optional[dict] = None,
    tone: str = "Professional",
    retrieved_context: Optional[list[dict]] = None,
) -> dict[str, Any]:
    mock_reply = generate_mock_reply(ticket_data, tone, analysis_data, retrieved_context)
    insufficient = not retrieved_context
    context_block = "\n\n".join(
        f"[{c.get('document_title', 'KB')}] {c.get('content', '')[:500]}" for c in (retrieved_context or [])[:4]
    )
    prompt = f"""Write a customer support reply in a {tone} tone.
Include: greeting, acknowledgment, clear next step, empathy matching sentiment, escalation note if needed, short closing.
Use knowledge base context when relevant. Do not invent policy facts outside context.
If context is missing, say you will confirm the exact policy shortly while still giving a useful next step.
Return JSON: {{"reply": "...", "used_context": true/false, "insufficient_context": true/false}}

Ticket subject: {ticket_data.get('subject')}
Customer: {ticket_data.get('customer_name')}
Message: {ticket_data.get('message')}
Analysis: {json.dumps(analysis_data or {})}
Knowledge base context:
{context_block or 'None'}
"""
    raw = _chat_completion(
        [
            {"role": "system", "content": "You write business-ready customer support replies. Return JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )
    parsed = _parse_json(raw)
    reply = (parsed or {}).get("reply") or mock_reply
    return {
        "reply": reply,
        "tone": tone,
        "citations": retrieved_context or [],
        "used_context": bool(retrieved_context) if not parsed else bool(parsed.get("used_context", bool(retrieved_context))),
        "insufficient_context": insufficient if not parsed else bool(parsed.get("insufficient_context", insufficient)),
        "source": "openai" if parsed else "mock",
    }


def generate_escalation_recommendation(
    ticket_data: dict[str, Any],
    analysis_data: Optional[dict] = None,
    sla_risk: bool = False,
    overdue: bool = False,
) -> dict[str, Any]:
    analysis = analysis_data or generate_mock_ticket_analysis(ticket_data)
    escalate = bool(analysis.get("escalate"))
    reason = analysis.get("escalation_reason") or "Review required."
    team = analysis.get("recommended_team") or "Manager"
    text = f"{ticket_data.get('subject', '')} {ticket_data.get('message', '')}"

    if ticket_data.get("status") == "Pending" or overdue or sla_risk:
        escalate = True
        if overdue:
            reason = (reason or "") + " Ticket is overdue for first response SLA."
            team = team or "Manager"
        elif sla_risk:
            reason = (reason or "") + " Ticket is approaching SLA breach (risk threshold)."
        elif ticket_data.get("status") == "Pending":
            reason = (reason or "") + " Ticket has been pending and may exceed SLA."

    if float(analysis.get("confidence", 1) or 1) < 0.55:
        escalate = True
        reason += " AI confidence is low; human review recommended."

    internal_note = (
        f"Priority={analysis.get('priority')}; Sentiment={analysis.get('sentiment')}; "
        f"Key issue={truncate(analysis.get('key_issue') or text, 180)}. "
        f"Suggested action: {analysis.get('suggested_next_action')}"
    )
    return {
        "escalate": escalate,
        "escalation_reason": reason.strip(),
        "recommended_team": team,
        "suggested_internal_note": internal_note,
        "confidence": analysis.get("confidence", 0.75),
    }


def generate_mock_support_answer(question: str, context: Optional[list[dict]] = None) -> dict[str, Any]:
    context = context or []
    if context:
        top = context[0]
        answer = (
            f"Based on **{top.get('document_title', 'our knowledge base')}**:\n\n"
            f"{top.get('content', '')[:700]}\n\n"
            "**Recommended agent action:** confirm the customer's scenario, follow the policy steps above, "
            "and document the outcome on the ticket.\n\n"
            "Citations used are listed in the panel so you can quote the exact policy language."
        )
        return {"answer": answer, "citations": context, "insufficient_context": False}

    q = normalize_text(question)
    if "refund" in q:
        answer = (
            "I don't have a matching indexed document for this yet, but the standard refund playbook is:\n"
            "1) verify purchase date and eligibility,\n"
            "2) confirm billing method,\n"
            "3) process eligible refunds within SLA,\n"
            "4) notify the customer with a clear timeline.\n\n"
            "Upload your Refund Policy to the knowledge base for stronger citations."
        )
    elif "payment" in q or "failed" in q:
        answer = (
            "No exact knowledge base hit was found. Standard failed-payment triage:\n"
            "verify card details, try an alternate method, check processor decline codes, "
            "and offer temporary access while Billing investigates."
        )
    elif "login" in q:
        answer = (
            "No indexed login article matched strongly. Standard steps:\n"
            "password reset, verify email ownership, check MFA/SSO, escalate to Technical if lockouts persist."
        )
    elif "cancel" in q:
        answer = (
            "No cancellation article matched strongly. Standard process:\n"
            "confirm identity, offer retention once, process cancellation on request, "
            "confirm end date/proration, send written confirmation, escalate if legal/angry."
        )
    else:
        answer = (
            "I couldn't find a strong knowledge base match for that question yet.\n"
            "Use standard triage: clarify the issue, check ticket history, apply SLA by priority, "
            "and escalate if risk is high. Consider uploading a policy doc covering this topic."
        )
    return {"answer": answer, "citations": [], "insufficient_context": True}


def answer_support_question(question: str, retrieved_context: Optional[list[dict]] = None) -> dict[str, Any]:
    mock = generate_mock_support_answer(question, retrieved_context)
    context_block = "\n\n".join(
        f"Source: {c.get('document_title')}\n{c.get('content', '')[:600]}" for c in (retrieved_context or [])[:5]
    )
    prompt = f"""Answer this internal support agent question using the knowledge base context.
Be actionable and policy-accurate. If context is insufficient, say what is missing and give a safe interim playbook.
Return JSON: {{"answer": "...", "insufficient_context": true/false}}

Question: {question}

Context:
{context_block or 'No context'}
"""
    raw = _chat_completion(
        [
            {"role": "system", "content": "You are an internal support copilot. Return JSON only."},
            {"role": "user", "content": prompt},
        ]
    )
    parsed = _parse_json(raw)
    if not parsed or not parsed.get("answer"):
        return mock
    return {
        "answer": parsed["answer"],
        "citations": retrieved_context or [],
        "insufficient_context": bool(parsed.get("insufficient_context", not retrieved_context)),
        "source": "openai",
    }


def generate_mock_recommendations(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    urgent = [t for t in tickets if t.get("priority") == "Urgent" or t.get("sentiment") == "Frustrated"]
    neg = [t for t in tickets if t.get("sentiment") in ("Negative", "Frustrated")]
    categories: dict[str, int] = {}
    for t in tickets:
        categories[t.get("category", "General Question")] = categories.get(t.get("category", "General Question"), 0) + 1
    top_category = max(categories, key=categories.get) if categories else "General Question"
    return [
        {
            "title": "Clear the urgent queue within the 1-hour SLA",
            "description": f"{len(urgent)} tickets are urgent or show frustrated sentiment. Assign senior agents and send first responses before the SLA clock breaches.",
            "category": "Urgency",
            "priority": "Urgent",
            "action_items": ["Open escalations inbox", "Assign senior agents", "Use Empathetic reply tone templates"],
        },
        {
            "title": "Protect at-risk customers",
            "description": f"{len(neg)} customers show negative/frustrated tone. Prioritize retention language and manager escalation where cancellation risk exists.",
            "category": "Retention",
            "priority": "High",
            "action_items": ["Flag cancellation keywords", "Offer policy-compliant goodwill options"],
        },
        {
            "title": f"Create macros for recurring {top_category} issues",
            "description": f"Most tickets currently fall under {top_category}. Ship a shared macro and a dedicated knowledge base article to cut handle time.",
            "category": "Knowledge Gaps",
            "priority": "Medium",
            "action_items": [f"Draft KB article for {top_category}", "Add macros for top 3 intents"],
        },
        {
            "title": "Close knowledge gaps on refunds, payments, and login",
            "description": "Agents still ask about refunds, failed payments, login recovery, and cancellations. Keep each policy indexed and cited in AI replies.",
            "category": "Knowledge Gaps",
            "priority": "High",
            "action_items": ["Upload refund policy", "Upload payment troubleshooting guide", "Verify vector indexing"],
        },
        {
            "title": "Keep the human approval workflow tight",
            "description": "Require Approve before Mark as Sent. Use Empathetic/Apologetic tones for frustrated customers and attach KB citations on every draft.",
            "category": "Quality",
            "priority": "Medium",
            "action_items": ["Require approval before send", "Audit last 20 AI replies"],
        },
        {
            "title": "Route escalations by specialty team",
            "description": "Send billing/payment failures to Billing, security/legal to Security, and product defects to Technical/Product with internal notes.",
            "category": "Escalation Routing",
            "priority": "High",
            "action_items": ["Review open escalations", "Confirm default escalation team in Settings"],
        },
    ]


def generate_support_recommendations(
    tickets: list[dict[str, Any]],
    analytics: Optional[dict] = None,
    business_settings: Optional[dict] = None,
) -> list[dict[str, Any]]:
    mock = generate_mock_recommendations(tickets)
    prompt = f"""Generate exactly 6 actionable support operations recommendations as JSON:
{{"recommendations":[{{"title":"","description":"","category":"","priority":"","action_items":[]}}]}}
Focus on urgency, retention risk, recurring issues, KB gaps, reply quality, escalation routing.
Business: {(business_settings or {}).get('business_name', 'Acme')}
Analytics: {json.dumps(analytics or {})[:2000]}
Ticket sample: {json.dumps(tickets[:12])[:3000]}
"""
    raw = _chat_completion(
        [
            {"role": "system", "content": "You are a support operations strategist. Return JSON only."},
            {"role": "user", "content": prompt},
        ]
    )
    parsed = _parse_json(raw)
    recs = (parsed or {}).get("recommendations")
    if isinstance(recs, list) and recs:
        return recs[:6]
    return mock
