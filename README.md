# Money Agent

Money Agent is a revenue-focused workflow automation service and its internal lead/CRM assistant.

## Operating model
1. Discover public posts where a buyer explicitly asks for a paid automation/integration project.
2. Reject ordinary job listings and generic AI discussions.
3. Score qualified buyer requests with visible reasons.
4. Draft a personalized offer for human review.
5. Track leads through a simple CRM pipeline.
6. Count revenue only when a payment is confirmed.

## First product to validate
**Lead Response Mini-System** for small businesses:
- Capture enquiries from one agreed form or mailbox.
- Log enquiries in a client-owned spreadsheet.
- Send an acknowledgement and notify the business owner.
- Create a follow-up reminder and status tracker.

Initial price hypotheses, not validated market rates: pilot €149; standard setup €299; optional support €39/month.

## Run locally
```bash
python backend/hunter.py
python backend/analyst.py
python backend/deal_maker.py
python backend/pipeline.py
python -m unittest discover -s tests -v
```

## CRM
```bash
python backend/crm.py status LEAD_ID contacted --note "Sent approved message"
python backend/crm.py payment LEAD_ID 149 --note "Pilot payment received" --confirmed
```
Only payments recorded with `--confirmed` count as revenue.

## Safety
- No automatic messages, registrations, purchases or ad clicks.
- A person verifies every lead and approves every contact.
- Do not store sensitive customer data in this repository.
- Agree scope, access, privacy terms and payment terms before implementation.
