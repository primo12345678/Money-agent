import html
import json
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# Public RSS sources only. The worker is rate-limited and never logs in or posts.
SOURCES = [
    ("Reddit r/forhire", "https://www.reddit.com/r/forhire/new/.rss?limit=50"),
    ("Reddit r/DoneDirtCheap", "https://www.reddit.com/r/DoneDirtCheap/new/.rss?limit=50"),
    ("Reddit r/smallbusiness", "https://www.reddit.com/r/smallbusiness/.rss?limit=30"),
    ("Reddit r/Entrepreneur", "https://www.reddit.com/r/Entrepreneur/.rss?limit=30"),
    ("Reddit r/ecommerce", "https://www.reddit.com/r/ecommerce/.rss?limit=30"),
]
MAX_AGE_DAYS = 14

HN_QUERIES = [
    '"looking for help" automation',
    '"need help" Zapier OR n8n',
    '"workflow automation" "looking for"',
    '"AI agent" "need someone"',
]
BLUESKY_QUERIES = [
    '"looking for" automation',
    '"need help" Zapier',
    '"need help" n8n',
    '"AI agent" business automation',
]
SERVICE_TERMS = {
    "ai_automation": ["ai automation", "workflow automation", "n8n", "zapier", "make.com", "ai agent", "automation workflow", "chatgpt integration"],
    "lead_generation": ["lead generation", "lead capture", "lead follow-up", "lead follow up", "crm automation", "sales automation"],
    "customer_support": ["customer support automation", "support chatbot", "customer service chatbot", "chatbot", "ticket automation"],
    "integration": ["api integration", "google sheets automation", "email automation", "webhook", "crm integration"],
}
BUYER_SIGNALS = [
    "[hiring]", "[task]", "looking for a freelancer", "need a freelancer",
    "seeking a freelancer", "hiring a freelancer", "freelancer needed",
    "need someone to build", "looking for someone to build",
    "looking for help with", "looking for help", "need help with",
    "need help setting up", "looking to hire", "want to hire",
    "seeking someone to", "paid project", "fixed price project",
    "fixed-price project", "project budget", "budget is", "budget:",
    "paying for", "will pay for", "commissioned project",
]
SELLER_TITLE_RE = re.compile(
    r"^\s*\[(?:for hire|available|self promotion|offer|offering|hire me|service provider)\]",
    re.I,
)
SELLER_SIGNALS = [
    "i am looking for freelance work", "i'm looking for freelance work",
    "available for freelance", "available for work", "my rate is",
    "rate: $", "rate: €", "hourly rate", "my services", "hire me",
    "i offer ", "i provide ", "dm me for", "portfolio:",
]
EMPLOYMENT_SIGNALS = [
    "full-time", "full time", "part-time", "part time", "annual salary",
    "per annum", "job opening", "job vacancy", "apply for this job",
    "join our team", "employment opportunity", "benefits package", "financial controller", "software engineer",
    "career opportunity", "position is", "salary range", "internship",
    "entry-level role", "remote job", "looking for a job",
]
BUDGET_PATTERN = re.compile(
    r"(?:project budget|budget|fixed[- ]price|pay(?:ing)? for|will pay)\s*"
    r"(?:is|of|:|=)?\s*(?:[$€£]\s*\d[\d,.]*|\d[\d,.]*\s*(?:USD|EUR|GBP))",
    re.I,
)


def fetch(url):
    last_error = None
    for attempt in range(3):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "MoneyAgent/1.0 (public RSS opportunity research; contact: repository owner)",
                "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code != 429 or attempt == 2:
                raise
            retry_after = error.headers.get("Retry-After", "3")
            try:
                delay = min(12, max(3, int(retry_after)))
            except ValueError:
                delay = 3
            time.sleep(delay * (attempt + 1))
    raise last_error


def clean(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def child_text(item, names):
    wanted = set(names)
    for node in item.iter():
        if node.tag.split("}")[-1] in wanted and node.text:
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
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
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
    project_intent = any(term in lower for term in (
        "paid project", "fixed price", "fixed-price", "project budget",
        "one-off project", "pilot project", "build an automation",
        "build a workflow", "set up an automation", "automation setup",
    ))
    # A generic [Hiring] tag or hourly job advert is not a buyer for our packaged service.
    if buyer_hits == ["[hiring]"] and not budget and not project_intent:
        return None, "employment_listing"
    if any(term in lower for term in ("hourly", "per hour", "/hr", "salary")) and not project_intent and not budget:
        return None, "employment_listing"
    if not category:
        return None, "no_relevant_service"
    if not buyer_hits and not budget:
        return None, "no_explicit_buyer_intent"
    age = None
    if published:
        age = max(0, (datetime.now(timezone.utc) - published).total_seconds() / 86400)
        if age > MAX_AGE_DAYS:
            return None, "stale"

    # A lead must show both a relevant service need and buyer intent/budget.
    score = min(
        100,
        40
        + min(20, len(service_hits) * 10)
        + min(20, len(buyer_hits) * 10)
        + (15 if budget else 0)
        + (10 if age is None else max(0, 10 - int(age // 2))),
    )
    return {
        "source": source,
        "title": title,
        "url": url,
        "published": published.isoformat() if published else "",
        "age_days": round(age, 1) if age is not None else None,
        "snippet": clean(description)[:1200],
        "service_category": category,
        "service_signals": service_hits[:8],
        "buyer_signals": buyer_hits[:8],
        "buyer_intent_score": score,
        "explicit_budget": bool(budget),
        "budget_signal": budget,
        "lead_type": "explicit_service_buyer_request",
        "human_review_required": True,
    }, ""


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



def fetch_hacker_news(query):
    from urllib.parse import urlencode
    params = urlencode({"query": query, "tags": "story", "hitsPerPage": 50})
    request = urllib.request.Request(
        "https://hn.algolia.com/api/v1/search_by_date?" + params,
        headers={"User-Agent": "MoneyAgent/1.0 public lead research"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8", "ignore"))
    found = []
    rejected = {}
    for hit in payload.get("hits", []):
        title = clean(hit.get("title") or "")
        description = clean(hit.get("story_text") or hit.get("comment_text") or "")
        created = hit.get("created_at", "")
        published = parse_date(created)
        object_id = hit.get("objectID", "")
        url = hit.get("url") or (f"https://news.ycombinator.com/item?id={object_id}" if object_id else "")
        lead, reason = evaluate(title, description, published, url, "Hacker News")
        if lead:
            found.append(lead)
        else:
            rejected[reason] = rejected.get(reason, 0) + 1
    return found, rejected



def fetch_bluesky(query):
    from urllib.parse import urlencode
    params = urlencode({"q": query, "limit": 100, "sort": "latest"})
    request = urllib.request.Request(
        "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?" + params,
        headers={"User-Agent": "MoneyAgent/1.0 public buyer-intent research"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8", "ignore"))
    found = []
    rejected = {}
    for item in payload.get("posts", []):
        record = item.get("record", {})
        author = item.get("author", {})
        title = clean(record.get("text", ""))[:180]
        description = clean(record.get("text", ""))
        created = record.get("createdAt", "")
        published = parse_date(created)
        uri = item.get("uri", "")
        rkey = uri.rsplit("/", 1)[-1] if uri else ""
        handle = author.get("handle", "")
        url = f"https://bsky.app/profile/{handle}/post/{rkey}" if handle and rkey else ""
        lead, reason = evaluate(title, description, published, url, "Bluesky")
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
            errors.append({"source": source, "error": str(error)[:300]})

    for query in HN_QUERIES:
        try:
            found, skipped = fetch_hacker_news(query)
            opportunities.extend(found)
            for reason, count in skipped.items():
                rejected[reason] = rejected.get(reason, 0) + count
        except Exception as error:
            errors.append({"source": "Hacker News: " + query, "error": str(error)[:300]})

    for query in BLUESKY_QUERIES:
        try:
            found, skipped = fetch_bluesky(query)
            opportunities.extend(found)
            for reason, count in skipped.items():
                rejected[reason] = rejected.get(reason, 0) + count
        except Exception as error:
            errors.append({"source": "Bluesky: " + query, "error": str(error)[:300]})

    unique, seen = [], set()
    for item in sorted(
        opportunities,
        key=lambda row: (row["buyer_intent_score"], row["explicit_budget"]),
        reverse=True,
    ):
        key = item.get("url") or item.get("title")
        if key and key not in seen:
            seen.add(key)
            unique.append(item)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent": "Money Agent",
        "mode": "qualified_buyer_opportunity_hunter",
        "commercial_goal": "Find genuine buyers for small-business workflow automation pilots",
        "safety": {
            "auto_submit": False,
            "auto_signup": False,
            "auto_spend": False,
            "auto_send": False,
            "human_approval_required": True,
        },
        "sources": [{"name": name, "url": url} for name, url in SOURCES] + [{"name": "Hacker News Algolia", "url": "https://hn.algolia.com/api"}, {"name": "Bluesky public search", "url": "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"}],
        "quality_control": {
            "candidate_count": len(opportunities),
            "qualified_leads": len(unique),
            "rejected_by_reason": rejected,
            "employment_feeds_removed": True,
            "seller_posts_rejected": True,
            "minimum_rule": "Relevant service need plus explicit buyer intent or a project budget; service-provider posts and ordinary employment listings rejected.",
        },
        "opportunities": unique[:50],
        "errors": errors,
    }
    with open("report.json", "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
