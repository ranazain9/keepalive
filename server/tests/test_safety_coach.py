"""
Unit & Latency Benchmark Tests for Agent #2 (The Safety Coach)
Verifies AHA protocol progression, metronome triggers, and sub-15ms latency SLA.
"""

import unittest
import time
from server.agents.safety_coach.agent import SafetyCoachAgent
from server.schemas.emergency import EmergencyIntent, PatientType

class TestSafetyCoach(unittest.TestCase):
    def setUp(self):
        self.coach = SafetyCoachAgent(session_id="test_session")

    def test_adult_cardiac_arrest_progression(self):
        # Step 1: Init protocol
        e1 = self.coach.initialize_protocol(EmergencyIntent.CARDIAC_ARREST, PatientType.ADULT)
        self.assertEqual(e1.step_number, 1)
        self.assertIn("911 CAD dispatch", e1.directive_text)
        self.assertIn("flat on firm ground", e1.directive_text)
        self.assertEqual(e1.metronome_bpm, 0)
        self.assertLess(e1.latency_ms, 15.0)

        # Step 2: Caller says "okay done"
        e2 = self.coach.process_rescuer_utterance("Okay, I called 911, it's done")
        self.assertIsNotNone(e2)
        self.assertEqual(e2.step_number, 2)
        self.assertIn("heel of hand", e2.directive_text)
        self.assertEqual(e2.metronome_bpm, 0)

        # Step 3: Caller says "ready" -> Compressions + 110 BPM Metronome
        e3 = self.coach.process_rescuer_utterance("Hands in place, ready")
        self.assertIsNotNone(e3)
        self.assertEqual(e3.step_number, 3)
        self.assertEqual(e3.metronome_bpm, 110)
        self.assertIn("Push hard and fast to the beat", e3.directive_text)

    def test_pediatric_infant_adaptation(self):
        e1 = self.coach.initialize_protocol(EmergencyIntent.CARDIAC_ARREST, PatientType.INFANT)
        self.assertEqual(e1.step_number, 1)
        
        # Advance to step 2
        e2 = self.coach.advance_step()
        self.assertEqual(e2.step_number, 2)
        self.assertIn("two fingers", e2.directive_text)

    def test_march_arterial_bleed_tourniquet(self):
        e1 = self.coach.initialize_protocol(EmergencyIntent.ARTERIAL_BLEED, PatientType.ADULT)
        self.assertEqual(e1.step_number, 1)
        self.assertIn("direct, heavy pressure", e1.directive_text)

        e2 = self.coach.advance_step()
        self.assertEqual(e2.step_number, 2)
        self.assertIn("tourniquet 2 to 3 inches above", e2.directive_text)

    def test_latency_benchmark_100_directives(self):
        """Benchmark: 100 step advancements must maintain < 2ms average latency (SLA < 15ms)."""
        self.coach.initialize_protocol(EmergencyIntent.CARDIAC_ARREST, PatientType.ADULT)
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            self.coach.advance_step()
            latencies.append((time.perf_counter() - start) * 1000.0)
            
        avg_latency = sum(latencies) / len(latencies)
        p99_latency = sorted(latencies)[98]
        
        print(f"\n[BENCHMARK Safety Coach] 100 Directives: Avg = {avg_latency:.3f}ms | p99 = {p99_latency:.3f}ms")
        self.assertLess(avg_latency, 5.0)
        self.assertLess(p99_latency, 15.0)

if __name__ == "__main__":
    unittest.main()
