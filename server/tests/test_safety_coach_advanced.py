"""
Advanced Clinical & Audio Tests for Agent #2 (Safety Coach)
Tests 2-minute fatigue swap alert, 30:2 breath cadence, depth targets,
Paramedic arrival trigger, and spoken voice directives.
"""

import unittest
import time
from server.agents.safety_coach.agent import SafetyCoachAgent
from server.schemas.emergency import EmergencyIntent, PatientType

class TestSafetyCoachAdvanced(unittest.TestCase):
    def setUp(self):
        self.coach = SafetyCoachAgent(session_id="advanced_test_session")

    def test_spoken_voice_and_target_depth(self):
        # Adult CPR Step 3
        self.coach.initialize_protocol(EmergencyIntent.CARDIAC_ARREST, PatientType.ADULT)
        self.coach.advance_step() # Step 2
        e3 = self.coach.advance_step() # Step 3
        
        self.assertEqual(e3.step_number, 3)
        self.assertGreater(len(e3.spoken_voice_text), 0, "Must provide natural spoken voice text")
        self.assertEqual(e3.target_depth_inches, 2.2, "Adult target depth must be 2.2 inches (2-2.4 in range)")
        self.assertEqual(e3.cadence_mode, "CONTINUOUS_110BPM")

    def test_pediatric_infant_30_2_cadence(self):
        self.coach.initialize_protocol(EmergencyIntent.CARDIAC_ARREST, PatientType.INFANT)
        self.coach.advance_step()
        e3 = self.coach.advance_step()
        
        self.assertEqual(e3.cadence_mode, "CYCLE_30_2", "Infant protocol must specify 30:2 cycle mode")
        self.assertEqual(e3.target_depth_inches, 1.5, "Infant depth must be 1.5 inches")

    def test_2_minute_fatigue_rescuer_swap(self):
        self.coach.initialize_protocol(EmergencyIntent.CARDIAC_ARREST, PatientType.ADULT)
        self.coach.advance_step()
        self.coach.advance_step() # CPR started
        
        # Simulate 121 seconds elapsed
        self.coach.state.cpr_started_at = time.time() - 121.0
        
        should_swap, elapsed, comp_count = self.coach.check_fatigue_swap_status()
        self.assertTrue(should_swap, "Must trigger rescuer swap at 2 minutes")
        self.assertGreaterEqual(comp_count, 200, "Estimated compressions should be ~220")

    def test_paramedic_arrival_halts_metronome(self):
        self.coach.initialize_protocol(EmergencyIntent.CARDIAC_ARREST, PatientType.ADULT)
        self.coach.advance_step()
        self.coach.advance_step()
        self.assertTrue(self.coach.state.metronome_active)
        
        # Voice cue: "Paramedics are here!"
        e_arrival = self.coach.process_rescuer_utterance("Paramedics are here right now!")
        self.assertIsNotNone(e_arrival)
        self.assertEqual(e_arrival.step_number, 99)
        self.assertFalse(self.coach.state.metronome_active, "Metronome must be halted on EMS arrival")
        self.assertTrue(self.coach.state.paramedics_arrived)

    def test_audio_spec_metronome_and_ducking(self):
        """Validates partner audio specification: 3 kHz metronome frequency and -4.0 dB ducking."""
        self.coach.initialize_protocol(EmergencyIntent.CARDIAC_ARREST, PatientType.ADULT)
        self.coach.advance_step()
        e3 = self.coach.advance_step()
        self.assertEqual(e3.metronome_freq_hz, 3000, "Must be 3000 Hz piercing frequency")
        self.assertEqual(e3.ducking_db, -4.0, "Must be -4.0 dB ducking gain")

    def test_latency_benchmark_sub_15ms(self):
        self.coach.initialize_protocol(EmergencyIntent.CARDIAC_ARREST, PatientType.ADULT)
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            self.coach.advance_step()
            latencies.append((time.perf_counter() - start) * 1000.0)

        avg_latency = sum(latencies) / len(latencies)
        print(f"\n[BENCHMARK Safety Coach Advanced] 100 Directives Avg: {avg_latency:.3f}ms")
        self.assertLess(avg_latency, 5.0)

if __name__ == "__main__":
    unittest.main()
