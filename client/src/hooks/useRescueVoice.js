import { useRef, useState, useCallback, useEffect } from 'react';

/**
 * Downsample native browser audio (44.1k/48k) to pristine 16kHz Int16 for AssemblyAI
 * (Exact algorithm from client_test.html)
 */
function downsampleBufferTo16k(inputData, inputSampleRate) {
  if (inputSampleRate === 16000) {
    const pcm16 = new Int16Array(inputData.length);
    for (let i = 0; i < inputData.length; i++) {
      const s = Math.max(-1, Math.min(1, inputData[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return pcm16;
  }
  const ratio = inputSampleRate / 16000;
  const newLength = Math.round(inputData.length / ratio);
  const result = new Int16Array(newLength);
  let offsetResult = 0;
  let offsetBuffer = 0;
  while (offsetResult < result.length) {
    const nextOffset = Math.round((offsetResult + 1) * ratio);
    let accum = 0,
      count = 0;
    for (let i = offsetBuffer; i < nextOffset && i < inputData.length; i++) {
      accum += inputData[i];
      count++;
    }
    const val = count > 0 ? accum / count : inputData[offsetBuffer];
    const s = Math.max(-1, Math.min(1, val));
    result[offsetResult] = s < 0 ? s * 0x8000 : s * 0x7fff;
    offsetResult++;
    offsetBuffer = nextOffset;
  }
  return result;
}

/**
 * Acoustic Echo Detection (Exact algorithm from client_test.html)
 */
export function isEchoOfSpeech(transcript, spokenTexts) {
  if (!transcript || !spokenTexts) return false;
  const tWords = transcript
    .toLowerCase()
    .replace(/[^a-z0-9 ]/g, '')
    .split(/\s+/)
    .filter((w) => w.length > 2);
  if (tWords.length === 0) return false;
  for (const text of spokenTexts) {
    if (!text) continue;
    const dWords = text
      .toLowerCase()
      .replace(/[^a-z0-9 ]/g, '')
      .split(/\s+/)
      .filter((w) => w.length > 2);
    if (dWords.length === 0) continue;
    let matches = 0;
    for (const w of tWords) {
      if (dWords.includes(w)) matches++;
    }
    // High-confidence echo: either 70%+ of words match or all words of a short phrase match exactly
    if (matches / tWords.length >= 0.70 || (tWords.length <= 2 && matches === tWords.length && matches >= 2)) {
      return true;
    }
  }
  return false;
}

/**
 * useRescueVoice
 * Captures 16kHz PCM audio and streams to AssemblyAI v3 WebSocket (/ws/triage)
 * Identical architecture to client_test.html.
 */
export function useRescueVoice({
  onTriageUpdate,
  onTranscriptUpdate,
  userLocation = 'Acquiring GPS...',
  userLat = 37.7749,
  userLon = -122.4194,
}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [rmsEnergy, setRmsEnergy] = useState(0);
  const [wpm, setWpm] = useState(0);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const processorRef = useRef(null);
  const speechStartTimeRef = useRef(null);
  const onTriageUpdateRef = useRef(onTriageUpdate);
  onTriageUpdateRef.current = onTriageUpdate;
  const onTranscriptUpdateRef = useRef(onTranscriptUpdate);
  onTranscriptUpdateRef.current = onTranscriptUpdate;

  // Stop recording and close connections cleanly
  const stopListening = useCallback(() => {
    if (processorRef.current) {
      try {
        processorRef.current.disconnect();
      } catch (e) {}
      processorRef.current = null;
    }
    if (audioCtxRef.current) {
      try {
        audioCtxRef.current.close();
      } catch (e) {}
      audioCtxRef.current = null;
    }
    if (mediaStreamRef.current) {
      try {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      } catch (e) {}
      mediaStreamRef.current = null;
    }
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (e) {}
      wsRef.current = null;
    }

    setIsListening(false);
    setRmsEnergy(0);
    speechStartTimeRef.current = null;
  }, []);

  // Start real-time audio pipeline and WebSocket stream
  const startListening = useCallback(async () => {
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }
    setError(null);
    speechStartTimeRef.current = Date.now();

    try {
      // 1. Microphone stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      mediaStreamRef.current = stream;

      // 2. AudioContext
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioCtx();
      if (ctx.state === 'suspended') {
        await ctx.resume();
      }
      audioCtxRef.current = ctx;
      const nativeSampleRate = ctx.sampleRate;

      // 3. Connect to FastAPI WebSocket (/ws/triage)
      const locQuery = encodeURIComponent(userLocation);
      let wsTargetUrl = '';
      const customWs = import.meta.env?.VITE_WS_URL;

      if (customWs) {
        const cleanBase = customWs.replace(/\/+$/, '');
        wsTargetUrl = `${cleanBase}/ws/triage?location=${locQuery}&lat=${userLat}&lon=${userLon}`;
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        if (window.location.port === '5173') {
          const hostIp = window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
          wsTargetUrl = `${protocol}//${hostIp}:8000/ws/triage?location=${locQuery}&lat=${userLat}&lon=${userLon}`;
        } else {
          wsTargetUrl = `${protocol}//${window.location.host}/ws/triage?location=${locQuery}&lat=${userLat}&lon=${userLon}`;
        }
      }

      const ws = new WebSocket(wsTargetUrl);
      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('🎙️ Real-time Rescue WebSocket connected to', host);
        setIsListening(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.error) {
            setError(data.error);
            console.warn('Voice agent warning from server:', data.error);
            return;
          }
          const isSpeaking = Boolean(window.__keepalive_isSpeaking);
          const recentlySpoke = (Date.now() - (window.__keepalive_lastSpeechEndTime || 0)) < 1200;
          const spokenDirective = window.__keepalive_lastSpokenDirectiveText || '';
          const spokenCompanion = window.__keepalive_lastSpokenCompanionText || '';

          if (data.type === 'PARTIAL_TRANSCRIPT') {
            // Acoustic Echo Filter on live streaming partials
            if (
              (isSpeaking || recentlySpoke) &&
              isEchoOfSpeech(data.transcript, [spokenDirective, spokenCompanion])
            ) {
              return;
            }
            setTranscript(data.transcript);
            if (onTranscriptUpdateRef.current)
              onTranscriptUpdateRef.current(data.transcript);
            return;
          }
          if (data.type === 'TRIAGE_UPDATE') {
            // Acoustic Echo Filter on final triage updates
            if (
              (isSpeaking || recentlySpoke) &&
              isEchoOfSpeech(data.transcript, [spokenDirective, spokenCompanion])
            ) {
              console.log('Acoustic echo filtered from WS:', data.transcript);
              return;
            }

            console.log('⚡ Received TRIAGE_UPDATE:', data);
            setTranscript(data.transcript);
            if (onTranscriptUpdateRef.current)
              onTranscriptUpdateRef.current(data.transcript);

            // Compute WPM velocity
            if (!speechStartTimeRef.current) speechStartTimeRef.current = Date.now();
            const elapsedSec = (Date.now() - speechStartTimeRef.current) / 1000.0;
            const wordCount = data.transcript.trim().split(/\s+/).length;
            if (elapsedSec > 0.5) {
              const calcWpm = Math.round((wordCount / elapsedSec) * 60);
              setWpm(calcWpm);
            }

            if (onTriageUpdateRef.current) onTriageUpdateRef.current(data);
          }
        } catch (e) {
          console.warn('WS parse error:', e);
        }
      };

      ws.onerror = (err) => {
        console.warn('WebSocket stream warning:', err);
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setIsListening(false);
        wsRef.current = null;
      };

      // 4. Client-side Speech Recognition Fallback (Automatic Instant Failover)
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      let recognition = null;
      if (SpeechRecognition) {
        try {
          recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = 'en-US';
          recognition.onresult = async (ev) => {
            const isSpeaking = window.__keepalive_isSpeaking;
            const lastEndTime = window.__keepalive_lastSpeechEndTime || 0;
            if (isSpeaking || Date.now() - lastEndTime < 350) return;

            let localText = '';
            let isFinalResult = false;
            for (let i = ev.resultIndex; i < ev.results.length; ++i) {
              localText += ev.results[i][0].transcript;
              if (ev.results[i].isFinal) isFinalResult = true;
            }
            localText = localText.trim();
            if (localText) {
              setTranscript(localText);
              if (onTranscriptUpdateRef.current) onTranscriptUpdateRef.current(localText);

              // If AssemblyAI WebSocket is not connected or experienced an error, seamlessly dispatch to /api/triage
              if (
                isFinalResult &&
                (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN)
              ) {
                console.log('⚡ Using client speech fallback to /api/triage:', localText);
                try {
                  const res = await fetch('/api/triage', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      text: localText,
                      location: userLocation,
                      lat: userLat,
                      lon: userLon,
                    }),
                  });
                  const triageData = await res.json();
                  triageData.is_final = true;
                  if (onTriageUpdateRef.current) onTriageUpdateRef.current(triageData);
                } catch (e) {
                  console.warn('Fallback triage error:', e);
                }
              }
            }
          };
          recognition.start();
        } catch (re) {
          console.warn('SpeechRecognition initialization note:', re);
        }
      }

      // 5. Audio Pipeline: stream mic -> processor (2048 samples = ~42ms) -> 16kHz PCM downsampler -> WebSocket
      const source = ctx.createMediaStreamSource(stream);
      const processor = ctx.createScriptProcessor(2048, 1, 1);
      processorRef.current = processor;

      const silentSink = ctx.createGain();
      silentSink.gain.value = 0.0;

      source.connect(processor);
      processor.connect(silentSink);
      silentSink.connect(ctx.destination);

      processor.onaudioprocess = (e) => {
        const isSpeaking = window.__keepalive_isSpeaking;
        const lastEndTime = window.__keepalive_lastSpeechEndTime || 0;

        // Acoustic Gating: Mute mic packets while agent voice speaks through loudspeaker
        if (isSpeaking || Date.now() - lastEndTime < 350) {
          setRmsEnergy(0);
          return;
        }

        const inputData = e.inputBuffer.getChannelData(0);

        let sumSquares = 0;
        for (let i = 0; i < inputData.length; i++) {
          sumSquares += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sumSquares / inputData.length);
        setRmsEnergy(rms);

        // Resample to 16,000 Hz Int16 PCM and stream to AssemblyAI
        const pcm16 = downsampleBufferTo16k(inputData, nativeSampleRate);
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(pcm16.buffer);
        }
      };

      setIsListening(true);
    } catch (err) {
      console.error('Microphone error:', err);
      setError('Microphone access denied or not available.');
    }
  }, [userLocation, userLat, userLon]);

  useEffect(() => {
    return () => {
      stopListening();
    };
  }, [stopListening]);

  return {
    isListening,
    transcript,
    setTranscript,
    rmsEnergy,
    wpm,
    error,
    startListening,
    stopListening,
  };
}
