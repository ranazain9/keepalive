# KeepAlive: Teammate Alignment & System Architecture Guide
### *The Actual Idea, Architecture, and Winning Pitch*

---

## 💡 The Core Problem & The Actual Idea

### What Everyone Else Is Doing
Most hackathon teams are building **chatbots with a voice skin** (e.g., customer support, cold callers, general search). In those applications:
* Waiting 1 to 2 seconds for an LLM response is acceptable.
* The user's hands are free to hold the phone and read text.
* Hallucinations are embarrassing, but not fatal.

### What KeepAlive Actually Is
**KeepAlive is an autonomous, hands-free emergency rescue cockpit for acute life-or-death crises (Sudden Cardiac Arrest, Massive Arterial Bleeding, Choking, Anaphylaxis, Overdose).**

When someone collapses:
1. **The Rescuer's Hands are Occupied:** They are actively pumping a chest or applying pressure to a bleeding wound. They **cannot** touch a screen, unlock a phone, or scroll through menus. **Voice is genuinely the only possible interface.**
2. **Every Second Counts:** In cardiac arrest, brain tissue begins to die in 3 to 4 minutes without blood flow. Waiting 1+ seconds for an LLM to generate a sentence is unacceptable.
3. **Generative AI Cannot Make Medical Decisions:** If an LLM hallucinates CPR hand placement or depth, it can be fatal.

---

## ⚡ The Architecture: "Two Brains. One Safety Boundary."

To win the hackathon while adhering to clinical standards, we use a **Hybrid Latency Architecture**:

```text
                                  High-Panic Caller Voice
                                             │
                                             ▼
                        ┌────────────────────────────────────────┐
                        │   AssemblyAI Voice Agent API (WS)      │
                        │   (Universal-3 Pro STT + LLM + TTS)    │
                        └────────────────────┬───────────────────┘
                                             │
                                             ▼
                        ┌────────────────────────────────────────┐
                        │ Sub-10ms Semantic Intent Router (<5ms) │
                        │  (Locks protocol: Cardiac Arrest, etc) │
                        └────────────────────┬───────────────────┘
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      ▼                                             ▼
       ┌──────────────────────────────┐              ┌──────────────────────────────┐
       │   BRAIN #1: Safety Engine    │              │ BRAIN #2: Voice Agent API    │
       │    (Deterministic Cache)     │              │     (Dynamic Companion)      │
       ├──────────────────────────────┤              ├──────────────────────────────┤
       │ • 15ms Immediate Directives  │              │ • ~1.0s Dynamic Turn-Taking  │
       │ • Verbatim AHA Instructions  │              │ • Bounded Micro-Q&A (<=18 w) │
       │ • 110 BPM Web Audio Metronome│              │ • Panic Hesitation Answers   │
       │ • Agonal Breathing Intercept │              │ • Post-Event Grounding / EMS │
       └──────────────────────────────┘              └──────────────────────────────┘
```

### 1. Brain #1: Deterministic Audio Directives (~15ms Latency)
* Pre-recorded, normalized audio clips stored locally.
* **Instant response:** When the system detects cardiac arrest, it immediately commands:
  > *"Call 911 now and put it on speaker! Roll the patient flat on their back. Kneel beside their chest."*
* Starts unbroken **110 BPM acoustic clicks** (AHA standard).
* Audio ducking: Spoken words automatically duck the metronome click volume by -14 dB without stopping the beat.

### 2. Brain #2: AssemblyAI Voice Agent API (~1.0s Turn-Taking)
* A single WebSocket connection that handles Universal-3 Pro Speech-to-Text, turn-taking, LLM response, and voice streaming.
* **No separate LLM or ElevenLabs keys needed.**
* Operates while the metronome is clicking to answer unexpected bystander panic questions:
  * Rescuer: *"I heard a loud pop, did I break a rib?!"*
  * Agent: *"A rib pop is normal during effective CPR. Do not stop—keep pushing to the beat!"*
  * Rescuer: *"He's throwing up!"*
  * Agent: *"Roll him on his side, clear the mouth, roll him back and immediately resume compressions."*
* Once paramedics arrive (*"Paramedics are here!"*), it compiles the **EMS Handoff Card** and guides the rescuer through deep breathing.

---

## 📊 Live HUD Latency Tracker (The Judge-Winning Differentiator)

On our Heads-Up Display (HUD), we display live telemetry that no other project is showing:

$$\mathbf{\text{Protocol Directive: } \sim 15\text{ms} \quad\vert\quad \text{AssemblyAI Live Agent: } \sim 1.0\text{s}}$$

### Why Judges Will Love This:
1. It shows that we deeply understand and fully utilize the **AssemblyAI Voice Agent API**.
2. It demonstrates engineering maturity: we explain to the judges why 1 second is amazing for conversation, but why cardiac arrest protocol requires a 15ms deterministic path.

---

## 🚨 The 911 Problem: How We Solved It

A major flaw in first-aid apps is ignoring emergency dispatch. Under American Heart Association (AHA) and ERC guidelines:
* **Step 1:** Call emergency services (911 / 112) and put them on speakerphone.
* **Step 2:** Start chest compressions.

### How KeepAlive Implements This:
1. **Audio Directive 1:** The very first spoken line commands:
   > *"Call 911 now and put it on speaker! Roll the patient flat on their back."*
2. **Persistent HUD Dispatch Bar:** A prominent, glowing red button at the top of the screen:
   `[ 📞 Call 911 (Speakerphone) ]`
3. **Voice Agent Guardrail:** If the caller asks the AssemblyAI Agent *"Did you call an ambulance?"*, the agent immediately instructs them:
   > *"Dial 911 now and place your phone on speaker next to the victim while you continue chest compressions."*

---

## 🧍 Interactive 3D Anatomical Cockpit (Three.js)

Instead of flat cartoon illustrations:
* A realistic 3D human body lying flat on the ground.
* Realistic 3D interlocked CPR hands actively compressing down 2 inches at 110 BPM in sync with the audio.
* Rescuers or helpers can orbit 360° or say *"Show top view"* to verify their hand is on the lower half of the breastbone and their elbows are locked straight.

---

## 🎯 What Each Team Member Needs to Know

| Component | Technology | Owner/Focus |
| :--- | :--- | :--- |
| **Voice Agent WebSocket** | AssemblyAI Voice Agent API | Connects mic stream, handles dynamic turn-taking & micro-Q&A prompts. |
| **Protocol Engine & Audio** | Web Audio API / Local Audio Cache | Pre-recorded 15ms clips, 110 BPM metronome engine, ducking envelope. |
| **Visual Cockpit** | Three.js WebGL / HTML5 Canvas | 3D body + compressing hands, live latency pill, 911 bar, step indicators. |
| **Pitch & Presentation** | Video / Pitch Deck | Focus on hands-occupied reality, 0ms vs 1s latency pitch, and safety boundary. |
