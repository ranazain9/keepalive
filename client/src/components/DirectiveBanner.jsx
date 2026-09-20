import React from 'react';
import { AlertTriangle, Activity } from 'lucide-react';

/**
 * DirectiveBanner
 * Giant, high-contrast clinical directive banner readable from 4-6 feet away.
 * Displays step status, agonal respiration intercept alerts, and AHA instructions.
 */
export function DirectiveBanner({ step = 1, directive = '', isAgonalAlert = false }) {
  const getStepBadge = () => {
    switch (step) {
      case 1:
        return { label: 'STEP 1: LAY PATIENT FLAT', color: '#38BDF8' };
      case 2:
        return { label: 'STEP 2: PLACE HANDS ON STERNUM', color: '#F59E0B' };
      case 3:
      default:
        return { label: 'STEP 3: 110 BPM CHEST COMPRESSIONS', color: '#EF4444' };
    }
  };

  const badge = getStepBadge();

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* Critical Agonal Breathing Callout Banner */}
      {isAgonalAlert && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            background: 'linear-gradient(90deg, rgba(239, 68, 68, 0.25) 0%, rgba(245, 158, 11, 0.2) 100%)',
            border: '2px solid #EF4444',
            borderRadius: '12px',
            padding: '12px 16px',
            animation: 'agonalAlert 1.2s infinite alternate',
          }}
        >
          <AlertTriangle size={24} color="#EF4444" />
          <div>
            <div style={{ fontSize: '12px', fontWeight: 800, color: '#FCA5A5', letterSpacing: '0.5px' }}>
              CRITICAL ALERT: AGONAL RESPIRATION DETECTED
            </div>
            <div style={{ fontSize: '11px', color: '#FEE2E2', marginTop: '2px', lineHeight: 1.4 }}>
              Gasping, snoring, or gurgling is brain-stem reflex, <strong>NOT normal breathing</strong>. DO NOT STOP CPR! KEEP PUSHING TO THE BEAT!
            </div>
          </div>
        </div>
      )}

      {/* Giant High-Contrast Directive Card */}
      <div
        className="hud-card"
        style={{
          padding: '18px 22px',
          borderLeft: `5px solid ${badge.color}`,
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 800,
              letterSpacing: '1px',
              padding: '3px 10px',
              borderRadius: '6px',
              background: `${badge.color}22`,
              color: badge.color,
              border: `1px solid ${badge.color}55`,
            }}
          >
            {badge.label}
          </span>
          <span style={{ fontSize: '11px', color: '#94A3B8', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Activity size={13} color="#10B981" />
            AHA 2025 BLS PROTOCOL
          </span>
        </div>

        <div
          style={{
            fontSize: '18px',
            fontWeight: 700,
            lineHeight: 1.4,
            color: '#F8FAFC',
            letterSpacing: '-0.3px',
          }}
        >
          {typeof directive === 'object' && directive !== null
            ? (directive.verbatim_text || directive.directive_text || JSON.stringify(directive))
            : String(directive || '')}
        </div>
      </div>
    </div>
  );
}
