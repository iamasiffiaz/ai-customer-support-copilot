"""Seed realistic demo data for AI Customer Support Copilot."""

from __future__ import annotations

from datetime import datetime, timedelta
import random

from database import SessionLocal, init_db, engine, Base
from models import (
    User,
    Ticket,
    TicketAnalysis,
    ReplyDraft,
    Escalation,
    KnowledgeBaseDocument,
    KnowledgeBaseChunk,
    Recommendation,
    AppSettings,
)
from routes.auth import hash_password
from services.chunking_service import chunk_text
from services.embedding_service import embed_texts
from services.vector_service import upsert_embeddings
from services.ai_service import generate_mock_ticket_analysis, generate_mock_reply

random.seed(42)


KB_DOCS = [
    {
        "title": "Refund Policy",
        "content": """Refund Policy
Customers may request a refund within 14 days of purchase for unused subscription periods.
Refunds are processed to the original payment method within 5–7 business days.
Partial month refunds are prorated for annual plans when cancellation is approved.
Charge disputes should be marked urgent and routed to Billing.
Agents must verify account ownership before issuing refunds.
Goodwill credits up to one month may be offered for service outages lasting over 24 hours.
""",
    },
    {
        "title": "Failed Payment Troubleshooting",
        "content": """Failed Payment Troubleshooting
Common causes: expired card, insufficient funds, bank decline, incorrect CVV, or 3DS failure.
Steps: 1) Ask customer to update payment method. 2) Retry charge after 15 minutes.
3) Offer temporary workspace access for up to 48 hours while billing investigates.
4) Escalate to Billing if payment fails three times or affects enterprise accounts.
Never store full card numbers in tickets. Document only last four digits and decline codes.
""",
    },
    {
        "title": "Account Login Issues",
        "content": """Account Login Issues
Guide customers through password reset using the registered email.
If MFA is enabled, verify recovery codes or send an authenticator reset after identity check.
Repeated lockouts after five failed attempts require a 30-minute cooldown or agent unlock.
SSO customers should confirm IdP configuration and certificate expiry.
Escalate to Technical if login works in one browser but fails persistently in others with API 401/403 errors.
""",
    },
    {
        "title": "Subscription Cancellation Process",
        "content": """Subscription Cancellation Process
Confirm identity and the subscription plan.
Present retention options once: pause for 30 days or switch to a lower plan.
If the customer still wants to cancel, process immediately and confirm end date.
Mention whether access continues until period end and whether refunds apply under Refund Policy.
Cancellation + angry language or legal threats should escalate to Manager.
Send written confirmation email after cancellation completes.
""",
    },
    {
        "title": "Data Security Policy",
        "content": """Data Security Policy
We encrypt data in transit (TLS) and at rest.
Suspicious access, account takeover, or breach claims are Security priority one.
Agents must not request passwords. Use secure reset flows only.
GDPR deletion requests are fulfilled within 30 days after verification.
For security incidents, escalate to Security with timestamps, IP hints, and affected accounts.
""",
    },
    {
        "title": "Bug Reporting Process",
        "content": """Bug Reporting Process
Collect: steps to reproduce, expected vs actual behavior, browser/OS, account ID, timestamps, screenshots.
Severity: Urgent for data loss/security; High for workflow blocked; Medium for partial degradation; Low for cosmetic.
Create engineering ticket references in the customer reply and set expectations for updates.
Regression bugs after releases should be tagged for Product and Technical jointly.
""",
    },
    {
        "title": "Feature Request Handling",
        "content": """Feature Request Handling
Thank the customer, clarify the use case and business impact, and log the request for Product review.
Do not promise timelines unless Product has published them.
If many customers request the same capability, recommend a knowledge base update with workarounds.
Feature requests are typically Low priority unless they unblock enterprise onboarding.
""",
    },
]


TICKET_SEEDS = [
    ("Ava Mitchell", "ava@northwind.io", "Northwind", "Payment failed on renewal", "Our company card payment failed again for the second time this week and the workspace is locked. This is unacceptable. We may cancel if not fixed today.", "Billing", "Open", "Urgent", "Frustrated"),
    ("Noah Patel", "noah@brightapps.co", "BrightApps", "Cannot login after password reset", "I reset my password but still cannot login. MFA keeps failing. Need access before standup.", "Account", "New", "High", "Negative"),
    ("Mia Chen", "mia@shoply.com", "Shoply", "Refund for annual plan", "I'd like a refund for our annual plan purchased 6 days ago. We chose the wrong tier.", "Billing", "Pending", "Medium", "Neutral"),
    ("Liam Brooks", "liam@orbit.dev", "Orbit", "API timeouts in production", "Our integration API calls are timing out intermittently since Friday. Customers are blocked from syncing orders.", "Technical Issue", "Open", "High", "Negative"),
    ("Emma Torres", "emma@harbor.ai", "Harbor AI", "Cancel subscription immediately", "Please cancel our subscription now. We are frustrated with repeated billing issues and considering legal options if charges continue.", "Billing", "Escalated", "Urgent", "Frustrated"),
    ("Oliver Hayes", "oliver@pixelcraft.io", "Pixelcraft", "Feature request: bulk ticket export", "Would love CSV export for tickets filtered by sentiment. Not urgent but useful for exec reporting.", "Feature Request", "New", "Low", "Positive"),
    ("Sophia Nguyen", "sophia@leafmail.com", "LeafMail", "Security concern - unusual login", "We saw login attempts from unknown IPs. Possible account compromise. Please investigate urgently.", "Account", "Escalated", "Urgent", "Negative"),
    ("Ethan Clark", "ethan@cubestore.com", "CubeStore", "Invoice shows double charge", "We were charged twice for March. Need a refund for the duplicate payment.", "Billing", "Open", "High", "Negative"),
    ("Isabella Reed", "isabella@tandemhq.com", "Tandem HQ", "Bug: dashboard charts blank", "Priority and sentiment charts on analytics render blank after filtering. Steps: open analytics, filter by Urgent.", "Bug Report", "Open", "Medium", "Neutral"),
    ("James Ortiz", "james@sunrise.fm", "Sunrise FM", "How do refunds work?", "Quick question: what is your refund window for monthly plans?", "General Question", "Resolved", "Low", "Positive"),
    ("Charlotte Kim", "charlotte@amberops.com", "AmberOps", "Repeated login failure", "This is the third time this month I cannot login. Reset emails arrive late. Very frustrated.", "Account", "Pending", "High", "Frustrated"),
    ("Benjamin Shaw", "ben@gridly.io", "Gridly", "Webhook signature validation failing", "Webhook signatures started failing after yesterday's deploy. Our ERP sync is broken.", "Technical Issue", "Open", "High", "Negative"),
    ("Amelia Foster", "amelia@nova.shop", "Nova Shop", "Need help changing support email", "We want to update the support email on our workspace settings. Where is that option?", "Account", "Resolved", "Low", "Positive"),
    ("Lucas Rivera", "lucas@bluekite.co", "BlueKite", "Cancellation + refund request", "We want to cancel and get a refund. Product didn't meet expectations and payment already failed once before.", "Billing", "Escalated", "Urgent", "Frustrated"),
    ("Harper Diaz", "harper@atelier.app", "Atelier", "Feature: Slack escalation alerts", "Please add Slack alerts when tickets escalate. Our managers miss email.", "Feature Request", "New", "Low", "Neutral"),
    ("Henry Morgan", "henry@quantix.ai", "Quantix", "Data deletion GDPR request", "Please delete all personal data for user id 44821 under GDPR. This is a legal compliance request.", "Account", "Escalated", "Urgent", "Neutral"),
    ("Evelyn Brooks", "evelyn@marketloop.com", "MarketLoop", "Failed payment enterprise account", "Enterprise payment failed and team seats are disabled. Affecting business operations today.", "Billing", "Open", "Urgent", "Frustrated"),
    ("Jack Wilson", "jack@cobaltops.com", "Cobalt Ops", "SSO certificate expired?", "Our SSO login stopped working. Suspect IdP certificate expiry. Need technical help.", "Technical Issue", "Pending", "High", "Negative"),
    ("Aria Bennett", "aria@flowstate.io", "FlowState", "Love the product, billing question", "Thanks for the great support last week! Quick question about switching from monthly to annual.", "Billing", "Resolved", "Low", "Positive"),
    ("Sebastian Cole", "seb@northpeak.dev", "Northpeak", "Bug report: reply editor loses draft", "Reply editor clears drafts after regenerate. Repro consistently on Chrome.", "Bug Report", "Open", "Medium", "Negative"),
    ("Scarlett Price", "scarlett@emberly.com", "Emberly", "Cannot access invoices", "Unable to download invoices from billing page - button does nothing.", "Billing", "New", "Medium", "Neutral"),
    ("Daniel Hayes", "daniel@stackyard.io", "Stackyard", "Angry about unresolved bug", "It's been two weeks and the sync bug is still broken. This is ridiculous. Fix it or we cancel.", "Bug Report", "Escalated", "Urgent", "Frustrated"),
    ("Grace Patel", "grace@meadowcrm.com", "Meadow CRM", "Password reset email not arriving", "My team is not receiving password reset emails. Checked spam. Need alternative unlock.", "Account", "Open", "High", "Negative"),
    ("Matthew Singh", "matt@orbitrail.com", "Orbit Rail", "What is cancellation process?", "How should I respond internally if a customer wants to cancel? Need policy steps.", "General Question", "Resolved", "Low", "Neutral"),
    ("Chloe Adams", "chloe@pinebatch.co", "Pinebatch", "Feature request: AI tone presets", "Can agents save preferred reply tones per queue? Friendly default for ecommerce.", "Feature Request", "Pending", "Low", "Positive"),
    ("Owen Turner", "owen@redline.tech", "Redline", "Security: leaked API key report", "Customer claims an API key may have leaked in a public gist. Need rotation guidance ASAP.", "Technical Issue", "Escalated", "Urgent", "Negative"),
    ("Lily Sanders", "lily@craftbar.com", "Craftbar", "Subscription pause option?", "Can we pause instead of cancel for 30 days while we migrate vendors?", "Billing", "New", "Medium", "Neutral"),
    ("Nathan Brook", "nathan@zenforce.io", "Zenforce", "Technical issue with mobile app crash", "App crashes on ticket detail for large message threads. Happens on iOS 18.", "Technical Issue", "Open", "Medium", "Negative"),
    ("Zoe Collins", "zoe@brightlane.co", "Brightlane", "Refund not received", "Refund was approved 8 days ago but money not in account. Getting frustrated.", "Billing", "Pending", "High", "Frustrated"),
    ("Caleb Morris", "caleb@datapike.ai", "Datapike", "General question on SLA", "What are first response SLAs for urgent vs high tickets?", "General Question", "Resolved", "Low", "Positive"),
    ("Nora Sullivan", "nora@harborops.com", "HarborOps", "Repeated payment failure", "Payment failed repeatedly and now account marked past due. Need escalation to billing manager.", "Billing", "Escalated", "Urgent", "Frustrated"),
    ("Ryan Fletcher", "ryan@shiftboard.app", "Shiftboard", "Bug: search filters ignore sentiment", "Inbox filters for Frustrated sentiment return all tickets. Blocking triage.", "Bug Report", "Open", "High", "Negative"),
    ("Hazel Ward", "hazel@copperdesk.com", "Copper Desk", "Account owner transfer", "Need to transfer workspace ownership after acquisition. What documents are required?", "Account", "Pending", "Medium", "Neutral"),
    ("Aaron Scott", "aaron@lumengrid.io", "LumenGrid", "Thank you for quick refund", "Refund processed perfectly. Appreciate the clear explanation from your agent.", "Billing", "Resolved", "Low", "Positive"),
    ("Penelope Ruiz", "penelope@softquay.com", "Softquay", "Legal complaint about terms", "Our counsel says auto-renew terms were unclear. Requesting contract review and possible cancellation with refund.", "Billing", "Escalated", "Urgent", "Negative"),
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        # wipe for clean demo
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()

        user = User(
            email="agent@supportcopilot.dev",
            full_name="Alex Morgan",
            role="agent",
            hashed_password=hash_password("demo1234"),
        )
        db.add(user)
        db.flush()

        settings = AppSettings(
            business_name="Support Copilot Demo",
            support_email="support@supportcopilot.dev",
            default_reply_tone="Professional",
            default_escalation_team="Manager",
        )
        db.add(settings)

        now = datetime.utcnow()
        tickets: list[Ticket] = []
        for i, row in enumerate(TICKET_SEEDS):
            name, email, company, subject, message, category, status, priority, sentiment = row
            created = now - timedelta(hours=random.randint(1, 240), minutes=random.randint(0, 59))
            first_resp = None
            resolved = None
            frt = None
            rest = None
            if status in ("Pending", "Resolved", "Escalated") and random.random() > 0.3:
                first_resp = created + timedelta(minutes=random.randint(15, 400))
                frt = (first_resp - created).total_seconds() / 60
            if status == "Resolved":
                resolved = (first_resp or created) + timedelta(hours=random.randint(2, 72))
                rest = (resolved - created).total_seconds() / 60
            ticket = Ticket(
                customer_name=name,
                customer_email=email,
                company=company,
                subject=subject,
                message=message,
                category=category,
                status=status,
                priority=priority,
                sentiment=sentiment,
                escalation_recommendation=status == "Escalated" or priority == "Urgent",
                assigned_agent_id=user.id if i % 2 == 0 else None,
                created_at=created,
                updated_at=created + timedelta(hours=random.randint(0, 48)),
                first_response_at=first_resp,
                resolved_at=resolved,
                first_response_time_minutes=frt,
                resolution_time_minutes=rest,
            )
            db.add(ticket)
            tickets.append(ticket)
        db.flush()

        # 15 analyses
        for ticket in tickets[:15]:
            analysis_data = generate_mock_ticket_analysis(
                {
                    "customer_name": ticket.customer_name,
                    "customer_email": ticket.customer_email,
                    "company": ticket.company,
                    "subject": ticket.subject,
                    "message": ticket.message,
                }
            )
            analysis = TicketAnalysis(
                ticket_id=ticket.id,
                summary=analysis_data["summary"],
                customer_intent=analysis_data["customer_intent"],
                sentiment=analysis_data["sentiment"],
                priority=analysis_data["priority"],
                category=analysis_data["category"],
                escalate=analysis_data["escalate"],
                escalation_reason=analysis_data["escalation_reason"],
                suggested_reply_tone=analysis_data["suggested_reply_tone"],
                key_issue=analysis_data["key_issue"],
                risk_level=analysis_data["risk_level"],
                suggested_next_action=analysis_data["suggested_next_action"],
                confidence=analysis_data["confidence"],
                raw_response=analysis_data,
            )
            ticket.ai_summary = analysis.summary
            ticket.sentiment = analysis.sentiment
            ticket.priority = analysis.priority
            ticket.category = analysis.category
            ticket.escalation_recommendation = analysis.escalate
            db.add(analysis)

        db.flush()

        # 12 reply drafts
        statuses = ["drafted", "edited", "approved", "sent", "drafted", "approved", "sent", "edited", "drafted", "approved", "sent", "drafted"]
        tones = ["Professional", "Empathetic", "Friendly", "Apologetic", "Concise", "Technical"]
        for i, ticket in enumerate(tickets[:12]):
            tone = tones[i % len(tones)]
            content = generate_mock_reply(
                {
                    "customer_name": ticket.customer_name,
                    "subject": ticket.subject,
                    "message": ticket.message,
                },
                tone=tone,
            )
            draft = ReplyDraft(
                ticket_id=ticket.id,
                agent_id=user.id,
                content=content,
                tone=tone,
                status=statuses[i],
                ai_generated=True,
                citations=[],
                approved_at=datetime.utcnow() if statuses[i] in ("approved", "sent") else None,
                sent_at=datetime.utcnow() if statuses[i] == "sent" else None,
            )
            ticket.ai_suggested_reply = content
            db.add(draft)

        # 8 escalations
        for ticket in [t for t in tickets if t.status == "Escalated" or t.priority == "Urgent"][:8]:
            db.add(
                Escalation(
                    ticket_id=ticket.id,
                    escalate=True,
                    reason=f"Escalated due to {ticket.priority} priority and {ticket.sentiment} sentiment on '{ticket.subject}'.",
                    recommended_team="Billing" if ticket.category == "Billing" else ("Security" if "security" in ticket.subject.lower() or "GDPR" in ticket.message else "Manager"),
                    internal_note=f"Review ticket #{ticket.id} and respond within SLA.",
                    status="open",
                )
            )

        # 5 KB documents (+ content has 7 topics; take first 5 for requirement, store all 7 for richness - user asked for 5 docs and 20 chunks)
        docs_to_use = KB_DOCS[:5]
        chunk_total = 0
        for doc_data in docs_to_use:
            doc = KnowledgeBaseDocument(
                title=doc_data["title"],
                filename=f"{doc_data['title'].lower().replace(' ', '_')}.txt",
                file_type="txt",
                content=doc_data["content"],
                status="indexed",
            )
            db.add(doc)
            db.flush()
            chunks = chunk_text(doc_data["content"], chunk_size=220, overlap=40)
            # ensure enough chunks overall
            vectors = embed_texts(chunks)
            points = []
            for idx, content in enumerate(chunks):
                chunk = KnowledgeBaseChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    content=content,
                    metadata_json={"title": doc.title},
                )
                db.add(chunk)
                db.flush()
                chunk.embedding_id = str(chunk.id)
                points.append(
                    {
                        "id": chunk.id,
                        "vector": vectors[idx],
                        "payload": {
                            "chunk_id": chunk.id,
                            "document_id": doc.id,
                            "document_title": doc.title,
                            "content": content,
                        },
                    }
                )
                chunk_total += 1
            if points:
                upsert_embeddings(points)
            doc.chunk_count = len(chunks)

        # If fewer than 20 chunks, add remaining KB docs
        if chunk_total < 20:
            for doc_data in KB_DOCS[5:]:
                doc = KnowledgeBaseDocument(
                    title=doc_data["title"],
                    filename=f"{doc_data['title'].lower().replace(' ', '_')}.txt",
                    file_type="txt",
                    content=doc_data["content"],
                    status="indexed",
                )
                db.add(doc)
                db.flush()
                chunks = chunk_text(doc_data["content"], chunk_size=200, overlap=30)
                vectors = embed_texts(chunks)
                points = []
                for idx, content in enumerate(chunks):
                    chunk = KnowledgeBaseChunk(
                        document_id=doc.id,
                        chunk_index=idx,
                        content=content,
                        metadata_json={"title": doc.title},
                    )
                    db.add(chunk)
                    db.flush()
                    chunk.embedding_id = str(chunk.id)
                    points.append(
                        {
                            "id": chunk.id,
                            "vector": vectors[idx],
                            "payload": {
                                "chunk_id": chunk.id,
                                "document_id": doc.id,
                                "document_title": doc.title,
                                "content": content,
                            },
                        }
                    )
                    chunk_total += 1
                if points:
                    upsert_embeddings(points)
                doc.chunk_count = len(chunks)
                if chunk_total >= 20:
                    break

        recs = [
            ("Urgent tickets need immediate attention", "Several urgent and frustrated tickets require first response within 1 hour.", "Urgency", "Urgent", ["Triage escalations", "Assign senior agents"]),
            ("At-risk customers detected", "Cancellation and refund language appears frequently. Prioritize retention handling.", "Retention", "High", ["Review cancellation tickets", "Offer policy-compliant options"]),
            ("Recurring billing failures", "Payment failure tickets are clustered. Improve macros and KB coverage.", "Knowledge Gaps", "High", ["Update failed payment guide", "Create billing macro"]),
            ("Missing KB article depth", "Login/MFA and GDPR deletion paths need clearer citations for agents.", "Knowledge Gaps", "Medium", ["Expand login KB", "Publish GDPR runbook"]),
            ("Strengthen approval workflow", "Keep AI replies in drafted/approved states before send to protect quality.", "Quality", "Medium", ["Require approval", "Audit sent replies"]),
            ("Route escalations by specialty", "Security/legal/billing escalations should map to specialty teams.", "Escalation Routing", "High", ["Update routing rules", "Train agents on team map"]),
        ]
        for title, desc, cat, pri, actions in recs:
            db.add(
                Recommendation(
                    title=title,
                    description=desc,
                    category=cat,
                    priority=pri,
                    action_items=actions,
                )
            )

        db.commit()
        print("Seed complete:")
        print(f"  User: {user.email} / demo1234")
        print(f"  Tickets: {db.query(Ticket).count()}")
        print(f"  Analyses: {db.query(TicketAnalysis).count()}")
        print(f"  Replies: {db.query(ReplyDraft).count()}")
        print(f"  Escalations: {db.query(Escalation).count()}")
        print(f"  KB docs: {db.query(KnowledgeBaseDocument).count()}")
        print(f"  KB chunks: {db.query(KnowledgeBaseChunk).count()}")
        print(f"  Recommendations: {db.query(Recommendation).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
