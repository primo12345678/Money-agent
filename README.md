# Money Agent

Money Agent has two revenue channels:
1. **Freelance work:** evaluate manually captured Upwork jobs, reject unprofitable work, and prepare proposal drafts for human review.
2. **Our service:** sell the Lead Response Mini-System to small, non-regulated service businesses.

## Freelance job hunter

The Upwork evaluator works from job details copied by a human into `data/upwork_inbox.json`. It does not log in to Upwork, scrape pages, buy Connects, or submit proposals.

Start with the example:
```bash
cp data/upwork_inbox.example.json data/upwork_inbox.json
python backend/upwork_hunter.py
```
The resulting `report.json` contains an `upwork` section with scored jobs, rejection reasons, and proposal drafts. Default minimums are USD 8/hour or USD 50 fixed-price; adjust these only after considering delivery time, fees, and actual profit. All proposals require human approval.

## Our first service: Lead Response Mini-System

For small, non-regulated service businesses that receive enquiries through one simple web form OR one shared mailbox and currently track them manually.

The pilot includes one intake channel, a customer-owned Google Sheet, owner notification, a simple lead pipeline, and an agreed follow-up reminder. Automated acknowledgements require customer approval.

See [the service blueprint](docs/lead-response-mini-system.md).

Initial price hypotheses (not validated market rates): EUR 149 pilot, EUR 299 standard setup after a successful pilot, optional EUR 39/month maintenance.

## Existing buyer-opportunity hunter

The public-source hunter searches Reddit RSS and Hacker News for explicit buyer requests for automation services. These sources are limited and do not provide Upwork jobs. It rejects ordinary employment ads and service-provider posts.

## Run locally

```bash
python backend/hunter.py
python backend/analyst.py
python backend/deal_maker.py
python backend/pipeline.py
python backend/upwork_hunter.py
python -m unittest discover -s tests -v
```

## CRM

```bash
python backend/crm.py status LEAD_ID contacted --note "Sent approved message"
python backend/crm.py payment LEAD_ID 149 --note "Pilot payment received" --confirmed
```
Only confirmed payments count as revenue.

## Safety and limitations

- No automatic Upwork scraping, login automation, Connects purchases, or proposal submission.
- No automatic sales messages, registrations, purchases, or ad clicks.
- A person verifies every lead and approves every contact/proposal.
- Do not store customer personal or sensitive data in this repository.
- Use customer-owned accounts and least-privilege access.
- Do not activate customer-facing messages until the customer approves content and trigger.
- Do not claim revenue until payment is received and confirmed.
