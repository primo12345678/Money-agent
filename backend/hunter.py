import html, json, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

SOURCES=[("Reddit r/forhire","https://www.reddit.com/r/forhire/new/.rss"),("Reddit r/DoneDirtCheap","https://www.reddit.com/r/DoneDirtCheap/new/.rss")]
MAX_AGE_DAYS=14
SERVICE_TERMS={"ai_automation":["ai automation","workflow automation","n8n","zapier","make.com","ai agent","automate","automation workflow"],"lead_generation":["lead generation","lead capture","lead follow-up","lead follow up","crm automation","sales automation"],"customer_support":["customer support automation","support chatbot","customer service chatbot","chatbot","ticket automation"],"integration":["api integration","google sheets automation","email automation","webhook","crm integration","integrate"]}
BUYER_SIGNALS=["looking for a freelancer","need a freelancer","seeking a freelancer","hiring a freelancer","freelancer needed","need someone to build","looking for someone to build","looking to hire a freelancer","contractor needed","paid project","fixed price project","fixed-price project","project budget","budget is","budget:","paying for","will pay for","freelance project","commissioned project"]
SELLER_TITLE_RE=re.compile(r"^\s*\[for hire\]",re.I)
EMPLOYMENT_SIGNALS=["full-time","full time","part-time","part time","annual salary","per annum","job opening","job vacancy","apply for this job","join our team","employment opportunity","benefits package","career opportunity","position is","salary range","internship","entry-level role","remote job","looking for a job"]
BUDGET_PATTERN=re.compile(r"(?:budget|project budget|pay|paying|fixed[- ]price|rate)[^\n]{0,35}(?:[$€£]\s*\d[\d,.]*|\d[\d,.]*\s*(?:USD|EUR|GBP))",re.I)
def fetch(url):
 r=urllib.request.Request(url,headers={"User-Agent":"MoneyAgent/2.0 (public opportunity research)"})
 with urllib.request.urlopen(r,timeout=25) as response:return response.read().decode("utf-8","ignore")
def clean(v):
 v=html.unescape(v or "");v=re.sub(r"<[^>]+>"," ",v);return re.sub(r"\s+"," ",v).strip()
def child_text(item,names):
 for n in item.iter():
  if n.tag.split("}")[-1] in set(names) and n.text:return n.text
 return ""
def item_link(item):
 for n in item.iter():
  if n.tag.split("}")[-1]=="link":
   v=n.attrib.get("href") or n.text
   if v and v.strip():return v.strip()
 return ""
def parse_date(v):
 if not v:return None
 try:
  d=parsedate_to_datetime(v)
  if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
  return d.astimezone(timezone.utc)
 except Exception:pass
 try:return datetime.fromisoformat(v.replace("Z","+00:00")).astimezone(timezone.utc)
 except Exception:return None
def classify_service(text):
 low=text.lower();hits={k:[t for t in ts if t in low] for k,ts in SERVICE_TERMS.items()};hits={k:v for k,v in hits.items() if v}
 if not hits:return None,[]
 k=max(hits,key=lambda x:len(hits[x]));return k,hits[k]
def buyer_signals(text):return [p for p in BUYER_SIGNALS if p in text.lower()]
def budget_signal(text):
 m=BUDGET_PATTERN.search(text);return clean(m.group(0)) if m else ""
def evaluate(title,description,published,url,source):
 combined=clean(f"{title} {description}");low=combined.lower();category,service_hits=classify_service(combined);buy_hits=buyer_signals(combined);employment=[t for t in EMPLOYMENT_SIGNALS if t in low];budget=budget_signal(combined)
 if employment:return None,"employment_listing"
 if SELLER_TITLE_RE.search(title):return None,"service_provider_listing"
 if not category:return None,"no_relevant_service"
 if not buy_hits and not budget:return None,"no_explicit_buyer_intent"
 age=None
 if published:
  age=max(0,(datetime.now(timezone.utc)-published).total_seconds()/86400)
  if age>MAX_AGE_DAYS:return None,"stale"
 score=min(100,45+12*len(buy_hits)+(15 if budget else 0))
 if "freelancer" in low or "freelance" in low or "contractor" in low:score=min(100,score+8)
 return {"source":source,"title":title,"url":url,"published":published.isoformat() if published else "","age_days":round(age,1) if age is not None else None,"snippet":clean(description)[:1200],"service_category":category,"service_signals":service_hits[:8],"buyer_signals":buy_hits[:8],"buyer_intent_score":score,"explicit_budget":bool(budget),"budget_signal":budget,"lead_type":"explicit_service_buyer_request","human_review_required":True},""
def parse_feed(xml_text,source):
 root=ET.fromstring(xml_text);items=[n for n in root.iter() if n.tag.split("}")[-1] in ("item","entry")];found=[];rejected={}
 for item in items:
  title=clean(child_text(item,["title"]));desc=clean(child_text(item,["description","summary","content","encoded"]));published=parse_date(clean(child_text(item,["pubDate","published","updated"])));url=item_link(item);lead,reason=evaluate(title,desc,published,url,source)
  if lead:found.append(lead)
  else:rejected[reason]=rejected.get(reason,0)+1
 return found,rejected
def main():
 opportunities=[];errors=[];rejected={}
 for source,url in SOURCES:
  try:
   found,skipped=parse_feed(fetch(url),source);opportunities.extend(found)
   for reason,count in skipped.items():rejected[reason]=rejected.get(reason,0)+count
  except Exception as error:errors.append({"source":source,"error":str(error)})
 seen=set();unique=[]
 for item in sorted(opportunities,key=lambda x:(x["buyer_intent_score"],x["explicit_budget"]),reverse=True):
  key=item.get("url") or item.get("title")
  if key and key not in seen:seen.add(key);unique.append(item)
 report={"generated_at":datetime.now(timezone.utc).isoformat(),"agent":"Money Agent","mode":"qualified_buyer_opportunity_hunter","commercial_goal":"Find genuine buyers for small-business workflow automation pilots","safety":{"auto_submit":False,"auto_signup":False,"auto_spend":False,"auto_send":False,"human_approval_required":True},"sources":[{"name":n,"url":u} for n,u in SOURCES],"quality_control":{"candidate_count":len(opportunities),"qualified_leads":len(unique),"rejected_by_reason":rejected,"employment_feeds_removed":True,"minimum_rule":"Relevant service signal plus explicit buyer intent or explicit budget; ordinary employment listings rejected."},"opportunities":unique[:50],"errors":errors}
 with open("report.json","w",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
if __name__=="__main__":main()
