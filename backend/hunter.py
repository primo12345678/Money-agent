import html, json, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

SOURCES = [
    ("Reddit r/forhire", "https://www.reddit.com/r/forhire/new/.rss"),
    ("Reddit r/DoneDirtCheap", "https://www.reddit.com/r/DoneDirtCheap/new/.rss"),
]
MAX_AGE_DAYS = 14
SERVICE_TERMS = {
    "ai_automation": ["ai automation", "workflow automation", "n8n", "zapier", "make.com", "ai agent", "automate", "automation workflow"],
    "lead_generation": ["lead generation", "lead capture", "lead follow-up", "lead follow up", "crm automation", "sales automation"],
    "customer_support": ["customer support automation", "support chatbot", "customer service chatbot", "chatbot", "ticket automation"],
    "integration": ["api integration", "google sheets automation", "email automation", "webhook", "crm integration", "integrate"],
}
BUYER_SIGNALS = ["looking for a freelancer", "need a freelancer", "seeking a freelancer", "hiring a freelancer",
    "freelancer needed", "need someone to build", "looking for someone to build", "looking to hire a freelancer",
    "contractor needed", "paid project", "fixed price project", "fixed-price project", "project budget",
    "budget is", "budget:", "paying for", "will pay for", "freelance project", "commissioned project", "[hiring]", "[task]"]
SELLER_TITLE_RE = re.compile(r"^\s*\[(?:for hire|available|self promotion)\]", re.I)
SELLER_SIGNALS = ["i am looking for freelance work", "i'm looking for freelance work", "available for freelance",
    "my rate is", "rate: $", "rate: €", "portfolio:"]
EMPLOYMENT_SIGNALS = ["full-time", "full time", "part-time", "part time", "annual salary", "per annum",
    "job opening", "job vacancy", "apply for this job", "join our team", "employment opportunity",
    "benefits package", "career opportunity", "position is", "salary range", "internship",
    "entry-level role", "remote job", "looking for a job"]
BUDGET_PATTERN = re.compile(r"(?:project budget|budget|fixed[- ]price|pay(?:ing)? for)\s*(?:is|of|:|=)?\s*(?:[$€£]\s*\d[\d,.]*|\d[\d,.]*\s*(?:USD|EUR|GBP))", re.I)

def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "MoneyAgent/3.0 (public opportunity research)"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "ignore")

def clean(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def child_text(item, names):
    for node in item.iter():
        if node.tag.split("}")[-1] in set(names) and node.text:
            return node.text
    return ""

def item_link(item):
    for node in item.iter():
        if node.tag.split("}")[-1] == "link":
            value = node.attrib.get("href") or node.text
            if value and value.strip():
                return value.strip()
    return ""

def parse_date(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            return None

def classify_service(text):
    lower = text.lower()
    hits = {key: [term for term in terms if term in lower] for key, terms in SERVICE_TERMS.items()}
    hits = {key: value for key, value in hits.items() if value}
    if not hits:
        return None, []
    category = max(hits, key=lambda key: len(hits[key]))
    return category, hits[category]

def buyer_signals(text):
    lower = text.lower()
    return [signal for signal in BUYER_SIGNALS if signal in lower]

def budget_signal(text):
    match = BUDGET_PATTERN.search(text)
    return clean(match.group(0)) if match else ""

def evaluate(title, description, published, url, source):
    combined = clean(f"{title} {description}")
    lower = combined.lower()
    if SELLER_TITLE_RE.search(title) or any(signal in lower for signal in SELLER_SIGNALS):
        return None, "service_provider_listing"
    if any(signal in lower for signal in EMPLOYMENT_SIGNALS):
        return None, "employment_listing"
    category, service_hits = classify_service(combined)
    buyer_hits = buyer_signals(combined)
    budget = budget_signal(combined)
    if not category:
        return None, "no_relevant_service"
    if not buyer_hits and not budget:
        return None, "no_explicit_buyer_intent"
    age = None
    if published:
        age = max(0, (datetime.now(timezone.utc) - published).total_seconds() / 86400)
        if age > MAX_AGE_DAYS:
            return None, "stale"
    score = min(100, 45 + 12 * len(buyer_hits) + (15 if budget else 0))
    if "freelancer" in lower or "freelance" in lower or "contractor" in lower:
        score = min(100, score + 8)
    return {"source": source, "title": title, "url": url, "published": published.isoformat() if published else "",
        "age_days": round(age, 1) if age is not None else None, "snippet": clean(description)[:1200],
        "service_category": category, "service_signals": service_hits[:8], "buyer_signals": buyer_hits[:8],
        "buyer_intent_score": score, "explicit_budget": bool(budget), "budget_signal": budget,
        "lead_type": "explicit_service_buyer_request", "human_review_required": True}, ""

def parse_feed(xml_text, source):
    root = ET.fromstring(xml_text)
    items = [node for node in root.iter() if node.tag.split("}")[-1] in ("item", "entry")]
    found, rejected = [], {}
    for item in items:
        title = clean(child_text(item, ["title"]))
        description = clean(child_text(item, ["description", "summary", "content", "encoded"]))
        published = parse_date(clean(child_text(item, ["pubDate", "published", "updated"])))
        lead, reason = evaluate(title, description, published, item_link(item), source)
        if lead:
            found.append(lead)
        else:
            rejected[reason] = rejected.get(reason, 0) + 1
    return found, rejected

def main():
    opportunities, errors, rejected = [], [], {}
    for source, url in SOURCES:
        try:
            found, skipped = parse_feed(fetch(url), source)
            opportunities.extend(found)
            for reason, count in skipped.items():
                rejected[reason] = rejected.get(reason, 0) + count
        except Exception as error:
            errors.append({"source": source, "error": str(error)})
    unique, seen = [], set()
    for item in sorted(opportunities, key=lambda row: (row["buyer_intent_score"], row["explicit_budget"]), reverse=True):
        key = item.get("url") or item.get("title")
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "agent": "Money Agent",
        "mode": "qualified_buyer_opportunity_hunter",
        "commercial_goal": "Find genuine buyers for small-business workflow automation pilots",
        "safety": {"auto_submit": False, "auto_signup": False, "auto_spend": False, "auto_send": False, "human_approval_required": True},
        "sources": [{"name": name, "url": url} for name, url in SOURCES],
        "quality_control": {"candidate_count": len(opportunities), "qualified_leads": len(unique), "rejected_by_reason": rejected,
            "employment_feeds_removed": True, "minimum_rule": "Relevant service signal plus explicit buyer intent or project budget; service-provider posts and ordinary employment listings rejected."},
        "opportunities": unique[:50], "errors": errors}
    with open("report.json", "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
