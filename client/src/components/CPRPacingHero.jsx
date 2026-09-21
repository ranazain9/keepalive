import React from 'react';
import { CPRVideoPlayer } from './CPRVideoPlayer';

/**
 * CPRPacingHero (STAGE 2: ACTIVE CPR PACING)
 * Clinical Resuscitation Cockpit:
 * - Top Navy Ribbon: STAGE 2: ACTIVE CPR PACING (HERO) with ECG lines
 * - Left: High-Definition Clinical CPR Video + Glowing Sternum Target + Vertical Depth Gauge (≥ 2.0")
 * - Right: Giant 110 BPM Rhythm Ring + Red Crosshairs + Live Compressions & 2-Min Swap Bar
 */
export function CPRPacingHero({
  isCPRActive = false,
  compressionCount = 0,
  beatPhase = 0,
  cycleTime = 0,
}) {
  // Format MM:SS for 2-min cycle
  const formatCycle = (sec) => {
    const m = String(Math.floor(sec / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    return `${m}:${s}`;
  };

  // 2-minute cycle progress (120s)
  const swapProgress = Math.min(100, ((cycleTime % 120) / 120) * 100);

  // Dynamic compression depth calculation synced to beat phase (Target: At least 2 inches / AHA standard)
  const depthInches = isCPRActive ? (2.0 + Math.sin(beatPhase * Math.PI) * 0.25).toFixed(1) : '2.0';
  const depthPercent = isCPRActive ? 75 + Math.sin(beatPhase * Math.PI) * 20 : 75;

  return (
    <div className="stage-card stage-2-container">
      {/* Deep Navy Ribbon Banner with ECG flourishes */}
      <div className="stage-2-ribbon">
        <svg viewBox="0 0 100 24" className="ribbon-ecg left" fill="none">
          <path d="M0,12 L30,12 L35,2 L40,22 L45,8 L50,16 L55,12 L100,12" stroke="#38BDF8" strokeWidth="2" />
        </svg>
        <span className="ribbon-title">STAGE 2: ACTIVE CPR PACING (HERO)</span>
        <svg viewBox="0 0 100 24" className="ribbon-ecg right" fill="none">
          <path d="M0,12 L45,12 L50,8 L55,22 L60,2 L65,16 L70,12 L100,12" stroke="#38BDF8" strokeWidth="2" />
        </svg>
      </div>

      {/* Main Split Grid: CPR Video on Left, Giant Rhythm Ring on Right */}
      <div className="stage-2-grid">
        {/* Left Column: Clinical Video Demonstration */}
        <div className="stage-col manikin-col">
          <div className="col-header-row">
            <div className="col-header-title">CLINICAL CPR PACING DEMO (110 BPM)</div>
          </div>

          <div className="manikin-stage-split">
            {/* Annotation Bullets */}
            <div className="manikin-annotations">
              <div className="annotation-item">• Heel on chest center</div>
              <div className="annotation-item">• Lock elbows straight</div>
              <div className="annotation-item">• Target: ≥ 2.0" depth</div>
            </div>

            {/* Center Visual Component: Clean High-Definition Clinical Video */}
            <div className="manikin-torso-container">
              <CPRVideoPlayer isCPRActive={isCPRActive} bpm={110} beatPhase={beatPhase} />
            </div>

            {/* Vertical Graduated Depth Gauge */}
            <div className="depth-gauge-meter">
              <div className="depth-readout">
                <span className="depth-label">DEPTH</span>
                <span className="depth-value">{depthInches}"</span>
                <span style={{ fontSize: '9px', color: 'var(--text-muted)', display: 'block' }}>≥ 2.0"</span>
              </div>

              <div className="depth-graduated-track">
                {/* Scale markings */}
                <div className="depth-ticks">
                  <span style={{ top: '0%' }}>2.4"</span>
                  <span style={{ top: '25%' }}>2.0"</span>
                  <span style={{ top: '65%' }}>1.0"</span>
                  <span style={{ top: '92%' }}>0"</span>
                </div>

                {/* Vertical Fill Tube */}
                <div className="depth-bar-cylinder">
                  <div
                    className="depth-cylinder-fill"
                    style={{ height: `${depthPercent}%` }}
                  ></div>
                </div>

                {/* Target indicator arrow */}
                <div className="depth-target-arrow">◀</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Giant 110 BPM Rhythm Ring */}
        <div className="stage-col rhythm-col">
          <div className="col-header-title">GIANT 110 BPM RHYTHM RING</div>
          <div className="col-header-sub">• Pulsing 110 BPM ring synced to audio clicks</div>

          {/* Giant Rhythm Ring Centerpiece */}
          <div className="rhythm-ring-centerpiece">
            {/* Red Crosshair Lines */}
            <div className="crosshair-line horizontal"></div>
            <div className="crosshair-line vertical"></div>

            {/* Concentric Pulsing Rhythm Rings */}
            <div className={`giant-ring-outer ${isCPRActive ? 'active-beat' : ''}`}>
              <div className="giant-ring-mid">
                <div className="giant-ring-inner">
                  {/* Digital BPM Readout */}
                  <div className="ring-bpm-number">110</div>
                  <div className="ring-bpm-label">BPM</div>
                </div>
              </div>
            </div>
          </div>

          {/* Rhythm Bottom Counters */}
          <div className="rhythm-stats-row">
            {/* Left Stat: Live Compressions Counter */}
            <div className="rhythm-stat-card">
              <div className="circle-badge cyan">{compressionCount}</div>
              <div className="stat-meta">
                <div className="stat-name">LIVE COMPRESSIONS</div>
                <svg viewBox="0 0 80 12" className="live-cyan-ecg" fill="none">
                  <path d="M0,6 L20,6 L24,1 L28,11 L32,4 L36,8 L40,6 L80,6" stroke="#00A8E8" strokeWidth="1.5" />
                </svg>
              </div>
            </div>

            {/* Right Stat: 2-Minute Rescuer Fatigue Swap Countdown */}
            <div className="rhythm-stat-card">
              <div className="circle-badge amber">{formatCycle(cycleTime)}</div>
              <div className="stat-meta">
                <div className="stat-name">RESCUER FATIGUE (2 MIN SWAP)</div>
                <div className="fatigue-progress-track">
                  <div
                    className="fatigue-progress-fill"
                    style={{ width: `${swapProgress}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
