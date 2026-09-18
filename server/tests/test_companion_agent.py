"""
Unit & Latency Benchmark Tests for Agent #3 (The Companion Agent)
Tests Panic Micro-Q&A (<18 words), Grounding responses, and sub-15ms latency.
"""

import unittest
import time
from server.agents.companion.agent import CompanionAgent
from server.agents.companion.micro_qa_engine import MicroQAEngine

class TestCompanionAgent(unittest.TestCase):
    def setUp(self):
        self.companion = CompanionAgent(session_id="test_companion", prefer_llm=False)
        self.qa_engine = MicroQAEngine()

    def test_live_groq_llm_generation(self):
        groq_companion = CompanionAgent(session_id="groq_test", prefer_llm=True)
        if groq_companion.llm_engine.groq_key:
            ans = groq_companion.process_utterance("I am so scared of breaking ribs", cpr_active=True)
            self.assertIsNotNone(ans)
            self.assertLessEqual(len(ans.split()), 18)
            self.assertTrue(ans.lower().endswith("beat.") or ans.lower().endswith("beat"))

    def test_rib_cracking_micro_qa_under_18_words(self):
        query = "I think I broke a rib, am I pressing too hard?"
        ans = self.companion.process_utterance(query)
        self.assertIsNotNone(ans)
        self.assertTrue("Rib popping" in ans or "rib pop" in ans.lower())
        word_count = len(ans.split())
        self.assertLessEqual(word_count, 18, "Answers must strictly be 18 words or fewer")

    def test_mouth_to_mouth_qa_under_18_words(self):
        query = "Should I give him mouth to mouth breathing?"
        ans = self.companion.process_utterance(query)
        self.assertIsNotNone(ans)
        self.assertIn("Hands-only CPR is just as effective", ans)
        self.assertLessEqual(len(ans.split()), 18)

    def test_stopping_exhaustion_qa(self):
        query = "Can I stop for a second, my arms hurt?"
        ans = self.companion.process_utterance(query)
        self.assertIsNotNone(ans)
        self.assertIn("Do not stop compressions", ans)
        self.assertLessEqual(len(ans.split()), 18)

    def test_emotional_grounding(self):
        query = "Oh god, I'm so scared I'm going to kill him!"
        ans = self.companion.process_utterance(query)
        self.assertIsNotNone(ans)
        self.assertIn("doing everything right", ans)
        self.assertLessEqual(len(ans.split()), 18)

    def test_expanded_grounding_crying_shaking(self):
        ans1 = self.companion.process_utterance("I am shaking so bad, help me!")
        self.assertIsNotNone(ans1)
        self.assertLessEqual(len(ans1.split()), 18)

        ans2 = self.companion.process_utterance("I am freaking out!")
        self.assertIsNotNone(ans2)
        self.assertLessEqual(len(ans2.split()), 18)

    def test_good_samaritan_legal_qa(self):
        query = "Can I get sued for breaking his ribs?"
        ans = self.companion.process_utterance(query)
        self.assertIsNotNone(ans)
        self.assertIn("Good Samaritan", ans)
        self.assertLessEqual(len(ans.split()), 18)

    def test_expose_bare_chest_qa(self):
        query = "Should I take his shirt off?"
        ans = self.companion.process_utterance(query)
        self.assertIsNotNone(ans)
        self.assertIn("bare chest", ans)
        self.assertLessEqual(len(ans.split()), 18)

    def test_untrained_novice_qa(self):
        query = "I don't know CPR, I've never done this!"
        ans = self.companion.process_utterance(query)
        self.assertIsNotNone(ans)
        self.assertIn("guide you", ans)
        self.assertIn("push to the beat", ans)
        self.assertLessEqual(len(ans.split()), 18)

    def test_too_late_doubt_qa(self):
        query = "Is it too late to save him?"
        ans = self.companion.process_utterance(query)
        self.assertIsNotNone(ans)
        self.assertIn("never too late", ans)
        self.assertLessEqual(len(ans.split()), 18)

    def test_ambulance_dispatch_status_qa(self):
        query = "Did you call 911? Where is the ambulance?"
        ans = self.companion.process_utterance(query)
        self.assertIsNotNone(ans)
        self.assertIn("911 CAD dispatch has been alerted", ans)
        self.assertLessEqual(len(ans.split()), 18)

    def test_patient_moan_sound_qa(self):
        query = "He just groaned and made a sound!"
        ans = self.companion.process_utterance(query)
        self.assertIsNotNone(ans)
        self.assertIn("Do not stop", ans)
        self.assertLessEqual(len(ans.split()), 18)

    def test_section_4_safety_gate_blocks_forbidden(self):
        from server.agents.companion.micro_qa_engine import enforce_section_4_safety_gate
        dangerous = "You can stop compressions now and take a rest."
        safe = enforce_section_4_safety_gate(dangerous)
        self.assertNotIn("stop compressions", safe.lower().replace("do not stop compressions", ""))
        self.assertIn("Do not stop compressions", safe)
        self.assertLessEqual(len(safe.split()), 18)

    def test_agent_identity_and_presence(self):
        ans1 = self.companion.process_utterance("Agent 3, are you there?", cpr_active=False)
        self.assertIsNotNone(ans1)
        self.assertIn("Agent 3", ans1)
        self.assertLessEqual(len(ans1.split()), 18)

        ans2 = self.companion.process_utterance("Agent 3", cpr_active=True)
        self.assertIsNotNone(ans2)
        self.assertIn("Agent 3", ans2)
        self.assertIn("push to the beat", ans2)
        self.assertLessEqual(len(ans2.split()), 18)

    def test_context_aware_help_me(self):
        # When CPR not active: asks for breathing/consciousness status
        ans_idle = self.companion.process_utterance("Hello, will you help me?", cpr_active=False)
        self.assertIsNotNone(ans_idle)
        self.assertIn("awake and breathing", ans_idle)
        self.assertLessEqual(len(ans_idle.split()), 18)

        # When CPR active: guides rescuer to keep pushing to the beat
        ans_cpr = self.companion.process_utterance("Help me!", cpr_active=True)
        self.assertIsNotNone(ans_cpr)
        self.assertIn("Keep pushing to the beat", ans_cpr)
        self.assertLessEqual(len(ans_cpr.split()), 18)

    def test_technique_verification(self):
        ans = self.companion.process_utterance("Am I doing this right?")
        self.assertIsNotNone(ans)
        self.assertIn("doing great", ans)
        self.assertLessEqual(len(ans.split()), 18)

    def test_asr_lips_cracking_normalization(self):
        # Handles AssemblyAI phonetic misinterpretation of 'ribs cracking' as 'lips cracking'
        ans = self.companion.process_utterance("Lips cracking!")
        self.assertIsNotNone(ans)
        self.assertTrue("Rib popping" in ans or "rib pop" in ans.lower())
        self.assertLessEqual(len(ans.split()), 18)

    def test_what_to_do_next_context(self):
        ans_cpr = self.companion.process_utterance("What do I do now?", cpr_active=True)
        self.assertIsNotNone(ans_cpr)
        self.assertIn("chest compressions", ans_cpr)
        self.assertLessEqual(len(ans_cpr.split()), 18)

        ans_assess = self.companion.process_utterance("What do I do?", cpr_active=False)
        self.assertIsNotNone(ans_assess)
        self.assertIn("awake", ans_assess)
        self.assertLessEqual(len(ans_assess.split()), 18)

    def test_qa_latency_benchmark_sub_15ms(self):
        query = "Where do my hands go on his chest?"
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            self.companion.process_utterance(query)
            latencies.append((time.perf_counter() - start) * 1000.0)

        avg_latency = sum(latencies) / len(latencies)
        print(f"\n[BENCHMARK Companion QA] 100 Runs Avg: {avg_latency:.3f}ms")
        self.assertLess(avg_latency, 15.0)

if __name__ == "__main__":
    unittest.main()
