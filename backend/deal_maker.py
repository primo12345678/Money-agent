import json
from datetime import datetime,timezone
INPUT="report.json"
def build_draft(item):
 a=item.get("analysis",{});offer=a.get("suggested_offer",{});title=item.get("title","your automation request");url=item.get("url","");price=offer.get("pilot_price_eur",149)
 message=("Hi,\n\n"+f"I came across your post, “{title}”, and wanted to ask whether you are still looking for help.\n\n"+"I build small, practical enquiry and workflow automations for small businesses. A first pilot can connect one agreed form or mailbox to a client-owned tracking sheet, send an acknowledgement, notify the owner and create a follow-up reminder.\n\n"+f"A tightly scoped pilot starts at €{price}; I would confirm the exact scope and final price with you before starting. I will not ask for sensitive customer data unless it is necessary and agreed in advance.\n\n"+"If this matches what you need, I can send a short scope and implementation plan.\n\nBest,\n[Your name]")
 return {"subject":"Quick question about your automation request","message":message,"source_post":url,"suggested_pilot_price_eur":price,"price_is_quote":False,"human_approval_required":True,"auto_send":False}
def main():
 with open(INPUT,encoding="utf-8") as f:report=json.load(f)
 drafts=[]
 for item in report.get("opportunities",[]):
  a=item.get("analysis",{})
  if a.get("eligible_for_human_review"):drafts.append({"title":item.get("title"),"url":item.get("url"),"source":item.get("source"),"priority":a.get("priority"),"opportunity_score":a.get("opportunity_score"),"offer":build_draft(item)})
 report["deal_maker"]={"status":"drafts_ready_for_human_review" if drafts else "no_qualified_drafts","created_at":datetime.now(timezone.utc).isoformat(),"auto_send":False,"draft_count":len(drafts),"drafts":drafts[:10]}
 with open(INPUT,"w",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
if __name__=="__main__":main()
