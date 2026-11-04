# Money Agent upgrade

This branch contains qualified buyer discovery, offer analysis, draft generation, CRM pipeline and confirmed revenue ledger.

Run from repository root:
```bash
python -m py_compile backend/*.py
python -m unittest discover -s tests -v
python backend/hunter.py
python backend/analyst.py
python backend/deal_maker.py
python backend/pipeline.py
```

The worker does not send messages, create accounts, purchase services or spend money. Human review and approval are required. Never mark a payment confirmed until funds have arrived.
