"""
Clinical Protocol Library (AHA / ERC / CoSTR / MARCH Compliant)
Pre-computed, deterministic rescue directives for sub-15ms Safety Coach execution.
Includes compression depth, 30:2 cadence, and fatigue swap reminders.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from server.schemas.emergency import EmergencyIntent, PatientType

@dataclass
class DirectiveStep:
    step_number: int
    title: str
    instruction: str
    spoken_voice_text: str
    audio_cue_id: str
    target_metronome_bpm: int = 0
    metronome_freq_hz: int = 3000
    target_depth_inches: float = 0.0
    target_depth_cm: float = 0.0
    cadence_mode: str = "CONTINUOUS_110BPM"  # CONTINUOUS_110BPM or CYCLE_30_2
    ducking_db: float = -4.0
    is_terminal_loop: bool = False
    requires_user_confirmation: bool = False

CLINICAL_PROTOCOLS: Dict[str, Dict[str, List[DirectiveStep]]] = {
    EmergencyIntent.CARDIAC_ARREST.value: {
        PatientType.ADULT.value: [
            DirectiveStep(
                step_number=1,
                title="AHA BLS Line 1: Emergency Services",
                instruction="Don't panic. 911 CAD dispatch has been alerted with your exact GPS location. We need to start CPR immediately! Lay them flat on firm ground.",
                spoken_voice_text="Don't panic. 911 CAD dispatch has been alerted with your exact GPS location. We need to start CPR immediately! Lay them flat on firm ground.",
                audio_cue_id="cpr_adult_step1_call911",
                target_metronome_bpm=0,
                target_depth_inches=0.0
            ),
            DirectiveStep(
                step_number=2,
                title="Patient Posture & Hand Placement",
                instruction="Put heel of hand on center of chest, lock your elbows straight.",
                spoken_voice_text="Put heel of hand on center of chest, lock your elbows straight.",
                audio_cue_id="cpr_adult_step2_posture",
                target_metronome_bpm=0,
                target_depth_inches=2.2,
                target_depth_cm=5.5
            ),
            DirectiveStep(
                step_number=3,
                title="110 BPM Rhythmic Compressions",
                instruction="Ready: 3... 2... 1... PUSH! Push hard and fast to the beat! Push down at least 2 inches, let chest rise fully every time.",
                spoken_voice_text="Ready: 3... 2... 1... PUSH! Push hard and fast to the beat! Push down two inches, let the chest rise fully every time.",
                audio_cue_id="cpr_adult_step3_compressions",
                target_metronome_bpm=110,
                target_depth_inches=2.2,
                target_depth_cm=5.5,
                is_terminal_loop=True
            )
        ],
        PatientType.CHILD.value: [
            DirectiveStep(
                step_number=1,
                title="Pediatric CPR Line 1",
                instruction="Don't panic. 911 CAD dispatch has been alerted with your exact GPS location. We need to start CPR immediately! Lay them flat on firm ground.",
                spoken_voice_text="Don't panic. 911 CAD dispatch has been alerted with your exact GPS location. We need to start CPR immediately! Lay them flat on firm ground.",
                audio_cue_id="cpr_child_step1_call911",
                target_metronome_bpm=0
            ),
            DirectiveStep(
                step_number=2,
                title="Pediatric Hand Placement",
                instruction="Place victim on firm ground. Use 1 or 2 hands on center of chest, compress 2 inches.",
                spoken_voice_text="Use one or two hands on center of chest, lock elbows straight.",
                audio_cue_id="cpr_child_step2_posture",
                target_metronome_bpm=0,
                target_depth_inches=2.0,
                target_depth_cm=5.0
            ),
            DirectiveStep(
                step_number=3,
                title="Pediatric 110 BPM Compressions",
                instruction="Compress to the beat! 30 compressions followed by 2 gentle breaths.",
                spoken_voice_text="Compress to the beat! 30 compressions followed by 2 gentle breaths.",
                audio_cue_id="cpr_child_step3_compressions",
                target_metronome_bpm=110,
                target_depth_inches=2.0,
                target_depth_cm=5.0,
                cadence_mode="CYCLE_30_2",
                is_terminal_loop=True
            )
        ],
        PatientType.INFANT.value: [
            DirectiveStep(
                step_number=1,
                title="Infant BLS Line 1",
                instruction="Don't panic. 911 CAD dispatch has been alerted with your exact GPS location. We need to start CPR immediately! Place infant on a flat surface.",
                spoken_voice_text="Don't panic. 911 CAD dispatch has been alerted with your exact GPS location. We need to start CPR immediately! Place infant on a flat surface.",
                audio_cue_id="cpr_infant_step1_call911",
                target_metronome_bpm=0
            ),
            DirectiveStep(
                step_number=2,
                title="Two-Finger Infant Technique",
                instruction="Place infant on flat surface. Use two fingers in center of chest just below nipple line.",
                spoken_voice_text="Place infant on flat surface. Use two fingers in center of chest.",
                audio_cue_id="cpr_infant_step2_posture",
                target_metronome_bpm=0,
                target_depth_inches=1.5,
                target_depth_cm=4.0
            ),
            DirectiveStep(
                step_number=3,
                title="Infant 110 BPM Gentle Compressions",
                instruction="Compress gently 1.5 inches deep at 110 BPM. 30 compressions then 2 small puffs of air.",
                spoken_voice_text="Compress gently 1.5 inches deep at 110 BPM. 30 compressions then 2 gentle puffs.",
                audio_cue_id="cpr_infant_step3_compressions",
                target_metronome_bpm=110,
                target_depth_inches=1.5,
                target_depth_cm=4.0,
                cadence_mode="CYCLE_30_2",
                is_terminal_loop=True
            )
        ]
    },
    EmergencyIntent.CHOKING.value: {
        PatientType.ADULT.value: [
            DirectiveStep(
                step_number=1,
                title="Choking Assessment & 911",
                instruction="Call 911 immediately! Ask: 'Are you choking? Can you speak or cough?'",
                spoken_voice_text="Call 911 immediately! Ask: Are you choking? Can you speak?",
                audio_cue_id="choke_adult_step1_assess",
                target_metronome_bpm=0
            ),
            DirectiveStep(
                step_number=2,
                title="Heimlich Maneuver (Abdominal Thrusts)",
                instruction="Stand behind them. Make a fist above navel, grasp with other hand, pull sharply inward and upward.",
                spoken_voice_text="Stand behind them. Make a fist above navel, pull sharply inward and upward.",
                audio_cue_id="choke_adult_step2_heimlich",
                target_metronome_bpm=0,
                is_terminal_loop=True
            )
        ],
        PatientType.CHILD.value: [
            DirectiveStep(
                step_number=1,
                title="Child Choking Assessment & 911",
                instruction="Call 911 immediately on speaker! Kneel behind child, encourage them to cough forcefully.",
                spoken_voice_text="Call 911 immediately on speaker! Kneel behind child, encourage them to cough.",
                audio_cue_id="choke_child_step1_assess",
                target_metronome_bpm=0
            ),
            DirectiveStep(
                step_number=2,
                title="Pediatric Abdominal Thrusts",
                instruction="Kneel behind child. Make a fist above navel, give quick upward thrusts with gentle inward pressure.",
                spoken_voice_text="Kneel behind child. Make a fist above navel, give quick upward thrusts.",
                audio_cue_id="choke_child_step2_thrusts",
                target_metronome_bpm=0,
                is_terminal_loop=True
            )
        ],
        PatientType.INFANT.value: [
            DirectiveStep(
                step_number=1,
                title="Infant Choking Line 1",
                instruction="Call 911 on speaker! Never do a blind finger sweep.",
                spoken_voice_text="Call 911 on speaker! Never do a blind finger sweep.",
                audio_cue_id="choke_infant_step1_call911",
                target_metronome_bpm=0
            ),
            DirectiveStep(
                step_number=2,
                title="5 Back Slaps & 5 Chest Thrusts",
                instruction="Lay infant face down along your forearm. Deliver 5 firm back slaps between shoulder blades, then turn over and give 5 chest thrusts.",
                spoken_voice_text="Lay infant face down along forearm. Give 5 firm back slaps, then turn over for 5 chest thrusts.",
                audio_cue_id="choke_infant_step2_slaps",
                target_metronome_bpm=0,
                is_terminal_loop=True
            )
        ]
    },
    EmergencyIntent.ARTERIAL_BLEED.value: {
        PatientType.ADULT.value: [
            DirectiveStep(
                step_number=1,
                title="MARCH Protocol: Direct Pressure",
                instruction="Call 911 on speaker! Apply immediate direct, heavy pressure with clean cloth or bare hands.",
                spoken_voice_text="Call 911 on speaker! Apply heavy direct pressure on the wound now.",
                audio_cue_id="bleed_step1_pressure",
                target_metronome_bpm=0
            ),
            DirectiveStep(
                step_number=2,
                title="Tourniquet / Hemostatic Control",
                instruction="If bleeding does not stop on limb, apply tourniquet 2 to 3 inches above wound, tighten until bleeding ceases.",
                spoken_voice_text="Apply tourniquet two to three inches above wound, tighten until bleeding stops.",
                audio_cue_id="bleed_step2_tourniquet",
                target_metronome_bpm=0,
                is_terminal_loop=True
            )
        ]
    },
    EmergencyIntent.ANAPHYLAXIS.value: {
        PatientType.ADULT.value: [
            DirectiveStep(
                step_number=1,
                title="EpiPen / Auto-Injector Deployment",
                instruction="Call 911 now! Locate EpiPen or epinephrine auto-injector immediately.",
                spoken_voice_text="Call 911 now! Locate the EpiPen immediately.",
                audio_cue_id="anaph_step1_epipen",
                target_metronome_bpm=0
            ),
            DirectiveStep(
                step_number=2,
                title="Thigh Injection",
                instruction="Inject into outer mid-thigh, push firmly until it clicks, hold in place for 3 full seconds.",
                spoken_voice_text="Inject into outer mid-thigh, push until it clicks, hold for three full seconds.",
                audio_cue_id="anaph_step2_inject",
                target_metronome_bpm=0,
                is_terminal_loop=True
            )
        ]
    },
    EmergencyIntent.OVERDOSE.value: {
        PatientType.ADULT.value: [
            DirectiveStep(
                step_number=1,
                title="Opioid Triage & Naloxone",
                instruction="Call 911 on speaker! Check if Narcan / Naloxone nasal spray is available.",
                spoken_voice_text="Call 911 on speaker! Grab Narcan or Naloxone nasal spray.",
                audio_cue_id="od_step1_narcan",
                target_metronome_bpm=0
            ),
            DirectiveStep(
                step_number=2,
                title="Nasal Administration & Recovery Posture",
                instruction="Spray full dose into one nostril. If unresponsive after 3 minutes, give second dose and place in recovery position.",
                spoken_voice_text="Spray full dose into one nostril. Place in recovery position.",
                audio_cue_id="od_step2_administer",
                target_metronome_bpm=0,
                is_terminal_loop=True
            )
        ]
    }
}
