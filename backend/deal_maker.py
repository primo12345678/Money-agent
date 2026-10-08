import json
from datetime import datetime, timezone

INPUT = "report.json"


def build_offer(item):
    analysis = item.get("analysis", {})
    offer = analysis.get("offer", {})

    title = item.get("title", "your workflow")
    service = offer.get(
        "service",
        "AI workflow improvement"
    )

    target = offer.get(
        "target_price_eur",
        500
    )

    starter = offer.get(
        "starter_price_eur",
        250
    )

    return {
        "subject": f"Proposal: {service}",
        "price_eur": target,
        "starter_price_eur": starter,

        "message": (
            f"Hi,\n\n"
            f"I saw your request about "
            f"\"{title}\". "
            f"I can help with "
            f"{service.lower()} and focus on "
            f"a working, measurable result.\n\n"

            f"Suggested first step: a small "
            f"implementation/audit for "
            f"€{starter}, with the full solution "
            f"targeted at about €{target} "
            f"depending on scope.\n\n"

            f"I can map the current workflow, "
            f"identify the highest-value "
            f"automation, and propose the "
            f"exact tools and deliverables "
            f"before any larger commitment.\n\n"

            f"If useful, I can send a short "
            f"implementation plan.\n\n"

            f"Best,\nMoney Agent"
        ),

        "human_approval_required": True,
        "auto_send": False,
    }


def main():
    with open(
        INPUT,
        "r",
        encoding="utf-8"
    ) as file:
        report = json.load(file)

    opportunities = report.get(
        "opportunities",
        []
    )

    drafts = []

    for item in opportunities[:10]:
        analysis = item.get(
            "analysis",
            {}
        )

        if not analysis:
            continue

        drafts.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "priority": analysis.get(
                "priority"
            ),
            "opportunity_score":
                analysis.get(
                    "opportunity_score"
                ),
            "estimated_value_eur":
                analysis.get(
                    "estimated_value_eur"
                ),
            "offer": build_offer(item),
        })

    report["deal_maker"] = {
        "status":
            "drafts_ready_for_human_review",

        "created_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "auto_send": False,
        "auto_signup": False,

        "draft_count":
            len(drafts),

        "drafts":
            drafts,
    }

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