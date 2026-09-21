import React, { useEffect, useRef } from 'react';

/**
 * Stage1TriageIntake (STAGE 1: TRIAGE / INTAKE)
 * Exactly replicates Stage 1 of the user design mockup:
 * - Left: Glowing concentric cyan mic orb
 * - Center: Dynamic live audio soundwave visualizer
 * - Center-Bottom: "Tell me what happened" prompt bubble / live transcription
 * - Right: Vertical audio level / volume meter
 */
export function Stage1TriageIntake({
  isListening = false,
  onToggleMic = () => {},
  transcript = '',
  rmsEnergy = 0,
  wpm = 0,
  directive = 'Tell me what happened',
  onStartCPR = null,
}) {
  const canvasRef = useRef(null);

  // Dynamic cyan audio soundwave animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    const drawWave = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const height = canvas.height;
      const centerY = height / 2;

      // Draw horizontal waveform bars matching mockup
      const bars = 48;
      const barWidth = 3;
      const spacing = (width - bars * barWidth) / (bars - 1);
      const activeEnergy = Math.max(0.12, rmsEnergy);

      for (let i = 0; i < bars; i++) {
        const x = i * (barWidth + spacing);
        // Harmonic envelope peaking in the center
        const envelope = Math.sin((i / (bars - 1)) * Math.PI);
        const wave = Math.sin(i * 0.4 + Date.now() * 0.006);
        const barHeight = Math.max(6, activeEnergy * 44 * envelope * (0.5 + 0.5 * Math.abs(wave)));

        ctx.fillStyle = isListening ? '#00A8E8' : 'rgba(0, 168, 232, 0.45)';
        ctx.beginPath();
        ctx.roundRect(x, centerY - barHeight / 2, barWidth, barHeight, 2);
        ctx.fill();
      }

      animId = requestAnimationFrame(drawWave);
    };

    drawWave();
    return () => cancelAnimationFrame(animId);
  }, [isListening, rmsEnergy]);

  // Volume meter height (0 - 100%)
  const meterHeight = Math.min(100, Math.max(15, rmsEnergy * 250));

  return (
    <div className="stage-card stage-1-container">
      <div className="stage-1-header">
        <span className="stage-1-title">STAGE 1: TRIAGE / INTAKE</span>
      </div>

      <div className="stage-1-body">
        {/* Left: Glowing Concentric Mic Orb */}
        <button
          className={`intake-mic-orb ${isListening ? 'active-listening' : ''}`}
          onClick={onToggleMic}
          title={isListening ? 'Click to Stop Listening' : 'Click to Speak'}
        >
          <div className="orb-ring ring-outer"></div>
          <div className="orb-ring ring-mid"></div>
          <div className="orb-core">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00A8E8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <line x1="12" x2="12" y1="19" y2="22"></line>
            </svg>
          </div>
        </button>

        {/* Center: Live Waveform Visualizer & Prompt Bubble */}
        <div className="stage-1-center">
          <canvas ref={canvasRef} width={520} height={56} className="waveform-canvas" />

          {/* Cyan "Tell me what happened" / Live Streaming Prompt Bubble & Directives */}
          <div className="intake-prompt-bubble" style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'center' }}>
            {transcript && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                🗣️ "{transcript}"
              </div>
            )}
            <div className="prompt-text" style={{ fontWeight: 700, color: directive ? '#00E5FF' : 'inherit' }}>
              {directive ? `🛡️ ${directive}` : (transcript ? '' : 'Tell me what happened')}
            </div>
            {directive && onStartCPR && (
              <button
                type="button"
                onClick={onStartCPR}
                style={{
                  marginTop: '4px',
                  background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
                  border: '1px solid rgba(239, 68, 68, 0.6)',
                  color: '#FFFFFF',
                  borderRadius: '999px',
                  padding: '4px 16px',
                  fontSize: '11px',
                  fontWeight: 800,
                  cursor: 'pointer',
                  letterSpacing: '0.5px',
                  boxShadow: '0 0 12px rgba(239, 68, 68, 0.4)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <span>▶ START 110 BPM CPR NOW</span>
              </button>
            )}
          </div>
        </div>

        {/* Right: Vertical Volume / Energy Level Meter */}
        <div className="volume-meter-track" title="Microphone Input Energy">
          <div className="meter-cylinder">
            <div className="meter-fill" style={{ height: `${meterHeight}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
}
