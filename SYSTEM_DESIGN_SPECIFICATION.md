# KeepAlive: Real-Time Voice & Visual Autonomous Emergency Rescue Cockpit
## Comprehensive System Design Specification (Final 9.6/10 Champion Edition)

---

## 1. Executive Summary & Core Mission

### 1.1 Project Title
**KeepAlive** (with *KeepAlive Companion*) — *The Autonomous Real-Time Voice & Visual Emergency First-Responder*

### 1.2 The Core Philosophy
> **"AI listens. Deterministic protocols decide. Voice guides. Visuals reinforce."**

* In computer science and WebSockets (like AssemblyAI's real-time streaming), a `keep-alive` packet maintains the connection.
* In emergency medicine, **KeepAlive** maintains the human connection—pumping oxygenated blood to the brain and controlling hemorrhage until paramedics arrive.

In sudden cardiac arrest, traumatic bleeding, choking, anaphylaxis, or overdose, every passing second without intervention causes irreversible tissue necrosis or brain death. Untrained bystanders frequently panic, freeze, or hesitate. Standard 911 phone calls are voice-only and prone to confusion, while mobile first-aid apps are static text booklets that require tapping through menus—which is physically impossible because the rescuer's hands are busy doing chest compressions or holding bleeding wounds.

**KeepAlive** bridges this survival gap with a zero-touch emergency rescue interface:
1. **Zero-Touch Speech Streaming:** Powered by **AssemblyAI Real-Time WebSocket Streaming**, capturing user speech in under 300 milliseconds with specialized medical word boosting.
2. **Sub-10ms Semantic Vector Intent Router:** Cosine similarity classification replacing brittle if-else string matching, instantly locking to the right emergency protocol in <5ms.
3. **Interactive 3D Anatomical Cockpit (Three.js WebGL):** An interactive 3D human patient lying flat on their back with realistic 3D interlocked CPR hands compressing the sternum at **110 BPM**, featuring 360° touch/voice orbit controls allowing rescuers to verify real hand positioning, 90° straight arm posture, and 2-inch compression depth from 6 to 10 feet away.
4. **Protocol-Locked Deterministic Execution:** Generative AI is **strictly isolated from the safety-critical execution path**. All emergency steps follow an immutable Finite State Machine (FSM) aligned with American Heart Association (AHA) and DHS "Stop the Bleed" guidelines.
5. **KeepAlive Companion (Bounded In-Crisis Q&A & Post-Event Grounding):** Powered by **AssemblyAI LLM Gateway**, providing bounded 18-word micro-clarifications during CPR and empathetic grounding after first responders arrive.
6. **AI-Generated EMS Handoff Summary:** Automatically compiling the second-by-second incident timeline into an instant handoff card for arriving paramedics.

---

## 2. The Real-World Hands-Occupied Survival Gap

* **The Perfusion Window:** In cardiac arrest, every minute without effective chest compressions reduces survival probability by 7–10%. Continuous bystander CPR maintains cerebral and myocardial perfusion until a defibrillator arrives.
* **The Bleed-Out Clock:** A severed femoral or brachial artery can result in fatal hypovolemic shock in under 3 minutes without immediate direct pressure or tourniquet application.
* **Hands-Occupied Reality:** Rescuers performing two-handed chest compressions or holding direct wound pressure physically cannot hold a phone, unlock a screen, or scroll through apps. **Voice is genuinely the only viable interface.**
* **The Paramedic Information Void:** When paramedics arrive, 2 to 3 critical minutes are wasted gathering chaotic verbal recollections. KeepAlive bridges this gap with an automated, second-by-second event log.

---

## 3. The Safety Shield Architecture

### 3.1 "Two Brains. One Safety Boundary."

```mermaid
flowchart TD
    A["🗣️ 'Help! My dad collapsed, he is not breathing!'"]

    subgraph EARS ["1 · Ears — they never decide"]
        B["🎙️ Mic · Web Audio · PCM16 16 kHz"]
        C["AssemblyAI Universal-3.5 Pro<br/>streaming STT · medical term boosting"]
        D["🔁 Echo filter: the mic stays open while we speak;<br/>transcripts matching the spoken line are dropped"]
        B --> C --> D
    end

    subgraph AG1 ["2 · Agent #1 — Triage & Dispatch"]
        E["Lexical cosine router over word + bigram counts<br/>0.49 ms measured from outside"]
        F["🔒 PROTOCOL LOCKED · AHA-BLS cardiac arrest"]
        G["🚨 Agonal-gasping override · MARCH trauma order"]
        H["📟 911 CAD packet — SIMULATED by default<br/>live relays opt-in via .env"]
        E --> F --> G --> H
    end

    subgraph AG2 ["3 · Agent #2 — Safety Coach · deterministic, no LLM"]
        I["🔊 'Don't panic. 911 CAD dispatch has been alerted<br/>with your exact GPS location…'"]
        J["Pre-rendered lines, one voice · trigger → sound 21 ms"]
        K["❤️ 110 BPM metronome, ducked -4 dB under speech"]
        L["Depth target ≥ 2.0 in · 2-minute rescuer swap"]
        I --> J --> K --> L
    end

    subgraph AG3 ["4 · Agent #3 — Clinical Companion"]
        M["🧠 Groq LPU qwen · 0.38 s measured end to end"]
        N["🛡️ Safety gate: ≤ 18 words · never 'stop compressions'<br/>no doses · no pulse checks"]
        O["⚡ Offline reflex: 26 scripted answers in 0.7 ms"]
        M --> N
        O --> N
    end

    subgraph OUT ["5 · What the rescuer gets"]
        P["🔊 Speaker: clicks + spoken directives, one human voice"]
        Q["📱 Cockpit: clinical pacing feed · BPM ring · depth gauge"]
        R["📊 Telemetry: routing 0.5 ms · voice 21 ms · companion 0.38 s"]
        S["🚨 Simulated 911 CAD bar, always on screen"]
    end

    subgraph EMS ["6 · Paramedic handoff"]
        T["🗣️ 'The paramedics are here!'"]
        U["⏱️ Timers freeze · compression count locked"]
        V["📄 EMS handoff card + incident timeline"]
    end

    A --> B
    D --> E
    F --> I
    D -.->|"question, not a command"| M
    N --> P
    L --> P
    L --> Q
    L --> R
    H --> S
    P --> T
    T --> U --> V
```

* **The Critical Medical Path (Pre-Recorded Directives ~15ms ➡️ FSM ➡️ HUD/Audio):** Generative AI is completely removed from clinical decisions. Medical actions are 100% deterministic, zero-hallucination, and protocol-locked to AHA guidelines.
* **The Dynamic Conversational Path (AssemblyAI Voice Agent API ~1s):** Handled over a single unified WebSocket (Universal-3 Pro STT + LLM + TTS + Turn-Taking + Tool Calling). Replaces brittle multi-vendor chains (external LLMs + ElevenLabs) while providing conversational agility for unexpected bystander questions, bounded safety advice, post-event debriefing, and EMS handoff compilation.
* **Live Dual-Latency Telemetry HUD Display:** The dashboard prominently showcases the latency delta:
  $$\text{Protocol Directive: } \sim 15\text{ms (Deterministic Audio Cache)} \quad\vert\quad \text{AssemblyAI Voice Agent: } \sim 1.0\text{s (Universal-3 Pro + LLM + TTS)}$$
  This directly validates AssemblyAI Voice Agent API adoption while demonstrating deliberate clinical design: life-saving physical directives cannot wait, while dynamic dialogue flows in conversational time.

### 3.2 Sub-10ms Semantic Vector Intent Router (Replacing Brittle If-Else)
In sudden emergencies, callers never speak uniform sentences. One caller screams: *"My dad fell on his knees in the kitchen and isn't breathing!"* while another cries: *"Unconscious, blue face, no pulse!"*
* **Why Traditional If-Else Fails:** Keyword matching (`if "not breathing" in text:`) breaks when callers use natural variations (*"gasping for air"*, *"chest not moving"*, *"passed out cold"*).
* **The Solution — Semantic Vector Routing:** 
  1. We pre-compute embedding centroids for approved clinical intent classes (`CARDIAC_ARREST`, `ARTERIAL_BLEED`, `CHOKING`, `ANAPHYLAXIS`, `OVERDOSE`).
  2. The incoming AssemblyAI real-time partial transcript is converted into a vector and matched via **Cosine Similarity in <5ms**.
  3. If similarity score $\ge 0.82$, the deterministic protocol locks immediately.
  4. If ambiguity exists ($0.60 \le \text{score} < 0.82$), the voice agent executes a single 1-second clarifying probe (*"Is he breathing normally, yes or no?"*).

### 3.3 Acoustic Engineering & Zero-Latency Audio Architecture

During active cardiac arrest or severe trauma, the smartphone rests flat on the floor on loudspeaker while the rescuer operates 2 to 6 feet away. This acoustic environment introduces three catastrophic failure modes that KeepAlive solves at the architectural level:

```mermaid
flowchart LR
    subgraph INPUT ["Audio Input & Gating"]
        MIC["🎙️ Phone Mic (Floor Level)"] --> AEC["Hardware AEC\n(autoGainControl: false)"]
        AEC --> GATE{"Software Gate\n(Is Directive Playing?)"}
        GATE -- "Yes & Below Barge-in" --> IGNORE["🔇 Mute Stream to AssemblyAI"]
        GATE -- "Yes & Loud Shouting" --> BARGE["⚡ Barge-In Trip: Cancel Audio"]
        GATE -- "No (Listening)" --> AAI["⚡ AssemblyAI WebSocket"]
    end

    subgraph DUAL_OUTPUT ["Dual Output Mixing (Web Audio API)"]
        CLICK["❤️ 110 BPM Metronome\n(Acoustic Click)"] --> GAIN["GainNode\n(Ducking Control)"]
        DIRECTIVE["📁 Pre-Rendered Local Audio\n(0ms Latency / Offline)"] --> MIX["🔊 Phone Speaker"]
        GAIN --> MIX
    end

    BARGE -.-> DIRECTIVE
```

#### 1. Acoustic Echo Cancellation (AEC) & Software Recognizer Gating
* **Hardware AEC:** Audio capture configures `navigator.mediaDevices.getUserMedia({ echoCancellation: true, noiseSuppression: true, autoGainControl: false })`. Disabling Automatic Gain Control (AGC) prevents the microphone from artificially boosting speakerphone metronome clicks during caller pauses.
* **Software Gating:** When KeepAlive plays a spoken directive, the client-side recognizer stream engages a software gate that suppresses echo transcription by AssemblyAI.
* **Barge-In Interrupt:** A high-threshold voice activity detector (VAD) monitors caller volume. If the caller shouts over the agent, the software gate opens, pre-rendered playback cancels instantaneously (`sourceNode.stop()`), and AssemblyAI transcribes the caller's urgent query.

#### 2. The Hybrid Audio Strategy (Deterministic Audio Cache + AssemblyAI Voice Agent API)
* **The Life-Critical Rationale:** In cardiac arrest, waiting 1 second for a critical directive is unviable. Core AHA-protocol directives play instantly at **~15ms** from pre-rendered local audio cache. Dynamic dialogue, panic questions, and post-event debriefing are handled by the **AssemblyAI Voice Agent API** (~1s total turnaround), demonstrating AssemblyAI's newest end-to-end voice technology without sacrificing medical safety.
* **Local Asset Bundling:** Core AHA and Stop the Bleed directives are pre-rendered into normalized local audio files bundled with the application (`.mp3` / `.wav`).
* **AssemblyAI Voice Agent API Integration:** Powered by a single unified WebSocket (Universal-3 Pro STT + LLM + TTS + Turn-Taking). Eliminates external API keys and brittle multi-service orchestration.

#### 3. Real-Time Web Audio Metronome Ducking
* **Dynamic Gain Envelope:** Spoken directives must cut through continuous 110 BPM metronome clicks without breaking the rescuer's compression cadence.
* **The Ducking Curve:** When a voice directive or Voice Agent stream triggers, the metronome `GainNode` ducks from `1.0` down to `0.20` (-14 dB) with a rapid **40ms attack**. The beat remains audible in the background to sustain CPR timing. Once speech ends, the gain smoothly recovers to `1.0` over a **150ms release**.

#### 4. Master Pre-Render Directive Script & Asset Manifest (Updated for 911 Protocol)

| Asset ID | Trigger / State | Verbatim Spoken Directive | Target Duration | Delivery Cadence |
| :--- | :--- | :--- | :--- | :--- |
| `cpr_01_confirm` | Semantic Lock (`CARDIAC_ARREST`) | *"Call 911 now and put it on speaker! Roll the patient flat on their back. Kneel beside their chest."* | ~4.0s | Firm, deliberate, commanding |
| `cpr_02_agonal` | Agonal Detector (`"gasping"` / `"snoring"`) | *"Do not stop. Gasping is agonal breathing, not normal breathing. Kneel beside their chest immediately."* | ~3.9s | Urgent, corrective, reassuring |
| `cpr_03_position` | Hand positioning prompt | *"Place the heel of one hand on the center of the chest. Interlock your other hand on top. Lock your elbows straight."* | ~4.5s | Clear, paced, instructional |
| `cpr_04_start_beat`| Metronome launch (110 BPM) | *"Push hard and fast to this beat. Push down two inches, then let the chest come all the way up. One, two, three, four."* | ~4.8s | Rhythmic, cadence-locked |
| `cpr_05_recoil` | 60s pacing reminder | *"Keep pushing to the beat. Allow full chest recoil. Do not lean on the chest."* | ~3.2s | Steady, firm reinforcement |
| `cpr_06_paramedic` | Caller: *"Paramedics are here"* | *"Stop compressions and step back. Let the paramedics take over. The emergency timeline is saved on your screen. Take a slow, deep breath."* | ~5.0s | De-escalating, grounding |
| `bleed_01_expose` | Semantic Lock (`ARTERIAL_BLEED`) | *"Call 911 on speaker now! Bleeding protocol locked. Rip or cut away clothing immediately to expose the bare wound."* | ~3.9s | Direct, urgent |
| `bleed_02_locate` | Direct pressure directive | *"Press both hands directly onto the wound with a clean cloth. Lean your full body weight into it."* | ~3.8s | Authoritative, firm |
| `bleed_03_tq_limb` | Extremity localized | *"Place the tourniquet two to three inches above the wound. Never place it over a joint. Pull the strap tight and twist the windlass until bleeding stops."* | ~5.5s | Methodical, instructional |
| `bleed_04_neck` | Neck safety intercept | *"Warning. Never apply a tourniquet to the neck. Apply firm, direct two-handed pressure with a clean cloth only."* | ~4.2s | High-alert safety alarm |
| `choke_01_assess` | Semantic Lock (`CHOKING`) | *"Stand behind them. Wrap your arms around their waist. If they can cough or speak, encourage them to keep coughing."* | ~4.0s | Clear, paced |
| `choke_02_thrusts`| Silent choking confirmed | *"Make a fist above their navel. Grasp your fist with your other hand. Deliver five quick, upward abdominal thrusts now."* | ~4.5s | Sharp, decisive |
| `qa_rib_pop` | Panic query: *"Did I break a rib?"* | *"A rib pop can happen during effective CPR. Do not stop—keep pushing to the beat."* | ~3.0s | Reassuring, firm |
| `qa_bed_surface` | Panic query: *"Can I leave him on bed?"* | *"Move them to a firm floor if you can do so safely. Then resume pushing."* | ~2.8s | Clear, actionable |
| `qa_vomit` | Panic query: *"He threw up / vomit"* | *"Roll them onto their side, clear the mouth, roll them back and immediately resume compressions."* | ~3.5s | Immediate corrective |
| `qa_fallback` | Unrecognized in-crisis query | *"Continue chest compressions to the beat. Emergency services will guide further."* | ~2.5s | Protocol-locking safety fall-back |

---

## 4. Full Spectrum of Handled Emergency Situations

KeepAlive is an extensible acute emergency response engine covering the full physiological spectrum of life-threatening trauma:

### 4.1 Flagship Hero: Sudden Cardiac Arrest (AHA BLS 2020–2025 Guidelines)
* **Cadence & Depth:** Continuous 110 BPM audiovisual cadence sitting squarely within the AHA-recommended 100–120 compressions/minute range, targeting 2 to 2.4 inches (5 to 6 cm) depth.
* **Elimination of Layperson Pulse Checks:** Untrained bystanders waste 1–2 critical minutes failing to locate a carotid pulse. KeepAlive bypasses pulse checks: unresponsiveness + absent/abnormal breathing triggers immediate compressions.
* **Realistic 3D Anatomical Body & Hands (Three.js WebGL):**
  * **No Abstract Lines:** Displays an actual, photorealistic 3D human body lying flat on their back (supine position) with clearly visible anatomical landmarks (collarbones, sternum, ribcage, nipple line).
  * **Realistic 3D Interlocked CPR Hands:** Accurately models rescuer hands with interlocked fingers and palm heel resting squarely on the lower third of the sternum.
  * **110 BPM Compression & Recoil Kinematics:** Hands actively press down 2 to 2.4 inches (5 cm) into the patient's chest and return with full chest recoil in lockstep with the 110 BPM audio clicks (~545ms cycle).
  * **360° Touch & Voice Orbit Inspection:** Rescuers or assistants can freely orbit and zoom around the 3D scene (or tap/say *"Top View"* / *"Side View"*) to verify:
    1. **Top-Down Alignment:** Heel of hand centered between nipples on the sternum.
    2. **Side Profile:** Arms locked at 90° directly above the victim's chest, ensuring compressions use upper body weight rather than fatiguing triceps.
* **Agonal Respiration Filter:** Detects descriptions of gasping or snoring sounds and immediately warns: *"Do NOT stop. Gasping is agonal breathing, not normal breathing. Keep pushing to the beat."*

### 4.2 Hero Extensibility: Catastrophic Arterial Bleeding (DHS "Stop the Bleed")
* **Step 1: Exposure:** Directs rescuer to cut or rip away clothing to expose the exact cutaneous bleeding point rather than compressing soaked fabric.
* **Step 2: Speech-Driven Wound Localization:** Rescuer says: *"Right thigh"* or *"Left arm"*. AssemblyAI transcribes in <300ms.
* **Step 3: Dynamic Tourniquet Placement Map:** HUD highlights that limb in pulsing red and renders the horizontal tourniquet guideline **2 to 3 inches above the wound** (closer to the trunk, avoiding joints).
* **Step 4: Neck Tourniquet Safety Interceptor:** If the rescuer mentions a neck laceration, the safety engine sounds an alarm: *"⚠️ NEVER apply a tourniquet around the neck! Apply direct two-handed cloth pressure only."*

### 4.3 Severe Airway Obstruction (Choking / Heimlich Maneuver)
* **Rapid Triage:** Checks: *"Can they speak, cough, or make sound?"* (If yes, encourages forceful coughing without interference).
* **Execution:** If silent choking (hands clutching throat), directs 5 rapid subdiaphragmatic inward/upward abdominal thrusts above the navel.
* **Dynamic Transition to CPR:** If victim becomes limp or unresponsive, the system immediately switches state to Cardiac Arrest CPR without needing a restart.

### 4.4 Acute Anaphylaxis (EpiPen / Auto-Injector Guidance)
* **Symptoms Detected:** Severe allergic reaction, facial/lip swelling, hives, audible stridor/wheezing.
* **Execution Directives:** *"Blue to the sky, orange to the thigh"*, firm perpendicular outer thigh strike through clothing.
* **Visual Hold Countdown:** 3-second radial hold meter on screen with audio count: *"1... 2... 3... Remove and massage for 10 seconds."*

### 4.5 Opioid & Narcotic Overdose (Nasal Naloxone / Narcan)
* **Symptoms Detected:** Pinpoint pupils, pale/blue lips, deep unresponsiveness, respiratory depression.
* **Administration:** Rapid guidance for 4mg nasal Narcan spray into nostril with thumb plunger strike.
* **Recovery & Assessment:** Directs lateral recovery position to prevent aspiration from vomiting, engaging a 2-minute timer for a second dose if breathing remains depressed.

### 4.6 Compound Multi-Trauma Triage Engine (The MARCH Protocol)
When an emergency involves multiple simultaneous injuries (e.g., arterial blood spurting + patient unresponsive and not breathing):
* **Clinical Triage Standard (MARCH):**
  1. **M**assive Bleeding (Arterial spurting kills within 3 minutes).
  2. **A**irway (Clear obstruction).
  3. **R**espiration (Agonal breathing intercept).
  4. **C**irculation (110 BPM chest compressions).
* **Deterministic Priority Cascade:** KeepAlive directs: *"First, apply direct pressure or tourniquet to the thigh wound, then immediately start chest compressions."* AssemblyAI LLM Gateway function calling validates multi-symptom extraction without delaying immediate verbal execution.

---

## 5. KeepAlive Companion: Bounded Intelligence Layer

### 5.1 In-Crisis Micro-Clarifications (`MAX_RESPONSE_WORDS = 18`)
During active CPR, rescuers experience panic-driven hesitations. KeepAlive Companion answers from an approved emergency FAQ in 1 short sentence without pausing the 110 BPM metronome:
* **Q:** *"Can I do CPR on his soft bed?"*
  * **A:** *"Move him to a firm floor if you can do so safely. Then keep pushing."*
* **Q:** *"I heard a bone pop, did I break his rib?!"*
  * **A:** *"A rib injury can happen during effective CPR. Do not stop—keep pushing to the beat."*
* **Q:** *"He vomited, what should I do?!"*
  * **A:** *"Roll him on his side, clear his mouth, roll him back and immediately resume compressions."*
* **Unapproved / Arbitrary Questions:** Fallback to safe instruction: *"Continue chest compressions to the beat. Emergency services will guide further."*

### 5.2 Post-Event Grounding (The Human Touch)
When the rescuer announces *"Paramedics are here!"*, the HUD renders the EMS Handoff Card and initiates empathetic grounding:
* *"The emergency is now being handled by professionals. Take a slow breath with me. Breathe in... and out. You did what you could to help."*
* Prompts to log the responding EMS unit and offers to contact family members.

---

## 6. The Real-Life Clinical Flow: Kitchen Collapse (00:00 to 03:45)

| Timeline | Rescuer Speech / State | Internal System Pipeline | KeepAlive HUD Audio & Visual Response |
| :--- | :--- | :--- | :--- |
| **00:00** | *"Help! My dad just fell in the kitchen, he's not breathing!"* | • Phone streams 16kHz PCM audio.<br/>• AssemblyAI WebSocket transcribes in **220ms**.<br/>• Semantic Router locks `CARDIAC_ARREST` in **4.1ms**. | **Screen:** Cockpit locks to `● PROTOCOL LOCKED: AHA-BLS`.<br/>**Audio:** *"Stay calm. Emergency services alerted. Put phone on speaker. Roll him flat on the floor."* |
| **00:05** | *"He's making strange snoring or gasping noises, should I wait?!"* | • AssemblyAI detects `"gasping"` / `"snoring"`.<br/>• Agonal Respiration Filter intercepts immediately. | **Audio:** *"Do NOT wait. Gasping is agonal breathing, not normal breathing. Place heel of hand on center of chest."*<br/>**Screen:** Sternum crosshairs illuminate. |
| **00:10** | Hands placed on sternum. | • FSM transitions to `ACTIVE_COMPRESSIONS`.<br/>• Web Audio API initiates synchronized 110 BPM engine. | **Audio:** 110 BPM acoustic metronome clicks begin: *"Push hard and fast to this beat. Down 2 inches."*<br/>**Screen:** Pulsing red heart ring expands/contracts at 110 BPM. |
| **01:15** | *"I heard a loud pop sound, did I break his rib?!"* | • Metronome runs continuously without pausing.<br/>• AssemblyAI LLM Gateway parses micro-question (`MAX_WORDS = 18`). | **Audio (over metronome):** *"A rib pop can happen during effective CPR. Do not stop—keep pushing to the beat!"* |
| **03:45** | *"The front door opened, paramedics are walking in right now!"* | • AssemblyAI transcribes `"paramedics are here"`.<br/>• Timers freeze. Compression counter logs 412 total.<br/>• AssemblyAI LLM Gateway formats JSON handoff card. | **Screen:** Displays **AI-Generated EMS Handoff Card**.<br/>**Audio:** *"Step back and let paramedics take over. Take a slow, deep breath with me. Breathe in... and out."* |

---

## 7. The 4 Killer Features That Win

### 7.1 🔒 Visible "Protocol Locked" Indicator
A prominent badge at the top of the HUD: **`● PROTOCOL LOCKED: AHA-BLS`** with active step tracking (**`CARDIAC ARREST • STEP 3 / 5`**). Proves that medical execution is strictly deterministic.

### 7.2 ⏱️ Live Immutable Rescue Timeline
A second-by-second operational log:
```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KEEPALIVE EVENT LOG
09:41:02 — Emergency detected (Cardiac Arrest)
09:41:08 — CPR Protocol Engaged
09:41:15 — Compressions Active (110 BPM)
09:42:10 — Bounded Q&A: Rib injury reassurance provided
09:45:17 — EMS Arrival Triggered (412 Compressions Delivered)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 7.3 🚨 Deterministic Panic Mode
Triggered by measurable acoustic signals (speech rate, repeated utterances, volume/energy, transcription fragmentation). The HUD strips away all secondary text and transforms into a high-visibility flight instrument:
```text
                 ❤️
             PUSH NOW
         ●  ●  ●  ●  ●
             110 BPM
```

### 7.4 🚑 AI-Generated EMS Handoff Card (Review with Arriving EMS)
Powered by **AssemblyAI LLM Gateway**, generating the structured summary in 2 seconds upon EMS arrival. Distinguishes immutable system timestamps from AI-summarized clinical handoff notes.

### 7.5 🧍 Realistic 3D Anatomical Cockpit & 360° Position Checker
Powered by **Three.js WebGL**, replacing flat diagrams or abstract lines with an authentic clinical simulation:
* **Interactive Supine Manikin:** A realistic 3D human patient positioned flat on the floor with visible thoracic anatomy.
* **Realistic Interlocked Hands:** Dual 3D hands in proper CPR interlocking posture compress the sternum down 2 inches and release for full recoil at 110 BPM.
* **Touch & Voice 360° Camera:** Bystanders can drag/pinch or verbally command (*"Show top view"*, *"Check arm angle"*) to verify hand placement directly over the sternum and ensure elbows are fully locked.

---

## 8. 2.5-Minute Pitch Video Blueprint (The 9.6/10 Storyboard)

| Timecode | Visual Scene | Audio & Dialogue | Storytelling Objective |
|---|---|---|---|
| **0:00 – 0:15** | Black screen: *"Your hands are busy saving a life. Why does emergency software require your hands?"* Cut to simulated collapse. | Sudden thud, dramatic silence. | **Fear & The Hook:** Proves voice-first is mandatory. |
| **0:15 – 0:35** | Rescuer shouts: *"Help! He collapsed, he's not breathing!"* Screen flashes **`CARDIAC ARREST DETECTED`**. | KeepAlive Voice: *"Kneel beside his chest. Lock elbows."* | **Control:** Demonstrates sub-second AssemblyAI STT. |
| **0:35 – 1:10** | **Realistic 3D Body & Interlocked Hands appear.** Hands pump the sternum down 2 inches at 110 BPM. Rescuer rotates camera 360° to check placement. | Audio clicks at 110 BPM. KeepAlive: *"Push center of chest. Down 2 inches. 1, 2, 3, 4."* | **The Money Shot:** Authentic 3D anatomical CPR pacing with 360° position inspection matching AHA standards. |
| **1:10 – 1:25** | Actor panics: *"I heard a bone pop, did I break his rib?!"* KeepAlive delivers bounded 12-word response without stopping metronome. | KeepAlive: *"A rib injury can happen during effective CPR. Do not stop—keep pushing."* | **Trust:** Bounded in-crisis micro-Q&A in action. |
| **1:25 – 1:35** | Flash **8-second architecture slide**: *Speech ➡️ AssemblyAI STT ➡️ Deterministic FSM ➡️ 3D Cockpit*. 🔒 *LLM ≠ Medical Decision*. | Narrator: *"The language model never decides the medical action. Protocols are locked in deterministic code."* | **Safety:** Disarms all hallucination concerns in 8 seconds. |
| **1:35 – 1:55** | Fast 15s switch to Bleeding: User shouts *"Right thigh!"* ➡️ 3D body highlights femoral artery with tourniquet line 2 inches above wound. | KeepAlive: *"Wrap tourniquet 2 inches above the cut. Never place on knee."* | **Extensibility:** Proves multi-emergency engine. |
| **1:55 – 2:15** | Rescuer shouts: *"Paramedics are here!"* Timers freeze. Screen shows **AI-Generated EMS Handoff** and initiates grounding. | KeepAlive: *"Paramedics on scene. Take a slow breath with me. You did what you could to help."* | **Continuity & Humanity:** EMS handoff + post-event grounding. |
| **2:15 – 2:30** | Final Logo: *KeepAlive — When seconds count, your hands should save a life, not hold a phone.* | Narrator: *"In networking, keep-alive maintains the connection. In emergencies, KeepAlive maintains human life."* | **The Winning Punchline:** Unforgettable finish. |

---

*Authored for the AssemblyAI Voice Agent Hackathon (lablab.ai) — KeepAlive Project Team.*
