# Money Agent

Money Agent is a revenue-focused workflow automation service and its internal lead/CRM assistant.

## Chosen business model

We will initially sell one narrowly scoped service: **Lead Response Mini-System** for small, non-regulated service businesses that receive enquiries through a simple web form or shared mailbox and currently track them manually.

The pilot covers one intake channel, a customer-owned Google Sheet, an owner notification, a simple lead-status pipeline, and an agreed follow-up reminder. An automated acknowledgement is optional and must be approved by the customer before activation.

See [the service blueprint](docs/lead-response-mini-system.md) for scope, exclusions, delivery steps, acceptance tests, privacy controls, and go/no-go criteria.

## Price hypotheses (not validated market rates)

- Pilot: EUR 149.
- Standard setup after a successful pilot: EUR 299, subject to scope.
- Optional maintenance: EUR 39/month, only if recurring support is requested.

These are our test prices, not customer budgets or guaranteed market rates. We will not scale the offer until a paid pilot is delivered and accepted.

## Operating model

1. Discover public posts where a buyer explicitly asks for a paid automation/integration project.
2. Reject ordinary job listings, service-provider ads, and generic AI discussions.
3. Score qualified buyer requests with visible reasons.
4. Draft a personalized offer for human review.
5. Track leads through a simple CRM pipeline.
6. Deliver customer work only after scope, access, privacy terms, and payment terms are agreed.
7. Count revenue only when a payment is confirmed.

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

- No automatic sales messages, registrations, purchases, or ad clicks.
- A person verifies every lead and approves every contact.
- Do not store customer personal or sensitive data in this repository.
- Use customer-owned accounts and least-privilege access.
- Do not activate customer-facing messages until the customer approves the content and trigger.
- Do not claim revenue until payment is received and confirmed.
