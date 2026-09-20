import React, { useRef, useEffect } from 'react';

/**
 * CPRVideoPlayer
 * High-definition clinical CPR video player replacing procedural 3D WebGL manikin.
 * Features:
 * - Dynamic playback rate synchronization to active BPM (base: 110 BPM)
 * - Auto-play on active CPR / graceful pause on standby
 * - Medical diagnostic HUD overlays (sternum target reticle, scanlines, live telemetry badge)
 * - Muted audio output to avoid interference with 3000 Hz metronome and AI voice
 */
export function CPRVideoPlayer({
  isCPRActive = false,
  bpm = 110,
  beatPhase = 0,
}) {
  const videoRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (isCPRActive) {
      // Calculate dynamic playback rate (calibrated for standard 110 BPM cadence)
      const targetRate = Math.max(0.75, Math.min(1.5, bpm / 110));
      video.playbackRate = targetRate;
      
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.catch((err) => {
          console.warn('CPR Video auto-play deferred:', err);
        });
      }
    } else {
      video.pause();
    }
  }, [isCPRActive, bpm]);

  return (
    <div className="cpr-video-monitor-container">
      {/* Primary Video Element */}
      <video
        ref={videoRef}
        src="/videos/cpr_demonstration.mp4"
        className="cpr-video-element"
        loop
        muted
        playsInline
        preload="auto"
      />

      {/* Subtle CRT / Medical Monitor Scanlines */}
      <div className="cpr-video-scanlines" />

      {/* Medical HUD Diagnostic Vignette & Borders */}
      <div className="cpr-video-vignette" />

      {/* Top Telemetry Overlay Badge */}
      <div className="cpr-video-status-bar">
        <div className={`cpr-status-pill ${isCPRActive ? 'active' : 'standby'}`}>
          <span className="cpr-status-dot" />
          <span className="cpr-status-text">
            {isCPRActive ? `PACING: ${bpm} BPM ACTIVE` : 'PACING STANDBY'}
          </span>
        </div>
        <div className="cpr-hud-tag">CLINICAL FEED</div>
      </div>

      {/* Sternum Compression Target Reticle Overlay */}
      <div className={`cpr-sternum-reticle ${isCPRActive ? 'pulsing' : ''}`}>
        <div className="reticle-ring ring-outer" />
        <div className="reticle-ring ring-inner" />
        <div className="reticle-crosshair ch-x" />
        <div className="reticle-crosshair ch-y" />
        <span className="reticle-label">STERNUM TARGET</span>
      </div>

      {/* Standby Watermark when Paused */}
      {!isCPRActive && (
        <div className="cpr-standby-overlay">
          <div className="cpr-standby-pill">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M8 5v14l11-7z" />
            </svg>
            <span>READY FOR COMPRESSIONS</span>
          </div>
        </div>
      )}
    </div>
  );
}
