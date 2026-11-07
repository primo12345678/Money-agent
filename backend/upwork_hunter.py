"""Safe evaluator for manually captured Upwork jobs; never scrapes or submits."""
import json, re
from pathlib import Path
from datetime import datetime, timezone

INBOX = Path("data/upwork_inbox.json")
REPORT = Path("report.json")
SKILL_GROUPS = {
 "spreadsheets": ("google sheets","excel","spreadsheet","pivot table","dashboard","data cleaning"),
 "research": ("web research","online research","internet research","market research","lead research"),
 "lead_generation": ("lead generation","lead gen","list building","prospect list","contact research"),
 "crm_automation": ("crm","hubspot","salesforce","pipedrive","follow-up","follow up","lead tracking"),
 "automation": ("workflow automation","zapier","make.com","n8n","automation","api integration"),
 "data_entry": ("data entry","data processing","data collection","data extraction"),
}
MIN_HOURLY_USD = 8.0
MIN_FIXED_USD = 50.0

def number(value):
 if value is None or value == "": return None
 if isinstance(value,(int,float)): return float(value)
 match=re.search(r"\d[\d,]*(?:\.\d+)?",str(value).replace(",",""))
 return float(match.group(0)) if match else None

def proposal_count(value):
 if isinstance(value,int): return value
 text=str(value or "").lower()
 if "less than 5" in text or "fewer than 5" in text: return 4
 match=re.search(r"\d+",text)
 return int(match.group(0)) if match else None

def evaluate_job(job):
 title=str(job.get("title","")).strip()
 description=str(job.get("description","")).strip()
 url=str(job.get("url","")).strip()
 if not title or not description or not url.startswith("https://www.upwork.com/"):
  return None,"missing_required_fields_or_non_upwork_url"
 text=" ".join(str(job.get(k,"")) for k in ("title","description","skills")).lower()
 matched={group:[term for term in terms if term in text] for group,terms in SKILL_GROUPS.items()}
 matched={k:v for k,v in matched.items() if v}
 if not matched: return None,"no_skill_fit"
 job_type=str(job.get("job_type","hourly" if job.get("hourly_min") or job.get("hourly_max") else "fixed")).lower()
 hmin,hmax,fixed=number(job.get("hourly_min")),number(job.get("hourly_max")),number(job.get("fixed_budget"))
 if job_type=="hourly" and (hmax is None or hmax<MIN_HOURLY_USD):
  return None,"hourly_rate_below_profit_floor"
 if job_type!="hourly" and fixed is not None and fixed<MIN_FIXED_USD:
  return None,"fixed_budget_below_profit_floor"
 proposals=proposal_count(job.get("proposals"))
 spend=number(job.get("client_total_spent"))
 rating=number(job.get("client_rating"))
 verified=bool(job.get("payment_verified",False))
 score=min(100,35+min(30,len(matched)*12)+(15 if proposals is not None and proposals<5 else 10 if proposals is not None and proposals<=10 else 5 if proposals is not None and proposals<=20 else 0)+(5 if verified else 0)+(5 if spend is not None and spend>=1000 else 2 if spend is not None and spend>=200 else 0)+(5 if rating is not None and rating>=4.8 else 2 if rating is not None and rating>=4.5 else -5 if rating is not None else 0))
 reasons=["skill fit: "+", ".join(matched)]
 if proposals is not None: reasons.append("competition: "+str(job.get("proposals")))
 if verified: reasons.append("payment verified")
 if spend is not None: reasons.append("client spend recorded")
 if job_type=="hourly": reasons.append("hourly range recorded")
 elif fixed is not None: reasons.append("fixed budget recorded")
 result={"job_id":str(job.get("job_id") or re.sub(r"[^a-zA-Z0-9]","",url)[-24:]),"title":title,"url":url,"job_type":job_type,"skills_matched":matched,"proposals":job.get("proposals"),"client_payment_verified":verified,"client_total_spent_usd":spend,"client_rating":rating,"hourly_min_usd":hmin,"hourly_max_usd":hmax,"fixed_budget_usd":fixed,"score":score,"decision":"apply_review" if score>=65 else "watch_or_skip","reasons":reasons,"human_approval_required":True,"connects_spend_allowed":False,"auto_submit":False,"captured_at":datetime.now(timezone.utc).isoformat()}
 return result,""

def build_proposal(job):
 title=str(job.get("title","your project")).strip()
 skills=job.get("skills_matched",{})
 labels=", ".join(skills.keys()) if isinstance(skills,dict) else "the requested workflow"
 message=(f"Hi,\n\nI reviewed your project, {title}. My proposed approach is to deliver a clear, tested solution focused on {labels}.\n\n"
 "I would first confirm the exact input format, expected output, volume and deadline. Then I would complete a small sample, validate it against your requirements, and deliver the finished work with a concise handover.\n\n"
 "I will confirm the scope and price with you before starting. I will not claim experience or results that I cannot demonstrate.\n\nBest regards")
 return {"message":message,"human_approval_required":True,"auto_submit":False,"connects_spend_allowed":False}

def process_inbox(jobs):
 qualified,rejected=[],{}
 for job in jobs:
  result,reason=evaluate_job(job)
  if result:
   result["proposal_draft"]=build_proposal(result)
   qualified.append(result)
  else: rejected[reason]=rejected.get(reason,0)+1
 qualified.sort(key=lambda x:(x["decision"]=="apply_review",x["score"]),reverse=True)
 return {"updated_at":datetime.now(timezone.utc).isoformat(),"source":"manual_upwork_capture","source_policy":"No Upwork scraping, login automation, Connects purchase, or proposal submission.","candidate_count":len(jobs),"qualified_count":len(qualified),"rejected_by_reason":rejected,"opportunities":qualified[:50],"safety":{"auto_submit":False,"auto_spend":False,"human_approval_required":True}}

def main():
 jobs=[]
 if INBOX.exists():
  with INBOX.open(encoding="utf-8") as f: payload=json.load(f)
  jobs=payload if isinstance(payload,list) else payload.get("jobs",[])
 if REPORT.exists():
  with REPORT.open(encoding="utf-8") as f: report=json.load(f)
 else: report={}
 report["upwork"]=process_inbox(jobs)
 with REPORT.open("w",encoding="utf-8") as f: json.dump(report,f,ensure_ascii=False,indent=2)
 print("Upwork jobs captured:",len(jobs),"qualified:",report["upwork"]["qualified_count"])

if __name__=="__main__": main()
