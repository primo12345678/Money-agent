import unittest
from backend.upwork_hunter import evaluate_job, build_proposal, process_inbox

class UpworkHunterTests(unittest.TestCase):
 def valid_job(self, **overrides):
  job={"job_id":"job-1","title":"Google Sheets lead tracker","description":"Build a spreadsheet dashboard for lead generation and follow-up tracking.","url":"https://www.upwork.com/jobs/job-1","job_type":"hourly","hourly_min":12,"hourly_max":20,"proposals":"Less than 5","payment_verified":True,"client_total_spent":1200,"client_rating":4.9,"skills":"Google Sheets, Excel, CRM"}
  job.update(overrides)
  return job
 def test_qualifies_relevant_profitable_job(self):
  result,reason=evaluate_job(self.valid_job())
  self.assertEqual(reason,"")
  self.assertEqual(result["decision"],"apply_review")
  self.assertGreaterEqual(result["score"],65)
  self.assertFalse(result["auto_submit"])
 def test_rejects_low_hourly_rate(self):
  result,reason=evaluate_job(self.valid_job(hourly_min=3,hourly_max=3.5))
  self.assertIsNone(result)
  self.assertEqual(reason,"hourly_rate_below_profit_floor")
 def test_rejects_non_upwork_url(self):
  result,reason=evaluate_job(self.valid_job(url="https://example.com/job"))
  self.assertIsNone(result)
  self.assertEqual(reason,"missing_required_fields_or_non_upwork_url")
 def test_rejects_unrelated_job(self):
  result,reason=evaluate_job(self.valid_job(title="TikTok slideshow creator",description="Create social media videos",skills="TikTok"))
  self.assertIsNone(result)
  self.assertEqual(reason,"no_skill_fit")
 def test_proposal_requires_approval_and_makes_no_claims(self):
  result,_=evaluate_job(self.valid_job())
  proposal=build_proposal(result)
  self.assertTrue(proposal["human_approval_required"])
  self.assertFalse(proposal["auto_submit"])
  self.assertIn("cannot demonstrate",proposal["message"])
 def test_process_inbox_counts_and_scores(self):
  report=process_inbox([self.valid_job(),self.valid_job(hourly_min=3,hourly_max=3.5)])
  self.assertEqual(report["candidate_count"],2)
  self.assertEqual(report["qualified_count"],1)
  self.assertFalse(report["safety"]["auto_spend"])

if __name__=="__main__": unittest.main()
