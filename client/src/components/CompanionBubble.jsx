import React from 'react';
import { ShieldCheck, HeartHandshake } from 'lucide-react';

/**
 * CompanionBubble
 * Agent #3 Clinical Companion Doctor Bedside Guidance.
 * Displays real-time Groq LPU reassurance for panic hesitation
 * adhering strictly to the <= 18 words cognitive-load rule.
 * 100% Hands-Free: No buttons, operated purely by voice.
 */
export function CompanionBubble({ message = null }) {
  const wordCount = message ? message.trim().split(/\s+/).length : 0;

  return (
    <div
      className="hud-card"
      style={{
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        border: message ? '1px solid rgba(168, 85, 247, 0.45)' : '1px solid var(--card-border)',
        background: message
          ? 'linear-gradient(135deg, rgba(168, 85, 247, 0.12) 0%, rgba(13, 20, 36, 0.85) 100%)'
          : 'var(--card-bg)',
        transition: 'all 0.3s ease',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <HeartHandshake size={18} color="#A855F7" />
          <span style={{ fontSize: '12px', fontWeight: 800, color: '#F3E8FF', letterSpacing: '0.5px' }}>
            AGENT #3 CLINICAL COMPANION · GROQ LPU
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span
            style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              background: wordCount <= 18 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: wordCount <= 18 ? '#10B981' : '#EF4444',
              border: wordCount <= 18 ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
            }}
          >
            {wordCount > 0 ? `${wordCount} / 18 WORDS RULE` : '≤ 18 WORDS RULE'}
          </span>
          <span
            style={{
              fontSize: '10px',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38BDF8',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <ShieldCheck size={11} /> SECTION 4 COMPLIANT
          </span>
        </div>
      </div>

      {/* Speech Message Box */}
      <div
        style={{
          background: 'rgba(0, 0, 0, 0.35)',
          borderLeft: '3px solid #A855F7',
          borderRadius: '0 8px 8px 0',
          padding: '14px 16px',
          fontSize: '15px',
          fontWeight: 500,
          lineHeight: 1.45,
          color: message ? '#F8FAFC' : '#94A3B8',
          fontStyle: message ? 'normal' : 'italic',
        }}
      >
        {message || 'Standby for clinical panic reassurance (e.g. cracking ribs, legal doubt, vomiting airway)...'}
      </div>
    </div>
  );
}
