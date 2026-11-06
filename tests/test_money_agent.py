import unittest
from datetime import datetime,timezone
from backend.hunter import evaluate,budget_signal
from backend.analyst import analyze
class HunterTests(unittest.TestCase):
 def test_rejects_job(self):
  lead,reason=evaluate("Remote AI Automation Engineer","Full-time role. Salary range $120,000. Join our team.",datetime.now(timezone.utc),"https://example.com/job","test")
  self.assertIsNone(lead);self.assertEqual(reason,"employment_listing")
 def test_rejects_for_hire_service_provider(self):
  lead,reason=evaluate("[For Hire] AI engineer – AI agents and workflow automation","I am looking for freelance work. Rate: $20/hr. Portfolio available.",datetime.now(timezone.utc),"https://example.com/for-hire","test")
  self.assertIsNone(lead);self.assertEqual(reason,"service_provider_listing")
 def test_accepts_paid_project(self):
  lead,reason=evaluate("[Hiring] Freelance n8n automation","Looking for a freelancer for a paid project. Budget is €500.",datetime.now(timezone.utc),"https://example.com/project","test")
  self.assertEqual(reason,"");self.assertIsNotNone(lead);self.assertTrue(lead["explicit_budget"])
 def test_rejects_generic_ai_post(self):
  lead,reason=evaluate("AI automation ideas","I am researching workflow automation tools.",datetime.now(timezone.utc),"https://example.com/post","test")
  self.assertIsNone(lead);self.assertEqual(reason,"no_explicit_buyer_intent")
 def test_salary_not_project_budget(self):self.assertEqual(budget_signal("Salary is $120,000 per year"),"")
class AnalystTests(unittest.TestCase):
 def test_offer_not_customer_budget(self):
  item={"service_category":"ai_automation","buyer_intent_score":80,"service_signals":["n8n","workflow automation"],"buyer_signals":["need a freelancer"],"explicit_budget":False,"age_days":1}
  a=analyze(item)["analysis"];self.assertTrue(a["price_is_our_test_offer_not_customer_budget"]);self.assertEqual(a["suggested_pilot_price_eur"],149)
if __name__=="__main__":unittest.main()
