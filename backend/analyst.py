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
    "ai_automation": ["automation", "workflow", "n8n", "zapier", "make.com", "ai agent"],
    "lead_generation": ["lead generation", "sales", "crm", "appointment", "outbound"],
    "ai_support": ["customer support", "chatbot", "support"],
    "integration": ["api integration", "integration", "api", "crm"],
}

# Only treat a number as a quoted project budget when the surrounding text
# explicitly describes a project budget/rate for the requested work.
BUDGET_CONTEXT = re.compile(
    r"(?:project|project's|client|fixed[- ]price|contract)\s+(?:budget|price|rate)"
    r"|(?:budget|price|rate)\s+(?:for this project|for the project|is|of|:|=)"
    r"|(?:paying|budget is|budget of|project budget|fixed price|paid project)\s*[:=]?",
    re.IGNORECASE,
)
MONEY_TOKEN = re.compile(r"(?:[$€£]\s*\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s*(?:USD|EUR|GBP)\b)", re.IGNORECASE)

EMPLOYMENT_CONTEXT = re.compile(
    r"\b(?:annual salary|salary|per annum|per year|yearly|hourly|per hour|\b/hr\b|\b/hour\b|compensation|pay range|salary range)\b",
    re.IGNORECASE,
)


def _amount(token):
    match = re.search(r"\d[\d,]*(?:\.\d+)?", token)
    return float(match.group(0).replace(",", "")) if match else None


def money_values(text):
    """Return amounts only when explicitly tied to a project/service budget.

    Generic salaries, company revenue, and unrelated prices are deliberately
    ignored. Unknown amounts are not treated as project budgets.
    """
    text = text or ""
    values = []
    for context_match in BUDGET_CONTEXT.finditer(text):
        start = max(0, context_match.start() - 100)
        end = min(len(text), context_match.end() + 140)
        context = text[start:end]
        if EMPLOYMENT_CONTEXT.search(context):
            continue
        for token in MONEY_TOKEN.findall(context):
            value = _amount(token)
            if value is not None and value > 0 and value not in values:
                values.append(value)
    return values


def classify(item):
    text = " ".join([
        item.get("title", ""),
        item.get("snippet", ""),
        " ".join(item.get("matched_keywords", [])),
    ]).lower()
    scores = {category: sum(1 for word in words if word in text)
              for category, words in CATEGORIES.items()}
    category = max(scores, key=scores.get)
    return (category, scores[category]) if scores[category] else ("other", 0)


def analyze(item):
    category, category_hits = classify(item)
    text = f"{item.get('title', '')} {item.get('snippet', '')}"
    budget = money_values(text)
    base = SERVICE_BANDS[category]

    if budget:
        estimated_value = max(budget)
        value_basis = "Explicit project budget/rate detected; verify with client"
    else:
        estimated_value = base["mid"]
        value_basis = "Service-band estimate; not a quoted client budget"

    fit = float(item.get("automation_fit", 0.0))
    confidence = float(item.get("confidence", 0.0))
    source_score = float(item.get("score", 0))
    money_score = min(100, 30 + estimated_value / 20)
    opportunity_score = round(min(100,
        source_score * 0.35 + fit * 100 * 0.25 + confidence * 100 * 0.15
        + money_score * 0.15 + min(100, category_hits * 15) * 0.10))
    priority = "HIGH" if opportunity_score >= 75 else "MEDIUM" if opportunity_score >= 55 else "LOW"

    services = {
        "ai_automation": "AI workflow automation",
        "lead_generation": "AI lead generation and follow-up",
        "ai_support": "AI customer-support automation",
        "integration": "AI/API/CRM integration",
        "other": "AI workflow improvement",
    }
    offer = {
        "service": services[category],
        "starter_price_eur": base["low"],
        "target_price_eur": base["mid"],
        "premium_price_eur": base["high"],
        "pitch": (f"I can help improve your {category.replace('_', ' ')} workflow, "
                  "confirm the scope first, and propose a measurable small first step."),
    }
    return {**item, "analysis": {
        "category": category,
        "priority": priority,
        "opportunity_score": opportunity_score,
        "estimated_value_eur": round(estimated_value),
        "value_basis": value_basis,
        "budget_signals": budget[:5],
        "offer": offer,
        "human_approval_required": True,
    }}


def main():
    with open(INPUT, "r", encoding="utf-8") as file:
        report = json.load(file)
    analyzed = [analyze(item) for item in report.get("opportunities", [])]
    analyzed.sort(key=lambda x: (x["analysis"]["opportunity_score"],
                                x["analysis"]["estimated_value_eur"]), reverse=True)
    report["mode"] = "opportunity_hunter_and_analyst"
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["analysis"] = {
        "status": "ready_for_human_review",
        "note": "Scores and service prices are estimates, not guaranteed earnings. Only explicit project-budget context is treated as a quoted budget.",
        "next_step": "Review the lead and verify the scope/budget before contacting the buyer.",
    }
    report["opportunities"] = analyzed[:30]
    with open(INPUT, "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
