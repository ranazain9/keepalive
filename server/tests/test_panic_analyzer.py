"""
Unit & Benchmark Tests for Multi-Modal Panic Analyzer
Tests linguistic scoring, speech velocity (WPM), acoustic RMS, and tension decay.
"""

import unittest
import struct
from server.agents.triage.panic_analyzer import PanicAnalyzer

class TestPanicAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = PanicAnalyzer()

    def test_linguistic_terror_markers(self):
        text = "Oh god help me, he is dying, somebody please help!"
        score = self.analyzer.calculate_linguistic_score(text)
        self.assertGreaterEqual(score, 0.70, "Terror markers + repetitions must yield high panic")

    def test_speech_velocity_wpm(self):
        # 15 words in 3.0 seconds = 300 WPM (Extreme rushing / panic)
        wpm_bonus = self.analyzer.calculate_wpm_score(15, 3.0)
        self.assertEqual(wpm_bonus, 0.25)
        
        # 4 words in 2.0 seconds = 120 WPM (Normal speech)
        normal_bonus = self.analyzer.calculate_wpm_score(4, 2.0)
        self.assertEqual(normal_bonus, 0.0)

    def test_acoustic_rms_energy(self):
        # Synthesize silence (zero amplitude)
        silence_pcm = struct.pack("<100h", *([0] * 100))
        rms_silence = self.analyzer.calculate_acoustic_rms(silence_pcm)
        self.assertEqual(rms_silence, 0.0)
        
        # Synthesize loud shouting (peak amplitude samples +/- 30000)
        shouting_samples = [30000 if i % 2 == 0 else -30000 for i in range(100)]
        shouting_pcm = struct.pack("<100h", *shouting_samples)
        rms_shout = self.analyzer.calculate_acoustic_rms(shouting_pcm)
        self.assertGreaterEqual(rms_shout, 0.80)

    def test_cpr_tension_decay(self):
        text = "Help me please, he is unresponsive!"
        initial_panic = self.analyzer.calculate_composite_panic(text, cpr_cycles=0)
        cpr_cycle_3_panic = self.analyzer.calculate_composite_panic(text, cpr_cycles=3)
        
        self.assertLess(cpr_cycle_3_panic, initial_panic, "Panic score must decay as CPR cycles progress")

if __name__ == "__main__":
    unittest.main()
