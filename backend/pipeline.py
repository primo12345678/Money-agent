import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
REPORT=Path("report.json");STORE=Path("data/lead_pipeline.json");REVENUE=Path("data/revenue.json")
STATUSES={"new","reviewed","contacted","replied","qualified","proposal_sent","won","lost"}
def read(path,default):
 if not path.exists():return default
 with path.open(encoding="utf-8") as f:return json.load(f)
def lead_id(url,title):return hashlib.sha256((url or title).encode()).hexdigest()[:12]
def main():
 report=read(REPORT,{});STORE.parent.mkdir(parents=True,exist_ok=True);store=read(STORE,{"updated_at":None,"leads":[]});leads={x["lead_id"]:x for x in store.get("leads",[])};now=datetime.now(timezone.utc).isoformat()
 for item in report.get("opportunities",[]):
  key=lead_id(item.get("url",""),item.get("title",""))
  if key in leads:leads[key]["last_seen_at"]=now;leads[key]["latest_score"]=item.get("analysis",{}).get("opportunity_score",0);continue
  leads[key]={"lead_id":key,"title":item.get("title",""),"url":item.get("url",""),"source":item.get("source",""),"first_seen_at":now,"last_seen_at":now,"status":"new","notes":"","latest_score":item.get("analysis",{}).get("opportunity_score",0),"actual_revenue_eur":0.0,"payment_confirmed":False}
 revenue=read(REVENUE,{"payments":[]});paid={}
 for p in revenue.get("payments",[]):
  if p.get("confirmed") is True:
   k=p.get("lead_id","");paid[k]=paid.get(k,0)+float(p.get("amount_eur",0))
 counts={s:0 for s in sorted(STATUSES)}
 for lead in leads.values():
  amount=round(paid.get(lead["lead_id"],0),2);lead["actual_revenue_eur"]=amount;lead["payment_confirmed"]=amount>0
  if amount>0 and lead.get("status")!="lost":lead["status"]="won"
  if lead.get("status") in counts:counts[lead["status"]]+=1
 with STORE.open("w",encoding="utf-8") as f:json.dump({"updated_at":now,"status_values":sorted(STATUSES),"leads":sorted(leads.values(),key=lambda x:x.get("last_seen_at",""),reverse=True)},f,ensure_ascii=False,indent=2)
 report["pipeline"]={"tracked_leads":len(leads),"status_counts":counts,"confirmed_revenue_eur":round(sum(paid.values()),2),"revenue_rule":"Only confirmed payments count; suggested prices are not revenue.","crm_file":str(STORE),"revenue_file":str(REVENUE)}
 with REPORT.open("w",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
if __name__=="__main__":main()
