import json
import re
import urllib.request
from datetime import datetime, timezone

SOURCES = [
    ("Upwork AI Automation",
     "https://www.upwork.com/freelance-jobs/ai-automation/"),
    ("Upwork AI Integration",
     "https://www.upwork.com/freelance-jobs/ai-integration/"),
]

KEYWORDS = [
    "automation", "ai agent", "ai integration",
    "workflow", "zapier", "make.com", "n8n",
    "chatbot", "lead", "fixed-price", "hourly"
]


def fetch(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "MoneyAgent/1.0"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "ignore")


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def score(text):
    low = text.lower()
    hits = sum(word in low for word in KEYWORDS)

    return {
        "score": min(100, 20 + hits * 8),
        "confidence": min(1.0, 0.3 + hits * 0.07),
        "automation_fit": min(1.0, 0.4 + hits * 0.06),
    }


def main():
    opportunities = []
    errors = []

    for name, url in SOURCES:
        try:
            page = clean(fetch(url))
            low = page.lower()

            for keyword in KEYWORDS:
                position = low.find(keyword)

                if position >= 0:
                    snippet = page[
                        max(0, position - 150):
                        position + 500
                    ]

                    opportunities.append({
                        "source": name,
                        "url": url,
                        "keyword": keyword,
                        "snippet": snippet,
                        **score(snippet)
                    })

        except Exception as error:
            errors.append({
                "source": name,
                "error": str(error)
            })

    opportunities.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    report = {
        "generated_at":
            datetime.now(timezone.utc).isoformat(),
        "agent": "Money Agent",
        "mode": "opportunity_hunter",
        "target": "Find legitimate income opportunities",
        "safety": {
            "auto_submit": False,
            "auto_signup": False,
            "auto_spend": False,
            "auto_click_ads": False
        },
        "opportunities": opportunities[:20],
        "errors": errors
    }

    with open("report.json", "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2
        )


if __name__ == "__main__":
    main()