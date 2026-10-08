import json
import re
from datetime import datetime, timezone

INPUT = "report.json"

SERVICE_BANDS = {
    "ai_automation": {"low": 250, "mid": 600, "high": 1500},
    "lead_generation": {"low": 300, "mid": 750, "high": 2000},
    "ai_support": {"low": 200, "mid": 500, "high": 1200},
    "integration": {"low": 250, "mid": 650, "high": 1600},
    "other": {"low": 150, "mid": 400, "high": 1000},
}

CATEGORIES = {
    "ai_automation": [
        "automation", "workflow", "n8n",
        "zapier", "make.com", "ai agent"
    ],
    "lead_generation": [
        "lead generation", "sales", "crm",
        "appointment", "outbound"
    ],
    "ai_support": [
        "customer support", "chatbot", "support"
    ],
    "integration": [
        "api integration", "integration", "api", "crm"
    ],
}


def money_values(text):
    values = []

    patterns = [
        r"[$€£]\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
        r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:USD|EUR|GBP)",
    ]

    for pattern in patterns:
        for raw in re.findall(pattern, text, flags=re.I):
            try:
                values.append(float(raw.replace(",", "")))
            except ValueError:
                pass

    return values


def classify(item):
    text = " ".join([
        item.get("title", ""),
        item.get("snippet", ""),
        " ".join(item.get("matched_keywords", [])),
    ]).lower()

    scores = {}

    for category, words in CATEGORIES.items():
        scores[category] = sum(
            1 for word in words if word in text
        )

    if not scores:
        return "other", 0

    category = max(scores, key=scores.get)

    if scores[category] == 0:
        return "other", 0

    return category, scores[category]


def analyze(item):
    category, category_hits = classify(item)

    text = (
        item.get("title", "")
        + " "
        + item.get("snippet", "")
    )

    budget = money_values(text)

    base = SERVICE_BANDS[category]

    if budget:
        estimated_value = max(budget)
        value_basis = "Detected budget/rate in listing"
    else:
        estimated_value = base["mid"]
        value_basis = (
            "Service-band estimate; "
            "not a quoted budget"
        )

    fit = float(
        item.get("automation_fit", 0.0)
    )

    confidence = float(
        item.get("confidence", 0.0)
    )

    source_score = float(
        item.get("score", 0)
    )

    money_score = min(
        100,
        30 + (estimated_value / 20)
    )

    opportunity_score = round(
        min(
            100,
            source_score * 0.35
            + fit * 100 * 0.25
            + confidence * 100 * 0.15
            + money_score * 0.15
            + min(100, category_hits * 15) * 0.10
        )
    )

    if opportunity_score >= 75:
        priority = "HIGH"
    elif opportunity_score >= 55:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    services = {
        "ai_automation":
            "AI workflow automation",
        "lead_generation":
            "AI lead generation and follow-up",
        "ai_support":
            "AI customer-support automation",
        "integration":
            "AI/API/CRM integration",
        "other":
            "AI workflow improvement",
    }

    offer = {
        "service": services[category],
        "starter_price_eur": base["low"],
        "target_price_eur": base["mid"],
        "premium_price_eur": base["high"],
        "pitch": (
            "I can automate the "
            + category.replace("_", " ")
            + " workflow, connect the required "
            "tools, and deliver a measurable "
            "working flow."
        ),
    }

    return {
        **item,
        "analysis": {
            "category": category,
            "priority": priority,
            "opportunity_score":
                opportunity_score,
            "estimated_value_eur":
                round(estimated_value),
            "value_basis":
                value_basis,
            "budget_signals":
                budget[:5],
            "offer":
                offer,
            "human_approval_required":
                True,
        },
    }


def main():
    with open(
        INPUT,
        "r",
        encoding="utf-8"
    ) as file:
        report = json.load(file)

    analyzed = [
        analyze(item)
        for item in report.get(
            "opportunities", []
        )
    ]

    analyzed.sort(
        key=lambda x: (
            x["analysis"][
                "opportunity_score"
            ],
            x["analysis"][
                "estimated_value_eur"
            ],
        ),
        reverse=True,
    )

    report["mode"] = (
        "opportunity_hunter_and_analyst"
    )

    report["generated_at"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    report["analysis"] = {
        "status":
            "ready_for_human_review",
        "note":
            "Scores and prices are estimates, "
            "not guaranteed earnings.",
        "next_step":
            "Review the highest-priority "
            "opportunity before contacting "
            "the buyer.",
    }

    report["opportunities"] = analyzed[:30]

    with open(
        INPUT,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2
        )


if __name__ == "__main__":
    main()