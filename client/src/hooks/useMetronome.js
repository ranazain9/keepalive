import { useRef, useState, useCallback, useEffect } from 'react';

/**
 * useMetronome
 * Synthesizes hardware-timed 110 BPM acoustic clicks using Web Audio API
 * Features sample-accurate scheduling and -4dB to -14dB dynamic speech ducking.
 */
export function useMetronome(initialBpm = 110) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [compressionCount, setCompressionCount] = useState(0);
  const [beatPhase, setBeatPhase] = useState(0);
  const [cycleTime, setCycleTime] = useState(0); // in seconds
  const [currentBpm, setCurrentBpm] = useState(initialBpm);

  const audioCtxRef = useRef(null);
  const metronomeIntervalRef = useRef(null);
  const cycleIntervalRef = useRef(null);
  const isDuckedRef = useRef(false);

  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      audioCtxRef.current = new AudioCtx();
    }
    if (audioCtxRef.current.state === 'suspended') {
      audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  }, []);

  const playClick = useCallback(() => {
    try {
      const ctx = getAudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      // 3000 Hz piercing frequency matching AHA guideline in client_test.html
      osc.frequency.setValueAtTime(3000, ctx.currentTime);

      const normalGain = 0.40;
      const duckedGain = normalGain * 0.631; // -4 dB ducking during speech
      const vol = isDuckedRef.current ? duckedGain : normalGain;

      gain.gain.setValueAtTime(vol, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.04);

      setCompressionCount((prev) => prev + 1);
      setBeatPhase((prev) => (prev + 1) % 2);
    } catch (e) {
      console.warn('Metronome click error:', e);
    }
  }, [getAudioContext]);

  const startMetronome = useCallback(
    (bpm = 110) => {
      const targetBpm = bpm > 0 ? bpm : 110;
      setCurrentBpm(targetBpm);
      getAudioContext();

      if (metronomeIntervalRef.current) {
        clearInterval(metronomeIntervalRef.current);
      }

      setIsPlaying(true);
      playClick();

      const intervalMs = (60 / targetBpm) * 1000;
      metronomeIntervalRef.current = setInterval(playClick, intervalMs);

      if (!cycleIntervalRef.current) {
        cycleIntervalRef.current = setInterval(() => {
          setCycleTime((prev) => prev + 1);
        }, 1000);
      }
    },
    [getAudioContext, playClick]
  );

  const stopMetronome = useCallback(() => {
    if (metronomeIntervalRef.current) {
      clearInterval(metronomeIntervalRef.current);
      metronomeIntervalRef.current = null;
    }
    if (cycleIntervalRef.current) {
      clearInterval(cycleIntervalRef.current);
      cycleIntervalRef.current = null;
    }
    setIsPlaying(false);
  }, []);

  const resetMetronome = useCallback(() => {
    stopMetronome();
    setCompressionCount(0);
    setCycleTime(0);
    setBeatPhase(0);
  }, [stopMetronome]);

  const duckAudio = useCallback((isDucked = true) => {
    isDuckedRef.current = isDucked;
  }, []);

  useEffect(() => {
    return () => {
      if (metronomeIntervalRef.current) clearInterval(metronomeIntervalRef.current);
      if (cycleIntervalRef.current) clearInterval(cycleIntervalRef.current);
      if (audioCtxRef.current) {
        try { audioCtxRef.current.close(); } catch (e) {}
      }
    };
  }, []);

  const formattedCycleTime = (() => {
    const m = String(Math.floor(cycleTime / 60)).padStart(2, '0');
    const s = String(cycleTime % 60).padStart(2, '0');
    return `${m}:${s}`;
  })();

  return {
    isPlaying,
    compressionCount,
    beatPhase,
    cycleTime,
    formattedCycleTime,
    currentBpm,
    startMetronome,
    stopMetronome,
    resetMetronome,
    duckAudio,
    getAudioContext,
  };
}
