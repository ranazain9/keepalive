import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { useMetronome } from './hooks/useMetronome';
import { useRescueVoice } from './hooks/useRescueVoice';
import { useRescueState } from './hooks/useRescueState';
import { useWakeLock } from './hooks/useWakeLock';
import { TopTelemetryBar } from './components/TopTelemetryBar';
import { Stage1TriageIntake } from './components/Stage1TriageIntake';
import { CPRPacingHero } from './components/CPRPacingHero';
import { CompanionBubble } from './components/CompanionBubble';
import { EMSHandoverCard } from './components/EMSHandoverCard';
import { EMSHandoverModal } from './components/EMSHandoverModal';

export default function App() {
  // 1. Audio Metronome Hook
  const {
    isPlaying: isMetronomeActive,
    compressionCount,
    beatPhase,
    cycleTime,
    formattedCycleTime,
    startMetronome,
    stopMetronome,
    resetMetronome,
    duckAudio,
    getAudioContext,
  } = useMetronome(110);

  // 2. Geolocation State
  const [userLocation, setUserLocation] = useState('201 Mission St, Financial District, San Francisco, CA');
  const [userCoords, setUserCoords] = useState({ lat: 37.7749, lon: -122.4194 });

  // 3. Central Rescue State Hook
  const {
    activeIntent,
    protocolStep,
    isParamedicLocked,
    directive,
    companionMessage,
    isAgonalAlert,
    latencies,
    cadInfo,
    handoffData,
    triageData,
    agent1Status,
    agent2Status,
    agent3Status,
    companionModel,
    speakCompanion,
    setCadInfo,
    handleUtterance,
    updateFromData,
    resetSession,
    advanceStep,
    startCPR,
  } = useRescueState({
    onStartCPR: startMetronome,
    onStopCPR: stopMetronome,
    onResetMetronome: resetMetronome,
    onDuckAudio: duckAudio,
  });

  // 4. Microphone & Voice Hook (16kHz audio pipeline)
  const {
    isListening,
    transcript,
    setTranscript,
    rmsEnergy,
    wpm,
    error: voiceError,
    startListening,
    stopListening,
  } = useRescueVoice({
    userLocation: userLocation,
    userLat: userCoords.lat,
    userLon: userCoords.lon,
    onTriageUpdate: (data) => {
      updateFromData(data, data.is_final !== undefined ? Boolean(data.is_final) : true);
    },
    onTranscriptUpdate: () => {},
  });

  // Local state for UI controls
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('keepalive_theme') || 'clinical';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('keepalive_theme', theme);
  }, [theme]);

  const [is911Active, setIs911Active] = useState(false);
  const [activeTakeStep, setActiveTakeStep] = useState(0);
  const [autoDemoRunning, setAutoDemoRunning] = useState(false);
  const [liveRunSeconds, setLiveRunSeconds] = useState(15);
  const [companionInput, setCompanionInput] = useState('');
  const [companionGlow, setCompanionGlow] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const autoTakeTimeoutsRef = useRef([]);
  const liveRunClockIntervalRef = useRef(null);

  // 5. Mobile Hardware Hardening: Screen Wake Lock during active rescue / triage
  const isEmergencyActive = isMetronomeActive || isListening || autoDemoRunning || (directive && !isParamedicLocked);
  useWakeLock(isEmergencyActive);

  // 6. Mobile First-Gesture Audio Unlock & iOS playback session initialization
  useEffect(() => {
    const unlockAudio = () => {
      try {
        getAudioContext();
      } catch (err) {
        console.warn('Audio unlock on first gesture error:', err);
      }
      window.removeEventListener('touchstart', unlockAudio, { capture: true });
      window.removeEventListener('pointerdown', unlockAudio, { capture: true });
      window.removeEventListener('click', unlockAudio, { capture: true });
    };

    window.addEventListener('touchstart', unlockAudio, { capture: true, passive: true });
    window.addEventListener('pointerdown', unlockAudio, { capture: true, passive: true });
    window.addEventListener('click', unlockAudio, { capture: true, passive: true });

    return () => {
      window.removeEventListener('touchstart', unlockAudio, { capture: true });
      window.removeEventListener('pointerdown', unlockAudio, { capture: true });
      window.removeEventListener('click', unlockAudio, { capture: true });
    };
  }, [getAudioContext]);

  // Lock system cleanly when paramedics arrive and speech completes
  useEffect(() => {
    if (isParamedicLocked) {
      console.log('🔒 System locked in EMS handoff mode.');
      stopListening();
      setIsModalOpen(true);
    }
  }, [isParamedicLocked, stopListening]);

  // 1. Initial Page Load: Auto-reset backend state and reverse-geocode geolocation
  useEffect(() => {
    resetSession();

    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;
          setUserCoords({ lat, lon });
          try {
            const res = await fetch(`/api/geocode?lat=${lat}&lon=${lon}`);
            const data = await res.json();
            const addr = data.address || `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            setUserLocation(addr);
            setCadInfo((prev) => ({ ...prev, address: addr }));
          } catch (e) {
            const fallback = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            setUserLocation(fallback);
            setCadInfo((prev) => ({ ...prev, address: fallback }));
          }
        },
        (err) => {
          console.warn('Geolocation fallback to standard address:', err.message);
          setCadInfo((prev) => ({
            ...prev,
            address: '201 Mission St, Financial District, San Francisco, CA',
          }));
        },
        { timeout: 5000 }
      );
    } else {
      setCadInfo((prev) => ({
        ...prev,
        address: '201 Mission St, Financial District, San Francisco, CA',
      }));
    }
  }, []);

  // Whenever handoffData becomes available or paramedic locked, open modal
  useEffect(() => {
    if (handoffData || isParamedicLocked) {
      setIsModalOpen(true);
    }
  }, [handoffData, isParamedicLocked]);

  // Trigger voice simulation via REST /api/triage
  const simulateVoice = async (phrase) => {
    getAudioContext();
    setTranscript(phrase);
    try {
      const res = await fetch('/api/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: phrase,
          location: userLocation,
          lat: userCoords.lat,
          lon: userCoords.lon,
        }),
      });
      const data = await res.json();
      updateFromData(data, true);
      if (data.companion_answer) {
        highlightCompanionCard();
      }
    } catch (e) {
      console.error('Simulation error:', e);
    }
  };

  // Direct Panic Q&A trigger
  const askCompanionQuick = async (query) => {
    if (!query) return;
    getAudioContext();
    highlightCompanionCard();
    setTranscript(query);
    try {
      const res = await fetch(`/api/test-companion?query=${encodeURIComponent(query)}`);
      const data = await res.json();
      if (data.companion_answer) {
        updateFromData(
          {
            companion_answer: data.companion_answer,
            companion_model: data.model || 'Groq LPU (qwen/qwen3.8-27b)',
          },
          true
        );
      }
    } catch (e) {
      console.error('Companion test error:', e);
    }
  };

  const triggerCompanionDirectTest = async () => {
    if (!companionInput.trim()) return;
    const q = companionInput.trim();
    setCompanionInput('');
    await askCompanionQuick(q);
  };

  const replayCurrentCompanionSpeech = () => {
    if (companionMessage && !companionMessage.includes('Standby')) {
      highlightCompanionCard();
      speakCompanion(companionMessage);
    }
  };

  const highlightCompanionCard = () => {
    setCompanionGlow(true);
    setTimeout(() => setCompanionGlow(false), 2500);
  };

  // 🎬 Video Take & Judge Simulation Helper Controls
  const triggerTakeStep = async (stepNum, isAutoDemo = false) => {
    setActiveTakeStep(stepNum);
    if (stepNum === 1) {
      // Step 1: Collapse / Not Breathing (Triage -> Dispatch & Step 1 instructions)
      await simulateVoice("Help! My dad just collapsed. He's not breathing.");
      if (isAutoDemo) {
        autoTakeTimeoutsRef.current.push(
          setTimeout(async () => {
            await simulateVoice('Hands are placed on the center of his chest.');
            autoTakeTimeoutsRef.current.push(
              setTimeout(async () => {
                await simulateVoice('Ready to compress');
              }, 2500)
            );
          }, 3200)
        );
      }
    } else if (stepNum === 2) {
      // Step 2: Hands placed & ready -> triggers 110 BPM CPR pacing
      await simulateVoice('Hands are placed on the center of his chest. Ready to compress.');
    } else if (stepNum === 3) {
      // Step 3: Ribs crack doubt -> Agent 3 Groq companion responds in <=18 words
      await simulateVoice('I heard a crack in his chest. Did I break his rib?');
    } else if (stepNum === 4) {
      // Step 4: Paramedics arrive -> Handover & permanent lock
      await simulateVoice('The paramedics are here.');
      setTimeout(() => {
        setIsModalOpen(true);
      }, 1200);
    }
  };

  // Auto-play live resuscitation drill
  const toggleAutoDemo = () => {
    if (autoDemoRunning) {
      autoTakeTimeoutsRef.current.forEach(clearTimeout);
      autoTakeTimeoutsRef.current = [];
      setAutoDemoRunning(false);
      handleManualReset();
      return;
    }

    setAutoDemoRunning(true);
    handleManualReset();

    // Step 1 at T=0s
    triggerTakeStep(1, true);

    // Gasping doubt at T=20s
    autoTakeTimeoutsRef.current.push(
      setTimeout(() => {
        simulateVoice("He's gasping. Is he breathing again?");
      }, 20000)
    );

    // Rib crack doubt at T=38s
    autoTakeTimeoutsRef.current.push(
      setTimeout(() => {
        triggerTakeStep(3);
      }, 38000)
    );

    // Paramedics arrive at T=54s
    autoTakeTimeoutsRef.current.push(
      setTimeout(() => {
        triggerTakeStep(4);
      }, 54000)
    );

    // Conclude at 68s
    autoTakeTimeoutsRef.current.push(
      setTimeout(() => {
        setAutoDemoRunning(false);
      }, 68000)
    );
  };

  // Clean Mic Toggle
  const handleMicToggle = () => {
    getAudioContext();
    if (!isListening) {
      startListening();
    } else {
      stopListening();
    }
  };

  // Clean manual reset
  const handleManualReset = () => {
    autoTakeTimeoutsRef.current.forEach(clearTimeout);
    autoTakeTimeoutsRef.current = [];
    if (liveRunClockIntervalRef.current) clearInterval(liveRunClockIntervalRef.current);
    setAutoDemoRunning(false);
    setActiveTakeStep(0);
    setIsModalOpen(false);
    resetSession();
  };

  return (
    <div className="cockpit-container">
      {/* Top Telemetry Header: LIVE CAD: KEEPALIVE EN ROUTE (ETA 3M) | LATITUDE: 0.8MS */}
      <TopTelemetryBar
        cadStatus={
          isParamedicLocked
            ? '🔒 SYSTEM LOCKED: EMS ON SCENE'
            : cadInfo.status
            ? `${cadInfo.status} (${cadInfo.unit || 'ETA 3M'})`
            : 'KEEPALIVE EN ROUTE (ETA 3M)'
        }
        latencyMs={`${latencies?.agent1 || '0.8'}MS`}
        theme={theme}
        onThemeChange={setTheme}
      />

      {/* JUDGE / SILENT DEMO BAR (One-Click Simulation for Mute / Denied Mic Environments) */}
      <section className="judge-demo-bar" aria-label="Judge Silent Demo Simulation">
        <div className="judge-demo-header">
          <div className="judge-demo-badge">
            <span className="judge-pulse-dot" />
            JUDGE / SILENT DEMO
          </div>
          <span className="judge-demo-subtext">
            No mic available? Click quick-phrases to simulate the multi-agent resuscitation flow:
          </span>
        </div>
        <div className="judge-pills-row">
          <button
            type="button"
            className={`judge-pill ${activeTakeStep === 1 ? 'active' : ''}`}
            onClick={() => triggerTakeStep(1)}
            title="Simulate: My dad collapsed, he's not breathing"
          >
            🚨 1. "Dad collapsed, not breathing"
          </button>
          <button
            type="button"
            className={`judge-pill ${activeTakeStep === 2 ? 'active' : ''}`}
            onClick={() => triggerTakeStep(2)}
            title="Simulate: Hands placed on chest, ready to compress"
          >
            👐 2. "Hands placed on chest, ready"
          </button>
          <button
            type="button"
            className={`judge-pill ${activeTakeStep === 3 ? 'active' : ''}`}
            onClick={() => triggerTakeStep(3)}
            title="Simulate: I heard a cracking rib sound"
          >
            🩺 3. "I heard a cracking rib sound"
          </button>
          <button
            type="button"
            className={`judge-pill ${activeTakeStep === 4 ? 'active' : ''}`}
            onClick={() => triggerTakeStep(4)}
            title="Simulate: The paramedics are here"
          >
            🚑 4. "The paramedics are here"
          </button>
          <button
            type="button"
            className={`judge-pill judge-pill-autorun ${autoDemoRunning ? 'running' : ''}`}
            onClick={toggleAutoDemo}
            title="Run full 70-second automated resuscitation drill"
          >
            {autoDemoRunning ? '⏹ Stop Auto-Run' : '▶ Auto-Run Demo (70s)'}
          </button>
          <button
            type="button"
            className="judge-pill judge-pill-reset"
            onClick={handleManualReset}
            title="Reset simulation to standby"
          >
            🔄 Reset
          </button>
        </div>
      </section>

      {/* STAGE 1: TRIAGE / INTAKE */}
      <Stage1TriageIntake
        isListening={isListening}
        onToggleMic={handleMicToggle}
        transcript={transcript}
        rmsEnergy={rmsEnergy}
        wpm={wpm}
        directive={directive}
        isParamedicLocked={isParamedicLocked}
        micError={voiceError}
      />

      {/* STAGE 2: ACTIVE CPR PACING (HERO) */}
      <CPRPacingHero
        isCPRActive={isMetronomeActive}
        compressionCount={compressionCount}
        beatPhase={beatPhase}
        cycleTime={cycleTime}
      />

      {/* AGENT #3: CLINICAL COMPANION BEDSIDE GUIDANCE */}
      <CompanionBubble message={companionMessage} />

      {/* STAGE 3: EMS TABLET HANDOVER */}
      <EMSHandoverCard
        handoffData={handoffData}
        compressions={compressionCount || 128}
        cycles={protocolStep}
        onOpenModal={() => setIsModalOpen(true)}
      />

      {/* EMS Handover Modal */}
      <EMSHandoverModal
        isOpen={isModalOpen}
        handoffData={handoffData}
        onReset={handleManualReset}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}
