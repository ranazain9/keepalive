import React from 'react';

/**
 * TopTelemetryBar
 * Replicates the top header pill from the clinical design mockup:
 * - Left: "LIVE CAD: KEEPALIVE EN ROUTE (ETA 3M)" with pulsing red dot
 * - Center: 3-Way Theme Switcher (Clinical Light, Tactical Dark HUD, High-Contrast Emergency)
 * - Right: "LATITUDE / LATENCY: 0.8MS"
 */
export function TopTelemetryBar({
  cadStatus = 'KEEPALIVE EN ROUTE (ETA 3M)',
  latencyMs = '0.8MS',
  theme = 'clinical',
  onThemeChange = () => {},
}) {
  return (
    <div className="top-telemetry-bar">
      {/* Left: LIVE CAD indicator */}
      <div className="telemetry-left">
        <span className="live-cad-dot"></span>
        <span className="live-cad-tag">LIVE CAD:</span>
        <span className="live-cad-value">{cadStatus}</span>
      </div>

      {/* Center: 3-Way Theme Switcher */}
      <div className="theme-switcher-pill" role="group" aria-label="HUD Theme Switcher">
        <button
          type="button"
          className={`theme-btn ${theme === 'clinical' ? 'active' : ''}`}
          onClick={() => onThemeChange('clinical')}
          title="Clinical Light Mode"
        >
          🏥 CLINICAL
        </button>
        <button
          type="button"
          className={`theme-btn ${theme === 'dark' ? 'active' : ''}`}
          onClick={() => onThemeChange('dark')}
          title="Tactical Dark HUD"
        >
          🌙 TACTICAL
        </button>
        <button
          type="button"
          className={`theme-btn ${theme === 'emergency' ? 'active' : ''}`}
          onClick={() => onThemeChange('emergency')}
          title="High-Contrast Red/Amber Emergency"
        >
          🚨 ALERT
        </button>
      </div>

      {/* Right: Telemetry / Latency */}
      <div className="telemetry-right">
        <span className="latency-label">LATITUDE:</span>
        <span className="latency-value">{latencyMs}</span>
      </div>
    </div>
  );
}
