import React from 'react';

/**
 * Stage 3: EMS Handover & Scanner Section
 * Faithful to user design mockup:
 * - Red Cross + ECG heartline banner
 * - Medical CAD SBAR report fields
 * - High-contrast "SCAN FOR EMS TABLET" QR Code
 */
export function EMSHandoverCard({ handoffData = null, compressions = 128, cycles = 1, onOpenModal = () => {} }) {
  const incidentId = handoffData?.cad_incident_id || 'SF-8453';
  const notes = handoffData?.notes || 'PATIENT UNRESPONSIVE. PARAMEDICS IN PROGRESS.';
  const swaps = handoffData?.fatigue_swaps !== undefined ? handoffData.fatigue_swaps : cycles;

  return (
    <div className="stage-card stage-3-container" onClick={onOpenModal} style={{ cursor: 'pointer' }} title="Click to open Paramedic EMS Electronic Handover Tablet">
      {/* Top Red Cross & Red ECG Heartbeat Strip */}
      <div className="stage-3-header-strip">
        <div className="medical-cross-badge">
          <span>+</span>
        </div>
        <div className="ecg-strip">
          <svg viewBox="0 0 500 40" preserveAspectRatio="none" className="ecg-svg">
            <path
              d="M0,20 L120,20 L130,5 L140,35 L150,15 L160,25 L170,20 L300,20 L310,5 L320,35 L330,15 L340,25 L350,20 L500,20"
              fill="none"
              stroke="#EF4444"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>

      {/* Main Split Content: SBAR CAD Table on Left, QR Code on Right */}
      <div className="stage-3-grid">
        {/* Left Column: SBAR CAD Medical Report */}
        <div className="sbar-report-column">
          <div className="cad-device-icon">
            <svg width="40" height="70" viewBox="0 0 40 70" fill="none">
              <rect x="2" y="2" width="36" height="66" rx="6" stroke="#00A8E8" strokeWidth="2.5" fill="#EBF8FE" />
              <rect x="6" y="8" width="28" height="38" rx="2" fill="#BAE6FD" />
              <circle cx="20" cy="56" r="4" fill="#00A8E8" />
              <path d="M12 20 L17 20 L20 14 L23 26 L26 20 L28 20" stroke="#0284C7" strokeWidth="2" fill="none" />
            </svg>
          </div>

          <div className="sbar-details-table">
            <div className="sbar-row">
              <span className="sbar-label">CPR:</span>
              <span className="sbar-value">110 BPM ACTIVE | AHA-BLS PROTOCOL</span>
            </div>
            <div className="sbar-row">
              <span className="sbar-label">TONE:</span>
              <span className="sbar-value">NORMAL SINUS RHYTHM (AED MONITORED)</span>
            </div>
            <div className="sbar-row">
              <span className="sbar-label">FATIGUE SWAPS:</span>
              <span className="sbar-value">{swaps}</span>
            </div>
            <div className="sbar-row">
              <span className="sbar-label">NOTES:</span>
              <span className="sbar-value">{notes}</span>
            </div>
          </div>
        </div>

        {/* Right Column: Scan for EMS Tablet QR Code */}
        <div className="qr-column">
          <div className="qr-title">SCAN FOR EMS TABLET</div>
          <div className="qr-wrapper">
            <svg width="110" height="110" viewBox="0 0 110 110" className="qr-svg">
              {/* Outer border & background */}
              <rect width="110" height="110" fill="#FFFFFF" rx="4" />
              {/* Corner Position Detection Patterns */}
              {/* Top-Left */}
              <rect x="10" y="10" width="28" height="28" fill="#0A2540" />
              <rect x="14" y="14" width="20" height="20" fill="#FFFFFF" />
              <rect x="18" y="18" width="12" height="12" fill="#0A2540" />
              {/* Top-Right */}
              <rect x="72" y="10" width="28" height="28" fill="#0A2540" />
              <rect x="76" y="14" width="20" height="20" fill="#FFFFFF" />
              <rect x="80" y="18" width="12" height="12" fill="#0A2540" />
              {/* Bottom-Left */}
              <rect x="10" y="72" width="28" height="28" fill="#0A2540" />
              <rect x="14" y="76" width="20" height="20" fill="#FFFFFF" />
              <rect x="18" y="80" width="12" height="12" fill="#0A2540" />
              {/* Data modules */}
              <rect x="44" y="12" width="6" height="6" fill="#0A2540" />
              <rect x="56" y="12" width="6" height="6" fill="#0A2540" />
              <rect x="48" y="24" width="6" height="6" fill="#0A2540" />
              <rect x="56" y="30" width="6" height="6" fill="#0A2540" />
              <rect x="12" y="46" width="6" height="6" fill="#0A2540" />
              <rect x="24" y="52" width="6" height="6" fill="#0A2540" />
              <rect x="36" y="44" width="6" height="6" fill="#0A2540" />
              <rect x="44" y="50" width="18" height="6" fill="#0A2540" />
              <rect x="68" y="46" width="6" height="6" fill="#0A2540" />
              <rect x="80" y="52" width="14" height="6" fill="#0A2540" />
              <rect x="44" y="66" width="6" height="14" fill="#0A2540" />
              <rect x="58" y="66" width="12" height="6" fill="#0A2540" />
              <rect x="76" y="72" width="6" height="18" fill="#0A2540" />
              <rect x="88" y="82" width="10" height="8" fill="#0A2540" />
              <rect x="54" y="84" width="12" height="14" fill="#0A2540" />
            </svg>
          </div>
          <div className="qr-subtitle">
            Present this to EMS<br />for instant data handoff.
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onOpenModal();
            }}
            style={{
              marginTop: '6px',
              background: '#0284C7',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '4px',
              padding: '4px 10px',
              fontSize: '10px',
              fontWeight: 800,
              letterSpacing: '0.4px',
              cursor: 'pointer',
              boxShadow: '0 2px 6px rgba(2, 132, 199, 0.3)',
            }}
          >
            📋 VIEW FULL REPORT
          </button>
        </div>
      </div>
    </div>
  );
}
