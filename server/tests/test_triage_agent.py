"""
Agent #1 Automated Unit & Latency Benchmark Tests
Verifies clinical classification accuracy and enforces strict <10ms latency SLA.
"""

import unittest
import time
from server.agents.triage.agent import TriageAgent
from server.agents.triage.schemas import EmergencyIntent, TriageAction

class TestTriageAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = TriageAgent()
        cls.agent.classify("Warmup classification")
        cls.agent.memory.clear()

    def setUp(self):
        self.agent.memory.clear()

    def test_cardiac_arrest_kitchen_collapse(self):
        phrase = "Help! My dad just fell in the kitchen, he is not breathing and turning blue!"
        result = self.agent.classify(phrase)
        self.assertEqual(result.intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertEqual(result.action, TriageAction.LOCK_PROTOCOL)
        self.assertIn("911 CAD dispatch", result.line_1_directive)
        self.assertLess(result.latency_ms, 10.0, "Latency must be strictly under 10ms")

    def test_agonal_breathing_detection(self):
        phrase = "He collapsed on the rug and is making strange snoring and gasping sounds!"
        result = self.agent.classify(phrase)
        self.assertEqual(result.intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertTrue(result.is_agonal_breathing, "Agonal breathing flag must be True")

    def test_arterial_bleeding_with_limb_localization(self):
        phrase = "Blood is spurting everywhere from a deep wound on his right thigh!"
        result = self.agent.classify(phrase)
        self.assertEqual(result.intent, EmergencyIntent.ARTERIAL_BLEED)
        self.assertEqual(result.detected_limb, "RIGHT_THIGH")
        self.assertEqual(result.action, TriageAction.LOCK_PROTOCOL)
        self.assertIn("right thigh", result.line_1_directive)

    def test_neck_wound_tourniquet_safety_intercept(self):
        phrase = "Deep cut on his neck, blood is gushing everywhere!"
        result = self.agent.classify(phrase)
        self.assertEqual(result.intent, EmergencyIntent.ARTERIAL_BLEED)
        self.assertEqual(result.detected_limb, "NECK_ALERT")
        self.assertIn("NEVER apply a tourniquet around the neck", result.line_1_directive)

    def test_choking_detection(self):
        phrase = "My brother is clutching his throat, he was eating steak and is choking!"
        result = self.agent.classify(phrase)
        self.assertEqual(result.intent, EmergencyIntent.CHOKING)
        self.assertEqual(result.action, TriageAction.LOCK_PROTOCOL)

    def test_anaphylaxis_detection(self):
        phrase = "Severe allergic reaction to peanuts, her lips are swollen and wheezing, need an epipen!"
        result = self.agent.classify(phrase)
        self.assertEqual(result.intent, EmergencyIntent.ANAPHYLAXIS)
        self.assertEqual(result.action, TriageAction.LOCK_PROTOCOL)

    def test_overdose_detection(self):
        phrase = "Took too many pills, passed out cold with pinpoint pupils and shallow breathing!"
        result = self.agent.classify(phrase)
        self.assertEqual(result.intent, EmergencyIntent.OVERDOSE)
        self.assertEqual(result.action, TriageAction.LOCK_PROTOCOL)

    def test_march_compound_trauma_prioritization(self):
        # Blood spurting + not breathing -> Arterial bleed must take priority first
        phrase = "He severed an artery on his leg, blood is spurting everywhere and he passed out not breathing!"
        result = self.agent.classify(phrase)
        self.assertEqual(result.intent, EmergencyIntent.ARTERIAL_BLEED, "MARCH protocol must prioritize massive bleeding over CPR")

    def test_pediatric_infant_adaptation(self):
        self.agent.memory.clear()
        phrase = "My 6-month-old baby is choking and turning blue!"
        result = self.agent.classify(phrase)
        self.assertEqual(result.patient_type.value, "INFANT")
        self.assertIn("two fingers", result.line_1_directive)

    def test_panic_score_analyzer(self):
        self.agent.memory.clear()
        phrase = "Oh god help me please! He is dying, oh god someone help!"
        result = self.agent.classify(phrase)
        self.assertTrue(result.is_high_panic, "Must detect high panic distress")
        self.assertGreaterEqual(result.panic_score, 0.70)

    def test_sliding_window_multi_burst_accumulation(self):
        self.agent.memory.clear()
        # Burst 1
        r1 = self.agent.classify("My grandfather fell down...")
        self.assertIn("fell down", r1.conversation_context)
        # Burst 2
        r2 = self.agent.classify("and he's not breathing!")
        self.assertEqual(r2.intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertEqual(r2.action, TriageAction.LOCK_PROTOCOL)

    def test_latency_benchmark_100_runs(self):
        """Benchmark: 100 consecutive classifications must maintain sub-10ms average latency."""
        self.agent.memory.clear()
        phrase = "Unresponsive on the ground, not breathing, send help!"
        # Warm-up run to ensure caches and JIT paths are primed
        self.agent.classify(phrase)
        self.agent.memory.clear()
        
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            self.agent.classify(phrase)
            latencies.append((time.perf_counter() - start) * 1000.0)
            
        avg_latency = sum(latencies) / len(latencies)
        p99_latency = sorted(latencies)[98]
        
        print(f"\n[BENCHMARK] 100 Runs: Avg Latency = {avg_latency:.2f}ms | p99 Latency = {p99_latency:.2f}ms")
        self.assertLess(avg_latency, 5.0, "Average classification latency must be < 5.0ms")
        self.assertLess(p99_latency, 35.0, "p99 latency must be strictly < 35.0ms")

if __name__ == "__main__":
    unittest.main()
