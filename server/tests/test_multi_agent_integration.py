"""
End-to-End Multi-Agent Integration Tests for KeepAlive
Validates coordination between:
- Agent #1: Triage Agent (Semantic classification, context, physiology, distress)
- Agent #2: Safety Coach Agent (Deterministic AHA protocols, 110 BPM metronome, step progression)
- Agent #3: Companion Agent (Bounded micro-Q&A <=18 words, grounding, paramedic EMS handoff)
- Tools: CAD emergency dispatch and AED locator
"""

import unittest
import time
from server.main import process_rescue_utterance, triage_agent, safety_coach, companion_agent
from server.schemas.emergency import EmergencyIntent, PatientType, TriageAction

class TestMultiAgentIntegration(unittest.TestCase):
    def setUp(self):
        triage_agent.reset()
        safety_coach.reset()

    def test_full_cardiac_arrest_rescue_cycle(self):
        """
        Tests complete real-world multi-turn rescue flow:
        1. Collapse with C-Spine trauma + agonal breathing + bystanders
        2. Affirmation step advancement to posture
        3. Ready affirmation to 110 BPM compressions
        4. In-crisis panic Q&A without disrupting metronome
        5. Paramedic arrival, metronome stop, and EMS handoff card generation
        """
        # Turn 1: Initial emergency declaration
        turn1 = process_rescue_utterance(
            "Help! My dad just fell down the stairs and hit his head! He collapsed, not breathing and making strange snoring gasping sounds! My brother is here with me!"
        )
        triage1 = turn1["triage"]
        directive1 = turn1["directive"]
        cad1 = turn1["cad_dispatch"]
        aed1 = turn1["aed_info"]

        # Verify Agent 1 (Triage)
        self.assertEqual(triage1.intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertEqual(triage1.action, TriageAction.LOCK_PROTOCOL)
        self.assertTrue(triage1.c_spine_risk, "Must identify cervical spine trauma from fall down stairs")
        self.assertTrue(triage1.is_agonal_breathing, "Must detect agonal snoring/gasping sounds")
        self.assertEqual(triage1.bystander_status, "MULTIPLE_PRESENT")

        # Verify Agent 2 (Safety Coach initialization)
        self.assertIsNotNone(directive1)
        self.assertEqual(directive1.step_number, 1)
        self.assertIn("flat on firm ground", directive1.directive_text)
        self.assertEqual(directive1.metronome_bpm, 0)
        self.assertTrue(safety_coach.state.is_locked)
        self.assertEqual(safety_coach.state.active_intent, EmergencyIntent.CARDIAC_ARREST)

        # Verify CAD and AED tools triggered
        self.assertIsNotNone(cad1)
        self.assertEqual(cad1["status"], "DISPATCH_CONFIRMED")
        self.assertIn("Medic-4", cad1["assigned_units"])
        self.assertIsNotNone(aed1)
        self.assertEqual(aed1["status"], "AED_LOCATED")

        # Turn 2: Caller confirms 911 called
        turn2 = process_rescue_utterance("Okay, I called 911 on speaker, it's done!")
        directive2 = turn2["directive"]
        self.assertIsNotNone(directive2)
        self.assertEqual(directive2.step_number, 2)
        self.assertIn("heel of hand", directive2.directive_text)
        self.assertEqual(directive2.metronome_bpm, 0)

        # Turn 3: Caller confirms hands placed -> Compressions active at 110 BPM
        turn3 = process_rescue_utterance("Hands placed in center of chest, ready!")
        directive3 = turn3["directive"]
        self.assertIsNotNone(directive3)
        self.assertEqual(directive3.step_number, 3)
        self.assertEqual(directive3.metronome_bpm, 110)
        self.assertEqual(directive3.target_depth_inches, 2.2)
        self.assertTrue(safety_coach.state.metronome_active)

        # Turn 4: Caller asks panic Q&A during active compressions
        turn4 = process_rescue_utterance("I heard a loud pop, did I break a rib?!")
        directive4 = turn4["directive"]
        companion_ans4 = turn4["companion_answer"]

        # Metronome & step 3 must stay locked without pause
        self.assertIsNotNone(directive4)
        self.assertEqual(directive4.step_number, 3)
        self.assertEqual(directive4.metronome_bpm, 110)

        # Companion answers <= 18 words
        self.assertIsNotNone(companion_ans4)
        self.assertTrue(any(w in companion_ans4.lower() for w in ["rib", "pop", "break", "push", "beat"]))
        word_count4 = len(companion_ans4.split())
        self.assertLessEqual(word_count4, 18, "Companion response must strictly adhere to <=18 words")

        # Turn 5: Caller expresses exhaustion
        turn5 = process_rescue_utterance("Can I stop for a second, my arms hurt?")
        companion_ans5 = turn5["companion_answer"]
        self.assertIsNotNone(companion_ans5)
        self.assertTrue(any(w in companion_ans5.lower() for w in ["stop", "push", "beat", "great", "keep"]))
        self.assertLessEqual(len(companion_ans5.split()), 18)

        # Turn 6: Paramedics arrive -> Metronome halts, EMS handoff card created
        # Simulate some CPR time
        safety_coach.state.cpr_started_at = time.time() - 95.0

        turn6 = process_rescue_utterance("Paramedics are here! The ambulance just arrived!")
        directive6 = turn6["directive"]
        handoff6 = turn6["handoff_card"]

        # Directive 6: step 99 arrival, metronome stopped
        self.assertIsNotNone(directive6)
        self.assertEqual(directive6.step_number, 99)
        self.assertEqual(directive6.metronome_bpm, 0)
        self.assertFalse(safety_coach.state.metronome_active)
        self.assertTrue(safety_coach.state.paramedics_arrived)

        # EMS Handoff card validation
        self.assertIsNotNone(handoff6)
        self.assertEqual(handoff6.primary_intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertEqual(handoff6.patient_type, PatientType.ADULT)
        self.assertTrue(handoff6.c_spine_trauma_risk, "Handoff card must retain C-spine risk from initial fall")
        self.assertTrue(handoff6.agonal_breathing_detected, "Handoff card must retain agonal breathing from initial presentation")
        self.assertEqual(handoff6.bystander_status, "MULTIPLE_PRESENT")
        self.assertGreater(handoff6.total_compressions_delivered, 0)
        self.assertGreater(len(handoff6.spoken_handoff_summary), 0)
        self.assertEqual(handoff6.spoken_report, handoff6.spoken_handoff_summary)

    def test_pediatric_infant_choking_and_escalation(self):
        """
        Tests pediatric flow and dynamic escalation.
        """
        # 1. Infant choking
        turn1 = process_rescue_utterance("My 6-month-old baby is choking and cannot make any sound!")
        triage1 = turn1["triage"]
        directive1 = turn1["directive"]
        self.assertEqual(triage1.intent, EmergencyIntent.CHOKING)
        self.assertEqual(triage1.patient_type, PatientType.INFANT)
        self.assertIsNotNone(directive1)
        self.assertEqual(directive1.step_number, 1)

        # 2. Advance to step 2: back slaps
        turn2 = process_rescue_utterance("Okay, 911 called on speaker, what next?")
        directive2 = turn2["directive"]
        self.assertIsNotNone(directive2)
        self.assertEqual(directive2.step_number, 2)
        self.assertIn("back slaps", directive2.directive_text.lower())

    def test_march_compound_trauma_bleed_priority(self):
        """
        Tests MARCH compound trauma: massive bleeding prioritized over cardiac arrest.
        """
        turn = process_rescue_utterance(
            "He was stabbed on his right leg, arterial blood is spurting everywhere and he passed out cold not breathing!"
        )
        triage = turn["triage"]
        directive = turn["directive"]
        self.assertEqual(triage.intent, EmergencyIntent.ARTERIAL_BLEED)
        self.assertEqual(triage.detected_limb, "RIGHT_LEG")
        self.assertIsNotNone(directive)
        self.assertIn("heavy pressure", directive.directive_text.lower())

    def test_session_reset(self):
        """
        Tests session reset functionality.
        """
        process_rescue_utterance("Help, he is not breathing!")
        self.assertTrue(safety_coach.state.is_locked)

        triage_agent.reset()
        safety_coach.reset()

        self.assertFalse(safety_coach.state.is_locked)
        self.assertIsNone(safety_coach.state.active_intent)
        self.assertEqual(len(triage_agent.memory.history), 0)

if __name__ == "__main__":
    unittest.main()
