import json
from datetime import datetime, timezone

INPUT = "report.json"
OFFER = {
    "name": "Lead Response Mini-System",
    "pilot_price_eur": 149,
    "standard_setup_price_eur": 299,
    "monthly_support_price_eur": 39,
    "scope": [
        "Capture enquiries from one agreed form or mailbox",
        "Log enquiries in a client-owned Google Sheet",
        "Send an acknowledgement and notify the business owner",
        "Create a simple follow-up reminder and status tracker",
    ],
    "delivery_note": "Final scope, access, privacy terms and price must be agreed with the customer.",
}
LABELS = {
    "ai_automation": "AI/workflow automation",
    "lead_generation": "Lead capture and follow-up",
    "customer_support": "Customer enquiry/support workflow",
    "integration": "Email, form, spreadsheet or CRM integration",
}


def analyze(item):
    category = item.get("service_category", "integration")
    buyer_signals = item.get("buyer_signals", [])
    service_signals = item.get("service_signals", [])
    has_budget = bool(item.get("explicit_budget"))
    age = item.get("age_days")
    recency = 10 if age is None else max(0, 10 - int(age // 2))
    buyer_score = min(25, len(buyer_signals) * 12)
    service_score = min(20, len(service_signals) * 8)
    budget_score = 15 if has_budget else 0
    specificity = min(10, len(buyer_signals) * 3 + len(service_signals) * 2)
    score = min(100, 35 + buyer_score + service_score + budget_score + recency + specificity)
    # Human review requires a real buyer signal, not merely a keyword or our own suggested price.
    eligible = bool(buyer_signals) and bool(service_signals) and score >= 65
    priority = "HIGH" if score >= 80 else "MEDIUM" if score >= 65 else "LOW"
    return {
        **item,
        "analysis": {
            "category": category,
            "category_label": LABELS.get(category, "Workflow automation"),
            "priority": priority,
            "opportunity_score": score,
            "score_components": {
                "buyer_intent": buyer_score,
                "service_fit": service_score,
                "explicit_budget": budget_score,
                "recency": recency,
                "specificity": specificity,
            },
            "suggested_offer": OFFER,
            "suggested_pilot_price_eur": OFFER["pilot_price_eur"],
            "price_is_our_test_offer_not_customer_budget": True,
            "eligible_for_human_review": eligible,
            "reason": (
                "Relevant buyer request; verify the post, buyer identity, scope and budget manually before contact."
                if eligible else
                "Not strong enough for human review; no outreach should be prepared."
            ),
        },
    }


def main():
    with open(INPUT, encoding="utf-8") as file:
        report = json.load(file)
    items = [analyze(item) for item in report.get("opportunities", [])]
    items.sort(
        key=lambda row: (
            row["analysis"]["eligible_for_human_review"],
            row["analysis"]["opportunity_score"],
            row.get("explicit_budget", False),
        ),
        reverse=True,
    )
    count = sum(item["analysis"]["eligible_for_human_review"] for item in items)
    report["mode"] = "qualified_buyer_hunter_and_offer_analyst"
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["commercial_model"] = {
        "offer": OFFER,
        "target": "One paid pilot, then repeatable setup and monthly support revenue",
        "revenue_definition": "Only customer payments recorded as received count as revenue.",
    }
    report["analysis"] = {
        "status": "ready_for_human_review" if count else "no_qualified_leads",
        "qualified_for_review": count,
        "total_candidates": len(items),
        "note": "No lead is contacted automatically. No revenue is claimed until payment is recorded.",
    }
    report["opportunities"] = items
    with open(INPUT, "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
