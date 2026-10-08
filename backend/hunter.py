import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

SOURCES = [
    (
        "Remotive",
        "https://remotive.com/remote-jobs/feed",
    ),
    (
        "We Work Remotely",
        "https://weworkremotely.com/remote-jobs.rss",
    ),
]

KEYWORDS = [
    "automation",
    "ai agent",
    "ai integration",
    "workflow",
    "zapier",
    "make.com",
    "n8n",
    "chatbot",
    "lead generation",
    "crm",
    "api integration",
    "no-code",
    "low-code",
    "sales",
    "marketing automation",
    "customer support",
    "ai",
]


def fetch(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "MoneyAgent/1.0"
        },
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8", "ignore")


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def score(text):
    low = text.lower()

    hits = [
        word for word in KEYWORDS
        if word in low
    ]

    return {
        "score": min(100, 20 + len(hits) * 7),
        "confidence": round(
            min(1.0, 0.35 + len(hits) * 0.07),
            2,
        ),
        "automation_fit": round(
            min(1.0, 0.40 + len(hits) * 0.06),
            2,
        ),
        "matched_keywords": hits[:10],
    }


def parse_rss(xml_text, source):
    root = ET.fromstring(xml_text)
    items = []

    for item in root.findall(".//item"):
        title = clean(
            item.findtext("title")
        )

        link = clean(
            item.findtext("link")
        )

        description = clean(
            item.findtext("description")
        )

        published = clean(
            item.findtext("pubDate")
        )

        combined = f"{title} {description}"

        if not any(
            word in combined.lower()
            for word in KEYWORDS
        ):
            continue

        items.append({
            "source": source,
            "title": title,
            "url": link,
            "published": published,
            "snippet": description[:900],
            **score(combined),
        })

    return items


def main():
    opportunities = []
    errors = []

    for source, url in SOURCES:
        try:
            xml = fetch(url)

            opportunities.extend(
                parse_rss(xml, source)
            )

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
            x["score"],
            x["automation_fit"],
        ),
        reverse=True,
    ):
        key = item.get("url") or item.get("title")

        if key and key not in seen:
            seen.add(key)
            unique.append(item)

    report = {
        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "agent":
            "Money Agent",

        "mode":
            "opportunity_hunter",

        "target":
            "Find legitimate income opportunities",

        "safety": {
            "auto_submit": False,
            "auto_signup": False,
            "auto_spend": False,
            "auto_click_ads": False,
        },

        "sources": [
            {
                "name": name,
                "url": url,
                "attribution_required": True,
            }
            for name, url in SOURCES
        ],

        "opportunities":
            unique[:30],

        "errors":
            errors,
    }

    with open(
        "report.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    main()