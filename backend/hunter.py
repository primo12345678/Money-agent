import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

SOURCES = [
("Reddit r/forhire", "https://www.reddit.com/r/forhire/new/.rss"),
("Reddit r/slavelabour", "https://www.reddit.com/r/slavelabour/new/.rss"),
("Remotive", "https://remotive.com/remote-jobs/feed"),
("We Work Remotely", "https://weworkremotely.com/remote-jobs.rss"),
]

KEYWORDS = [
"automation", "ai agent", "ai integration", "workflow",
"zapier", "make.com", "n8n", "chatbot", "lead generation",
"crm", "api integration", "no-code", "low-code",
"marketing automation", "customer support", "ai",
]

BUYER_SIGNALS = [
"looking for a freelancer", "need a freelancer",
"looking to hire", "need help with", "looking for someone to",
"seeking someone to", "project budget", "budget is",
"paying", "paid project", "fixed price", "contractor needed",
"need someone to build", "want to build",
"looking for a developer", "looking for an expert", "[hiring]",
]

EMPLOYMENT_SIGNALS = [
"full-time", "full time", "annual salary", "per annum",
"job opening", "job vacancy", "apply for this job",
"join our team", "employment opportunity", "benefits package",
]

STRONG_PROJECT_SIGNALS = [
"project budget", "budget is", "paid project",
"fixed price", "contractor needed", "[hiring]",
]

def fetch(url):
request = urllib.request.Request(
url,
headers={"User-Agent": "MoneyAgent/1.0"},
)
with urllib.request.urlopen(request, timeout=25) as response:
return response.read().decode("utf-8", "ignore")

def clean(text):
text = re.sub(r"<[^>]+>", " ", text or "")
return re.sub(r"\s+", " ", text).strip()

def score(text):
low = text.lower()
hits = [word for word in KEYWORDS if word in low]
return {
"score": min(100, 20 + len(hits) * 7),
"confidence": round(min(1.0, 0.35 + len(hits) * 0.07), 2),
"automation_fit": round(min(1.0, 0.40 + len(hits) * 0.06), 2),
"matched_keywords": hits[:10],
}

def child_text(item, names):
for name in names:
value = item.findtext(name)
if value:
return value
value = item.findtext("{*}" + name)
if value:
return value
return ""

def parse_rss(xml_text, source):
root = ET.fromstring(xml_text)
items = root.findall(".//item")
if not items:
items = root.findall(".//{*}entry")

found = []
for item in items:
    title = clean(child_text(item, ["title"]))
    link_node = item.find("link")
    if link_node is None:
        link_node = item.find("{*}link")

    link = ""
    if link_node is not None:
        link = clean(
            link_node.text or link_node.attrib.get("href", "")
        )

    description = clean(
        child_text(item, ["description", "summary", "content"])
    )
    published = clean(
        child_text(item, ["pubDate", "published", "updated"])
    )

    combined = f"{title} {description}"
    low = combined.lower()

    if not any(word in low for word in KEYWORDS):
        continue

    buyer_hits = [
        phrase for phrase in BUYER_SIGNALS if phrase in low
    ]
    employment_hits = [
        phrase for phrase in EMPLOYMENT_SIGNALS if phrase in low
    ]

    if not buyer_hits:
        continue

    if employment_hits and not any(
        phrase in low for phrase in STRONG_PROJECT_SIGNALS
    ):
        continue

    found.append({
        "source": source,
        "title": title,
        "url": link,
        "published": published,
        "snippet": description[:900],
        "lead_type": "potential_buyer_request",
        "buyer_intent_score": min(100, len(buyer_hits) * 25),
        "buyer_signals": buyer_hits[:6],
        "employment_signals": employment_hits[:5],
        **score(combined),
    })

return found
def main():
opportunities = []
errors = []

for source, url in SOURCES:
    try:
        opportunities.extend(parse_rss(fetch(url), source))
    except Exception as error:
        errors.append({
            "source": source,
            "error": str(error),
        })

seen = set()
unique = []
for item in sorted(
    opportunities,
    key=lambda x: (
        x["buyer_intent_score"],
        x["score"],
    ),
    reverse=True,
):
    key = item.get("url") or item.get("title")
    if key and key not in seen:
        seen.add(key)
        unique.append(item)

report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "agent": "Money Agent",
    "mode": "buyer_opportunity_hunter",
    "target": "Find potential buyers for AI automation services",
    "safety": {
        "auto_submit": False,
        "auto_signup": False,
        "auto_spend": False,
        "auto_click_ads": False,
        "auto_send": False,
    },
    "sources": [
        {
            "name": name,
            "url": url,
            "attribution_required": True,
        }
        for name, url in SOURCES
    ],
    "lead_quality": {
        "rule": "Require relevant keywords and buyer-intent signals.",
        "buyer_leads_found": len(unique),
        "human_review_required": True,
    },
    "opportunities": unique[:30],
    "errors": errors,
}

with open("report.json", "w", encoding="utf-8") as file:
    json.dump(report, file, ensure_ascii=False, indent=2)

 if __name__ == "__main__":
    main()