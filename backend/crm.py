import argparse,json
from datetime import datetime,timezone
from pathlib import Path
STORE=Path("data/lead_pipeline.json");REVENUE=Path("data/revenue.json")
VALID={"new","reviewed","contacted","replied","qualified","proposal_sent","won","lost"}
def load(p,d):
 if not p.exists():return d
 with p.open(encoding="utf-8") as f:return json.load(f)
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("w",encoding="utf-8") as f:json.dump(d,f,ensure_ascii=False,indent=2)
def main():
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest="command",required=True)
 s=sub.add_parser("status");s.add_argument("lead_id");s.add_argument("value",choices=sorted(VALID));s.add_argument("--note",default="")
 p=sub.add_parser("payment");p.add_argument("lead_id");p.add_argument("amount_eur",type=float);p.add_argument("--note",default="");p.add_argument("--confirmed",action="store_true")
 a=parser.parse_args();now=datetime.now(timezone.utc).isoformat()
 if a.command=="status":
  d=load(STORE,{"leads":[]});lead=next((x for x in d["leads"] if x["lead_id"]==a.lead_id),None)
  if not lead:raise SystemExit("Lead not found. Run the worker first.")
  lead["status"]=a.value;lead["notes"]=a.note or lead.get("notes","");lead["updated_at"]=now;save(STORE,d);print("Lead status updated.");return
 if a.amount_eur<=0:raise SystemExit("Payment amount must be positive.")
 d=load(REVENUE,{"payments":[]});d["payments"].append({"lead_id":a.lead_id,"amount_eur":round(a.amount_eur,2),"note":a.note,"confirmed":bool(a.confirmed),"recorded_at":now});save(REVENUE,d);print("Payment saved; only --confirmed payments count as revenue.")
if __name__=="__main__":main()
