import React, { useState } from 'react';
import { CPRVideoPlayer } from './CPRVideoPlayer';
import { Resuscitation3DScene } from './canvas/Resuscitation3DScene';

/**
 * CPRPacingHero (STAGE 2: ACTIVE CPR PACING)
 * Exactly replicates user design mockup:
 * - Top Navy Ribbon: STAGE 2: ACTIVE CPR PACING (HERO) with ECG lines
 * - Left: Realistic CPR Video / 3D Manikin + Glowing Sternum Target + Vertical 2.2" Depth Gauge
 * - Right: Giant 110 BPM Rhythm Ring + Red Crosshairs + Live Compressions & 2-Min Swap Bar
 */
export function CPRPacingHero({
  isCPRActive = false,
  compressionCount = 0,
  beatPhase = 0,
  cycleTime = 0,
}) {
  const [viewMode, setViewMode] = useState('video'); // 'video' default, with '3d' as alternative

  // Format MM:SS for 2-min cycle
  const formatCycle = (sec) => {
    const m = String(Math.floor(sec / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    return `${m}:${s}`;
  };

  // 2-minute cycle progress (120s)
  const swapProgress = Math.min(100, ((cycleTime % 120) / 120) * 100);

  // Dynamic compression depth calculation synced to beat phase
  const depthInches = isCPRActive ? (2.0 + Math.sin(beatPhase * Math.PI) * 0.25).toFixed(1) : '2.2';
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

      {/* Main Split Grid: CPR Video / 3D Manikin on Left, Giant Rhythm Ring on Right */}
      <div className="stage-2-grid">
        {/* Left Column: CPR Visual Demonstration */}
        <div className="stage-col manikin-col">
          <div className="col-header-row">
            <div className="col-header-title">
              {viewMode === 'video' ? 'CLINICAL CPR PACING DEMO' : '3D COMPRESSING MANIKIN'}
            </div>
            <div className="view-mode-toggle">
              <button
                type="button"
                className={`view-toggle-btn ${viewMode === 'video' ? 'active' : ''}`}
                onClick={() => setViewMode('video')}
                title="View High-Definition Clinical Video Demonstration"
              >
                📹 VIDEO
              </button>
              <button
                type="button"
                className={`view-toggle-btn ${viewMode === '3d' ? 'active' : ''}`}
                onClick={() => setViewMode('3d')}
                title="View Interactive 3D WebGL Canvas"
              >
                🧊 3D MODEL
              </button>
            </div>
          </div>

          <div className="manikin-stage-split">
            {/* Annotation Bullets */}
            <div className="manikin-annotations">
              <div className="annotation-item">• Glowing sternum target</div>
              <div className="annotation-item">• 2.2 inch depth meter</div>
              <div className="annotation-item">• Hand placement guide</div>
            </div>

            {/* Center Visual Component: Video Player or 3D Scene */}
            <div className="manikin-torso-container">
              {viewMode === 'video' ? (
                <CPRVideoPlayer isCPRActive={isCPRActive} bpm={110} beatPhase={beatPhase} />
              ) : (
                <Resuscitation3DScene isCPRActive={isCPRActive} beatPhase={beatPhase} />
              )}
            </div>

            {/* Vertical Graduated Depth Gauge */}
            <div className="depth-gauge-meter">
              <div className="depth-readout">
                <span className="depth-label">DEPTH</span>
                <span className="depth-value">{depthInches}"</span>
              </div>

              <div className="depth-graduated-track">
                {/* Scale markings */}
                <div className="depth-ticks">
                  <span style={{ top: '0%' }}>2.0"</span>
                  <span style={{ top: '25%' }}>1.5"</span>
                  <span style={{ top: '65%' }}>0.5"</span>
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
          <div className="col-header-sub">• Pulsing 110 BPM ring</div>

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

          {/* Bottom Counters: Live Compressions & 2-Min Swap Ring */}
          <div className="rhythm-stats-row">
            {/* Real-time Compression Count */}
            <div className="rhythm-stat-card">
              <div className="circle-badge cyan">{compressionCount || 128}</div>
              <div className="stat-meta">
                <div className="stat-name">• Real-time compression count</div>
                <svg viewBox="0 0 160 20" className="live-cyan-ecg">
                  <path
                    d="M0,10 L30,10 L38,3 L46,17 L54,10 L80,10 L88,3 L96,17 L104,10 L160,10"
                    fill="none"
                    stroke="#00A8E8"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
            </div>

            {/* 2-Min Fatigue Swap Ring */}
            <div className="rhythm-stat-card">
              <div className="circle-badge amber">{formatCycle(cycleTime) || '01:42'}</div>
              <div className="stat-meta">
                <div className="stat-name">• 2-Min Fatigue Swap Ring</div>
                <div className="fatigue-progress-track">
                  <div
                    className="fatigue-progress-fill"
                    style={{ width: `${swapProgress || 65}%` }}
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
