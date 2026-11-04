import json
from datetime import datetime,timezone
INPUT="report.json"
OFFER={"name":"Lead Response Mini-System","pilot_price_eur":149,"standard_setup_price_eur":299,"monthly_support_price_eur":39,"scope":["Capture enquiries from one agreed form or mailbox","Log enquiries in a client-owned Google Sheet","Send an acknowledgement and notify the business owner","Create a simple follow-up reminder and status tracker"],"delivery_note":"Final scope, access, privacy terms and price must be agreed with the customer."}
LABELS={"ai_automation":"AI/workflow automation","lead_generation":"Lead capture and follow-up","customer_support":"Customer enquiry/support workflow","integration":"Email, form, spreadsheet or CRM integration"}
def analyze(item):
 category=item.get("service_category","integration");buyer=int(item.get("buyer_intent_score",0));services=item.get("service_signals",[]);buyers=item.get("buyer_signals",[]);budget=bool(item.get("explicit_budget"));age=item.get("age_days")
 recency=10 if age is None else max(0,10-int(age//2));specificity=min(10,len(services)*3+len(buyers)*2);budget_score=15 if budget else 0
 score=round(min(100,buyer*.40+min(25,len(services)*8)+budget_score+recency+specificity));priority="HIGH" if score>=80 else "MEDIUM" if score>=65 else "LOW";eligible=score>=65 and bool(buyers or budget)
 return {**item,"analysis":{"category":category,"category_label":LABELS.get(category,"Workflow automation"),"priority":priority,"opportunity_score":score,"score_components":{"buyer_intent":round(buyer*.40),"service_fit":min(25,len(services)*8),"explicit_budget":budget_score,"recency":recency,"specificity":specificity},"suggested_offer":OFFER,"suggested_pilot_price_eur":149,"price_is_our_test_offer_not_customer_budget":True,"eligible_for_human_review":eligible,"reason":"Relevant service signal plus explicit buyer-intent evidence. A human must verify the post and scope before contact."}}
def main():
 with open(INPUT,encoding="utf-8") as f:report=json.load(f)
 items=[analyze(x) for x in report.get("opportunities",[])];items.sort(key=lambda x:(x["analysis"]["eligible_for_human_review"],x["analysis"]["opportunity_score"],x.get("explicit_budget",False)),reverse=True);count=sum(x["analysis"]["eligible_for_human_review"] for x in items)
 report["mode"]="qualified_buyer_hunter_and_offer_analyst";report["generated_at"]=datetime.now(timezone.utc).isoformat();report["commercial_model"]={"offer":OFFER,"target":"One paid pilot, then repeatable setup and monthly support revenue","revenue_definition":"Only customer payments recorded as received count as revenue."};report["analysis"]={"status":"ready_for_human_review" if count else "no_qualified_leads","qualified_for_review":count,"total_candidates":len(items),"note":"No lead is contacted automatically. No revenue is claimed until payment is recorded."};report["opportunities"]=items
 with open(INPUT,"w",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
if __name__=="__main__":main()
