import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { useMetronome } from './hooks/useMetronome';
import { useRescueVoice } from './hooks/useRescueVoice';
import { useRescueState } from './hooks/useRescueState';
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
  const [is911Active, setIs911Active] = useState(false);
  const [activeTakeStep, setActiveTakeStep] = useState(0);
  const [autoDemoRunning, setAutoDemoRunning] = useState(false);
  const [liveRunSeconds, setLiveRunSeconds] = useState(15);
  const [companionInput, setCompanionInput] = useState('');
  const [companionGlow, setCompanionGlow] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const autoTakeTimeoutsRef = useRef([]);
  const liveRunClockIntervalRef = useRef(null);

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
            const res = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`
            );
            const data = await res.json();
            const addr =
              data.display_name ||
              (data.address
                ? `${data.address.road || ''}, ${data.address.city || data.address.town || ''}, ${data.address.country || ''}`
                : `${lat.toFixed(4)}, ${lon.toFixed(4)}`);
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

  // 🎬 70s Video Take Helper Controls
  const triggerTakeStep = async (stepNum, isAutoDemo = false) => {
    setActiveTakeStep(stepNum);
    if (stepNum === 1) {
      // 0:15 Collapse / Not Breathing
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
      // 0:45 Gasping doubt
      await simulateVoice("He's gasping. Is he breathing again?");
    } else if (stepNum === 3) {
      // 1:08 Ribs crack doubt
      await simulateVoice('I heard a crack in his chest. Did I break his rib?');
    } else if (stepNum === 4) {
      // 1:14 Paramedics arrive
      await simulateVoice('The paramedics are here.');
      setTimeout(() => {
        setIsModalOpen(true);
      }, 1200);
    }
  };

  // Auto-play 70s live video take
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

    // Step 2 at T=22s
    autoTakeTimeoutsRef.current.push(
      setTimeout(() => {
        if (autoDemoRunning) triggerTakeStep(2);
      }, 22000)
    );

    // Step 3 at T=44s
    autoTakeTimeoutsRef.current.push(
      setTimeout(() => {
        if (autoDemoRunning) triggerTakeStep(3);
      }, 44000)
    );

    // Step 4 at T=56s
    autoTakeTimeoutsRef.current.push(
      setTimeout(() => {
        if (autoDemoRunning) triggerTakeStep(4);
      }, 56000)
    );

    // Conclude at 70s
    autoTakeTimeoutsRef.current.push(
      setTimeout(() => {
        setAutoDemoRunning(false);
      }, 70000)
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
        cadStatus={cadInfo.status ? `${cadInfo.status} (${cadInfo.unit || 'ETA 3M'})` : 'KEEPALIVE EN ROUTE (ETA 3M)'}
        latencyMs={`${latencies?.agent1 || '0.8'}MS`}
      />

      {/* STAGE 1: TRIAGE / INTAKE */}
      <Stage1TriageIntake
        isListening={isListening}
        onToggleMic={handleMicToggle}
        transcript={transcript}
        rmsEnergy={rmsEnergy}
        wpm={wpm}
        directive={directive}
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
