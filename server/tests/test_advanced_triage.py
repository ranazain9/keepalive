"""
Advanced Intelligence Unit & Benchmark Tests for Agent #1
Tests Fuzzy/Phonetic tolerance, Bystander delegation, C-Spine trauma risk,
Dynamic protocol escalation, and Multi-lingual recognition.
"""

import unittest
import time
from server.agents.triage.agent import TriageAgent
from server.schemas.emergency import EmergencyIntent, TriageAction

class TestAdvancedTriage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = TriageAgent()

    def setUp(self):
        self.agent.memory.clear()
        self.agent.previous_locked_intent = None
        self.agent.pending_probe_intent = None

    def test_fuzzy_noisy_stt_tolerance(self):
        """Test noisy/distorted words: 'dad is clapse and not breathin'"""
        phrase = "Help! My dad is clapse on the floor and not breathin!"
        res = self.agent.classify(phrase)
        self.assertEqual(res.intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertEqual(res.action, TriageAction.LOCK_PROTOCOL)

    def test_bystander_resource_delegation(self):
        """Test bystander detection: delegates 911 & AED to bystander"""
        phrase = "My grandfather collapsed and is not breathing! My brother and mom are here with me!"
        res = self.agent.classify(phrase)
        self.assertEqual(res.intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertEqual(res.bystander_status, "MULTIPLE_PRESENT")
        self.assertIn("Direct the person with you to call 911 and find an AED", res.line_1_directive)

    def test_cspine_trauma_safeguard(self):
        """Test mechanical trauma: prevents dangerous neck tilting"""
        phrase = "He fell down the stairs from the roof, unconscious and not breathing!"
        res = self.agent.classify(phrase)
        self.assertEqual(res.intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertTrue(res.c_spine_risk, "Must detect cervical spine trauma risk")
        self.assertIn("Do NOT twist neck", res.line_1_directive)

    def test_location_aware_dispatch_directive(self):
        """Test GPS/Address location incorporation into Agent #1 result and directive"""
        phrase = "He collapsed in the kitchen not breathing!"
        loc = "742 Evergreen Terrace, Springfield"
        res = self.agent.classify(phrase, location=loc)
        self.assertEqual(res.intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertEqual(res.verified_location, loc)
        self.assertIn(loc, res.line_1_directive)

    def test_choking_to_unconscious_escalation(self):
        """Test choking victim passing out -> Escalates to CPR compressions"""
        # 1. Choking first
        r1 = self.agent.classify("My friend is choking on a piece of steak!")
        self.assertEqual(r1.intent, EmergencyIntent.CHOKING)
        
        # 2. He passes out
        r2 = self.agent.classify("He just turned purple and lost consciousness, went limp!")
        self.assertEqual(r2.intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertTrue(r2.is_escalated, "Must flag protocol escalation")
        self.assertIn("Choking victim has collapsed", r2.line_1_directive)

    def test_spanish_emergency_recognition(self):
        """Test Spanish emergency crisis anchors"""
        phrase = "Ayuda por favor, mi padre se cayo y no respira!"
        res = self.agent.classify(phrase)
        self.assertEqual(res.intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertEqual(res.detected_language, "es")
        self.assertEqual(res.action, TriageAction.LOCK_PROTOCOL)

    def test_urdu_hindi_emergency_recognition(self):
        """Test Urdu/Hindi emergency crisis anchors"""
        phrase = "Madad karo bhai, bohot khoon beh raha hai deep wound se!"
        res = self.agent.classify(phrase)
        self.assertEqual(res.intent, EmergencyIntent.ARTERIAL_BLEED)
        self.assertEqual(res.detected_language, "ur/hi")

    def test_sub_10ms_latency_benchmark_100_runs(self):
        phrase = "Accident on stairs, unconscious, not breathing, brother is here!"
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            self.agent.classify(phrase)
            latencies.append((time.perf_counter() - start) * 1000.0)

        avg_latency = sum(latencies) / len(latencies)
        p99_latency = sorted(latencies)[98]

        print(f"\n[BENCHMARK Advanced Triage] 100 Runs: Avg = {avg_latency:.2f}ms | p99 = {p99_latency:.2f}ms")
        self.assertLess(avg_latency, 5.0)
        self.assertLess(p99_latency, 25.0)

if __name__ == "__main__":
    unittest.main()
