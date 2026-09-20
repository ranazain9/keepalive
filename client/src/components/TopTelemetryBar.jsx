import React from 'react';

/**
 * TopTelemetryBar
 * Replicates the top header pill from the user design mockup:
 * - Left: "LIVE CAD: KEEPALIVE EN ROUTE (ETA 3M)" with pulsing red dot
 * - Right: "LATITUDE / LATENCY: 0.8MS"
 */
export function TopTelemetryBar({
  cadStatus = 'KEEPALIVE EN ROUTE (ETA 3M)',
  latencyMs = '0.8MS',
}) {
  return (
    <div className="top-telemetry-bar">
      {/* Left: LIVE CAD indicator */}
      <div className="telemetry-left">
        <span className="live-cad-dot"></span>
        <span className="live-cad-tag">LIVE CAD:</span>
        <span className="live-cad-value">{cadStatus}</span>
      </div>

      {/* Right: Telemetry / Latency */}
      <div className="telemetry-right">
        <span className="latency-label">LATITUDE:</span>
        <span className="latency-value">{latencyMs}</span>
      </div>
    </div>
  );
}
