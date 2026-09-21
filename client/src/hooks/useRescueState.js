import { useState, useCallback, useRef } from 'react';

/**
 * useRescueState
 * Central coordinator for emergency protocol state, CAD dispatch,
 * clinical step transitions, and resilient speech synthesis queue.
 * Matches client_test.html exact priority scheduling, chime, and Groq LPU voice.
 */
export function useRescueState({ onStartCPR, onStopCPR, onResetMetronome, onDuckAudio }) {
  const [activeIntent, setActiveIntent] = useState(null);
  const [protocolStep, setProtocolStep] = useState(1);
  const [isParamedicLocked, setIsParamedicLocked] = useState(false);
  const [directive, setDirective] = useState('Voice agent ready. State what happened to begin.');
  const [companionMessage, setCompanionMessage] = useState(null);
  const [isAgonalAlert, setIsAgonalAlert] = useState(false);
  const [latencies, setLatencies] = useState({
    protocolMs: '<1ms',
    companionMs: '~200ms',
    stt: 'Universal-3 Pro',
  });
  const [cadInfo, setCadInfo] = useState({
    status: '911 CAD STANDBY',
    unit: 'Unit Pending',
    address: 'Acquiring GPS...',
    aed: 'Lobby Box A (45m away)',
  });
  const [handoffData, setHandoffData] = useState(null);
  const [triageData, setTriageData] = useState(null);
  const [agent1Status, setAgent1Status] = useState('WAITING FOR VOICE');
  const [agent2Status, setAgent2Status] = useState('STANDBY');
  const [agent3Status, setAgent3Status] = useState('STANDBY (Activates during CPR)');
  const [companionModel, setCompanionModel] = useState('⚡ GROQ LPU ACTIVE');

  // Queue and deduplication refs (exact logic from client_test.html)
  const speechQueueRef = useRef([]);
  const isSynthesizingRef = useRef(false);
  const lastSpokenTextRef = useRef('');
  const lastSpokenDirectiveTextRef = useRef('');
  const activeUtteranceRef = useRef(null);
  const audioCtxRef = useRef(null);

  // Dual-Tone Reassuring Companion Chime (Web Audio API - exact from client_test.html)
  const playCompanionChime = useCallback(() => {
    try {
      if (!audioCtxRef.current) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        audioCtxRef.current = new AudioCtx();
      }
      if (audioCtxRef.current.state === 'suspended') {
        audioCtxRef.current.resume();
      }
      const ctx = audioCtxRef.current;
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      // Comforting upward interval: 523.25 Hz (C5) -> 659.25 Hz (E5)
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.12);

      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.35);
    } catch (e) {
      console.warn('Chime error:', e);
    }
  }, []);

  // Process Speech Queue with Chromium GC protection and auto-recovery
  const processSpeechQueue = useCallback(() => {
    if (!window.speechSynthesis) return;
    if (isSynthesizingRef.current || speechQueueRef.current.length === 0) return;

    const nextItem = speechQueueRef.current.shift();
    if (!nextItem || !nextItem.text) return;

    lastSpokenTextRef.current = nextItem.text;
    isSynthesizingRef.current = true;

    try {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
    } catch (e) {}

    const utterance = new SpeechSynthesisUtterance(nextItem.text);
    activeUtteranceRef.current = utterance;
    // Retain global reference to avoid Chromium GC bug where onend never fires
    window.__keepalive_utterances = window.__keepalive_utterances || [];
    window.__keepalive_utterances.push(utterance);

    utterance.rate = nextItem.options?.rate || 1.05;
    utterance.pitch = nextItem.options?.pitch || 1.0;
    utterance.lang = 'en-US';

    let watchdogTimer = null;
    let keepAliveInterval = null;

    const cleanupSpeech = () => {
      if (watchdogTimer) {
        clearTimeout(watchdogTimer);
        watchdogTimer = null;
      }
      if (keepAliveInterval) {
        clearInterval(keepAliveInterval);
        keepAliveInterval = null;
      }
      activeUtteranceRef.current = null;
      if (window.__keepalive_utterances) {
        const idx = window.__keepalive_utterances.indexOf(utterance);
        if (idx > -1) window.__keepalive_utterances.splice(idx, 1);
      }
      window.__keepalive_isSpeaking = false;
      window.__keepalive_lastSpeechEndTime = Date.now();
      isSynthesizingRef.current = false;
      if (onDuckAudio) onDuckAudio(false);
    };

    // Keepalive Heartbeat: prevents Chromium on Windows from silently pausing long sentences
    keepAliveInterval = setInterval(() => {
      if (window.speechSynthesis && window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
        window.speechSynthesis.pause();
        window.speechSynthesis.resume();
      }
    }, 2500);

    // Dynamic Watchdog: scaled to word count (never cuts off long 20-30 word clinical directives)
    const wordCount = nextItem.text.trim().split(/\s+/).length;
    const safeTimeoutMs = Math.max(16000, wordCount * 900 + 8000);

    watchdogTimer = setTimeout(() => {
      if (isSynthesizingRef.current) {
        try { window.speechSynthesis.cancel(); } catch (e) {}
        cleanupSpeech();
        setTimeout(processSpeechQueue, 60);
      }
    }, safeTimeoutMs);

    // Audio Ducking while speaking
    utterance.onstart = () => {
      window.__keepalive_isSpeaking = true;
      if (onDuckAudio) onDuckAudio(true);
    };

    utterance.onend = () => {
      cleanupSpeech();
      if (nextItem.onEnd) {
        try { nextItem.onEnd(); } catch (e) { console.warn('onEnd callback error:', e); }
      }
      setTimeout(processSpeechQueue, 100);
    };

    utterance.onerror = (err) => {
      console.warn('Speech synthesis error:', err);
      cleanupSpeech();
      if (nextItem.onEnd) {
        try { nextItem.onEnd(); } catch (e) { console.warn('onEnd callback error:', e); }
      }
      setTimeout(processSpeechQueue, 80);
    };

    try {
      window.speechSynthesis.speak(utterance);
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
    } catch (e) {
      console.warn('speak error:', e);
      cleanupSpeech();
    }
  }, [onDuckAudio]);

  // Enqueue Speech
  const enqueueSpeech = useCallback(
    (text, isPriority = false, options = {}, onEnd = null) => {
      if (!window.speechSynthesis || !text) return;
      text = text.trim();
      if (!text) return;

      const item = { text, options, onEnd };
      if (isPriority) {
        speechQueueRef.current = [item];
        if (window.speechSynthesis.speaking) {
          try { window.speechSynthesis.cancel(); } catch (e) {}
          isSynthesizingRef.current = false;
          window.__keepalive_isSpeaking = false;
        }
      } else {
        const alreadyInQueue = speechQueueRef.current.some((i) => i.text === text);
        if (!alreadyInQueue && text !== lastSpokenTextRef.current) {
          speechQueueRef.current.push(item);
        }
      }
      processSpeechQueue();
    },
    [processSpeechQueue]
  );

  // Spoken directives & companion wrappers
  const speakDirective = useCallback(
    (text, isPriority = false, onEnd = null) => {
      enqueueSpeech(text, isPriority, { rate: 1.05, pitch: 1.0 }, onEnd);
    },
    [enqueueSpeech]
  );

  const speakCompanion = useCallback(
    (text, onEnd = null) => {
      if (!text) return;
      window.__keepalive_lastSpokenCompanionText = text;
      playCompanionChime();
      if (window.speechSynthesis) {
        try {
          window.speechSynthesis.cancel();
          window.speechSynthesis.resume();
        } catch (e) {}
      }
      isSynthesizingRef.current = false;
      window.__keepalive_isSpeaking = false;
      speechQueueRef.current = [];
      setTimeout(() => {
        enqueueSpeech(text, true, { rate: 1.0, pitch: 1.02 }, onEnd);
      }, 40);
    },
    [playCompanionChime, enqueueSpeech]
  );

  // Reset Session
  const resetSession = useCallback(async () => {
    try {
      await fetch('/api/reset', { method: 'POST' });
    } catch (e) {
      console.warn('Reset request error:', e);
    }
    speechQueueRef.current = [];
    isSynthesizingRef.current = false;
    lastSpokenTextRef.current = '';
    lastSpokenDirectiveTextRef.current = '';
    window.__keepalive_lastSpokenDirectiveText = '';
    window.__keepalive_lastSpokenCompanionText = '';
    if (window.speechSynthesis) window.speechSynthesis.cancel();

    setActiveIntent(null);
    setProtocolStep(1);
    setIsParamedicLocked(false);
    setDirective('Voice agent ready. State what happened to begin.');
    setCompanionMessage(null);
    setIsAgonalAlert(false);
    setHandoffData(null);
    setTriageData(null);
    setAgent1Status('WAITING FOR VOICE');
    setAgent2Status('STANDBY');
    setAgent3Status('STANDBY (Activates during CPR)');
    if (onResetMetronome) {
      onResetMetronome();
    } else if (onStopCPR) {
      onStopCPR();
    }
  }, [onResetMetronome, onStopCPR]);

  // Unified State & Audio Dispatch from WebSocket or REST
  const updateFromData = useCallback(
    (data, isFinal = true) => {
      if (!data) return;

      // 1. Triage Intent & Latency
      if (data.triage) {
        setTriageData(data.triage);
        if (data.triage.intent) setActiveIntent(data.triage.intent);
        if (data.triage.triage_metadata?.agonal_respiration || data.triage.is_agonal_breathing) {
          setIsAgonalAlert(true);
        }
        setLatencies({
          protocolMs: data.triage.latency_ms ? `${data.triage.latency_ms.toFixed(1)}ms` : '<1ms',
          companionMs: data.companion_answer ? '~200ms' : '<1ms',
          stt: 'Universal-3 Pro',
        });
      }
      if (data.agent_1_status) setAgent1Status(data.agent_1_status);
      if (data.agent_2_status) setAgent2Status(data.agent_2_status);
      if (data.agent_3_status) setAgent3Status(data.agent_3_status);
      if (data.companion_model) setCompanionModel(data.companion_model);

      // 2. CAD Information
      if (data.cad_dispatch) {
        const unit = data.cad_dispatch.cad_unit_id || 'Medic-4';
        const inc = data.cad_dispatch.cad_incident_id || '--';
        setCadInfo((prev) => ({
          ...prev,
          status: `911 CAD: ${unit.toUpperCase()} DISPATCHED`,
          unit: `ETA: 3m | Inc: ${inc.slice(-4)}`,
        }));
      }
      if (data.aed_info?.description || data.aed_info?.aed_location) {
        const desc = data.aed_info.description || data.aed_info.aed_location;
        setCadInfo((prev) => ({
          ...prev,
          aed: desc,
        }));
      }

      // 3. Directive & Companion extraction
      const companionAns = data.companion_answer || data.companion_response;
      const directive = data.directive;
      const spokenDirectiveText =
        typeof directive === 'object' && directive !== null
          ? directive.spoken_voice_text || directive.verbatim_text || directive.directive_text || ''
          : typeof directive === 'string'
          ? directive
          : '';

      const isNewDirective = Boolean(
        spokenDirectiveText && spokenDirectiveText !== lastSpokenDirectiveTextRef.current
      );

      if (directive) {
        const displayDirective =
          typeof directive === 'object'
            ? directive.directive_text || directive.verbatim_text || ''
            : directive;
        if (displayDirective) {
          setDirective(displayDirective);
        } else if (data.triage?.line_1_directive) {
          setDirective(data.triage.line_1_directive);
        }
        if (directive.step_number) {
          setProtocolStep(directive.step_number);
        }
        if (directive.metronome_bpm > 0 && onStartCPR) {
          onStartCPR(directive.metronome_bpm);
        } else if (directive.metronome_bpm === 0 && onStopCPR) {
          onStopCPR();
        } else if (directive.step_number >= 3 && onStartCPR) {
          onStartCPR(110);
        }
      } else if (data.triage?.line_1_directive) {
        setDirective(data.triage.line_1_directive);
      }

      if (companionAns) {
        setCompanionMessage(companionAns);
      }

      // 4. Coordinated Audio Output: Agent 2 Directives have Top Priority (Never Skipped)
      if (isFinal) {
        if (isNewDirective) {
          // Agent 2 is actively guiding (e.g. positioning or 3... 2... 1... PUSH countdown):
          // Agent 2 MUST speak cleanly and exclusively! Agent 3 does NOT speak while Agent 2 guides.
          lastSpokenDirectiveTextRef.current = spokenDirectiveText;
          window.__keepalive_lastSpokenDirectiveText = spokenDirectiveText;
          speakDirective(spokenDirectiveText, true);
        } else if (companionAns) {
          // Only when Agent 2 is NOT delivering a guiding directive (during ongoing CPR):
          // Agent 3 answers caller panic questions and doubts immediately!
          speakCompanion(companionAns);
        }
      }

      // 5. EMS Paramedic Handover Lockdown & Permanent System Lock after Answer
      if (
        data.agent_2_status === 'PARAMEDICS_ARRIVED_LOCKED' ||
        data.agent_3_status === 'INCIDENT_CONCLUDED' ||
        data.handoff_card ||
        data.paramedics_arrived ||
        data.system_locked
      ) {
        setIsParamedicLocked(true);
        if (onStopCPR) onStopCPR();

        const handoff = data.handoff_card || data.ems_handoff_card || {
          status: 'Paramedics on scene. Patient handed over.',
          cycles: 1,
          cpr_duration_seconds: 120,
          total_compressions: 220,
        };
        setHandoffData(handoff);

        const finalSpeech =
          'The paramedics are in charge now. Step back and take a deep breath. You did everything right.';
        setDirective(finalSpeech);

        // Deliver concluding answer, then permanently LOCK THE SYSTEM once speech completes!
        speakCompanion(finalSpeech, () => {
          console.log('🔒 Paramedic concluding response completed. System is locked in EMS handoff mode.');
          setIsParamedicLocked(true);
          setAgent1Status('CLOSED_HANDED_OFF');
          setAgent2Status('PARAMEDICS_ARRIVED_LOCKED');
          setAgent3Status('INCIDENT_CONCLUDED');
          setDirective('🔒 SYSTEM LOCKED: Paramedics are in charge. You did everything right.');
        });
      }
    },
    [onStartCPR, onStopCPR, speakCompanion, speakDirective, enqueueSpeech, resetSession]
  );

  // Process incoming rescuer utterance through REST fallback
  const handleUtterance = useCallback(
    async (text) => {
      if (isParamedicLocked) return;
      try {
        const res = await fetch('/api/triage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text,
            location: cadInfo.address,
            lat: 37.7749,
            lon: -122.4194,
          }),
        });

        if (!res.ok) throw new Error(`Triage error: ${res.status}`);
        const data = await res.json();
        updateFromData(data, true);
      } catch (err) {
        console.warn('REST triage fallback error:', err);
      }
    },
    [isParamedicLocked, cadInfo.address, updateFromData]
  );

  // Manually advance Safety Coach clinical step
  const advanceStep = useCallback(async () => {
    try {
      const res = await fetch('/api/safety_coach/advance', { method: 'POST' });
      const data = await res.json();
      if (data.directive) {
        const stepNum = data.directive.step_number || 1;
        updateFromData({
          directive: data.directive,
          agent_2_status: stepNum >= 3 ? 'ACTIVE_CPR_110BPM' : `ACTIVE_STEP_${stepNum}`,
          agent_3_status: stepNum >= 3 ? 'ACTIVE_QNA_RESPONDER' : 'STANDBY'
        }, true);
      }
    } catch (e) {
      console.error('Advance step error:', e);
    }
  }, [updateFromData]);

  // Immediately jump to 110 BPM CPR Pacing
  const startCPR = useCallback(async () => {
    try {
      const res = await fetch('/api/safety_coach/start_cpr', { method: 'POST' });
      const data = await res.json();
      if (data.directive) {
        updateFromData({
          directive: data.directive,
          agent_2_status: 'ACTIVE_CPR_110BPM',
          agent_3_status: 'ACTIVE_CPR_PACING_COMPANION'
        }, true);
      }
    } catch (e) {
      console.error('Start CPR error:', e);
    }
  }, [updateFromData]);

  return {
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
  };
}
