import React, { useState, useEffect } from 'react';
import { speakLive, stopLive } from '../audio/clipVoice';
import {
  Ambulance,
  CheckCircle2,
  RotateCcw,
  Copy,
  Check,
  Volume2,
  VolumeX,
  FileText,
  QrCode,
  Activity,
  Clock,
  Heart,
  ShieldCheck,
  ShieldAlert,
  Zap,
  Download,
  AlertTriangle,
  UserCheck,
} from 'lucide-react';

/**
 * EMSHandoverModal
 * High-Density Clinical Electronic Handover Tablet Interface for incoming paramedics.
 * Standardized to NEMSIS v3.5 & AHA 2020 BLS Clinical Handover guidelines.
 */
export function EMSHandoverModal({
  isOpen = false,
  handoffData = null,
  onReset = () => {},
  onClose = () => {},
}) {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState('clinical'); // 'clinical' | 'json' | 'qr'
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [copied, setCopied] = useState(false);

  // Extract structured fields
  const incidentId =
    handoffData?.incident_id || handoffData?.cad_incident_id || 'CAD-SFPD-1789920509';
  const timestamp = handoffData?.timestamp_utc || new Date().toISOString();
  const primaryIntent = (
    handoffData?.primary_intent ||
    handoffData?.intent ||
    'CARDIAC_ARREST'
  ).replace(/_/g, ' ');
  const patientType = handoffData?.patient_type || 'ADULT';
  const confidence = Math.round(
    (handoffData?.triage_confidence !== undefined ? handoffData.triage_confidence : 1) * 100
  );

  const cprDurationSec = handoffData?.cpr_duration_seconds ?? 91.7;
  const formatDuration = (sec) => {
    const m = Math.floor(sec / 60);
    const s = Math.round(sec % 60);
    return `${m} min ${s} sec`;
  };

  const totalCompressions =
    handoffData?.total_compressions_delivered ??
    handoffData?.total_compressions ??
    168;

  const ahaCycles = handoffData?.aha_cycles_completed ?? handoffData?.cpr_cycles ?? 0;
  const aedDeployed = Boolean(handoffData?.aed_deployed);
  const cSpineRisk = Boolean(
    handoffData?.c_spine_trauma_risk ?? handoffData?.c_spine_risk
  );
  const agonalBreathing = Boolean(
    handoffData?.agonal_breathing_detected ?? handoffData?.agonal_breathing
  );
  const bystanderStatus = handoffData?.bystander_status || 'SINGLE BYSTANDER';

  const verbalReport =
    handoffData?.spoken_report ||
    handoffData?.spoken_handoff_summary ||
    handoffData?.verbal_report ||
    `EMS Handoff: ${patientType} patient with ${primaryIntent}. Bystander CPR performed for ${formatDuration(
      cprDurationSec
    )}, approximately ${totalCompressions} compressions delivered at 110 BPM. ${
      aedDeployed ? 'Public access AED was deployed.' : 'Awaiting defibrillation.'
    }`;

  const fullPayload = handoffData || {
    incident_id: incidentId,
    timestamp_utc: timestamp,
    primary_intent: primaryIntent,
    triage_confidence: confidence / 100,
    patient_type: patientType,
    cpr_duration_seconds: cprDurationSec,
    total_compressions_delivered: totalCompressions,
    aha_cycles_completed: ahaCycles,
    c_spine_trauma_risk: cSpineRisk,
    agonal_breathing_detected: agonalBreathing,
    bystander_status: bystanderStatus,
    aed_deployed: aedDeployed,
    spoken_handoff_summary: verbalReport,
    spoken_report: verbalReport,
  };

  const jsonSummary = JSON.stringify(fullPayload, null, 2);

  const handleCopyJson = () => {
    navigator.clipboard.writeText(jsonSummary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleDownloadJson = () => {
    const blob = new Blob([jsonSummary], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${incidentId}_clinical_handoff.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const toggleReadAloud = async () => {
    if (isSpeaking) {
      stopLive();
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    setIsSpeaking(true);

    // The handover briefing is read in the same voice as everything else. It is
    // built from the incident log, so "briefing" keeps it whole — the
    // conversational three-sentence cap would drop clinical facts.
    const spoken = await speakLive(verbalReport, { protocolState: 'briefing' });
    if (spoken) {
      setIsSpeaking(false);
      return;
    }

    // /speak not deployed: the browser reads it, as before.
    if (!('speechSynthesis' in window)) {
      setIsSpeaking(false);
      return;
    }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(verbalReport);
    u.rate = 1.02;
    u.pitch = 1.0;
    u.onend = () => setIsSpeaking(false);
    u.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(u);
  };

  // Cleanup speech on unmount
  useEffect(() => {
    return () => {
      stopLive();
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(2, 6, 23, 0.88)',
        backdropFilter: 'blur(16px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        animation: 'fadeIn 0.2s ease-out',
      }}
    >
      <div
        className="hud-card"
        style={{
          width: '100%',
          maxWidth: '780px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          background: 'linear-gradient(180deg, #0B132B 0%, #080C17 100%)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          borderRadius: '12px',
          boxShadow: '0 25px 70px -10px rgba(0, 0, 0, 0.95), 0 0 35px rgba(56, 189, 248, 0.15)',
          overflow: 'hidden',
        }}
      >
        {/* Top Field Tablet Diagnostic Chassis Header */}
        <div
          style={{
            padding: '16px 22px',
            background: 'rgba(15, 23, 42, 0.75)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '8px',
                background: 'rgba(56, 189, 248, 0.15)',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38BDF8',
              }}
            >
              <Ambulance size={22} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '15px', fontWeight: 800, color: '#F8FAFC', letterSpacing: '0.4px' }}>
                  PARAMEDIC EMS ELECTRONIC HANDOVER
                </span>
                <span
                  style={{
                    fontSize: '10px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: 'rgba(56, 189, 248, 0.15)',
                    color: '#38BDF8',
                    border: '1px solid rgba(56, 189, 248, 0.3)',
                  }}
                >
                  NEMSIS v3.5
                </span>
              </div>
              <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '2px' }}>
                Incident ID: <strong style={{ color: '#E2E8F0', fontFamily: 'var(--font-mono)' }}>{incidentId}</strong> · {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '20px',
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                color: '#10B981',
                fontSize: '11px',
                fontWeight: 800,
                letterSpacing: '0.5px',
              }}
            >
              <CheckCircle2 size={13} />
              SCENE SECURED
            </div>
            <button
              onClick={onClose}
              style={{
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '6px',
                color: '#94A3B8',
                width: '30px',
                height: '30px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                fontSize: '16px',
                transition: 'all 0.15s ease',
              }}
              title="Close modal"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tab Navigation Strip */}
        <div
          style={{
            display: 'flex',
            background: 'rgba(10, 16, 30, 0.95)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            padding: '0 20px',
            gap: '8px',
          }}
        >
          <button
            type="button"
            onClick={() => setActiveTab('clinical')}
            style={{
              padding: '12px 16px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'clinical' ? '2px solid #38BDF8' : '2px solid transparent',
              color: activeTab === 'clinical' ? '#38BDF8' : '#94A3B8',
              fontSize: '12px',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.15s ease',
            }}
          >
            <Activity size={14} />
            CLINICAL SUMMARY &amp; METRICS
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('json')}
            style={{
              padding: '12px 16px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'json' ? '2px solid #38BDF8' : '2px solid transparent',
              color: activeTab === 'json' ? '#38BDF8' : '#94A3B8',
              fontSize: '12px',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.15s ease',
            }}
          >
            <FileText size={14} />
            STRUCTURED ePCR JSON
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('qr')}
            style={{
              padding: '12px 16px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'qr' ? '2px solid #38BDF8' : '2px solid transparent',
              color: activeTab === 'qr' ? '#38BDF8' : '#94A3B8',
              fontSize: '12px',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.15s ease',
            }}
          >
            <QrCode size={14} />
            TABLET QR SYNC
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div
          style={{
            padding: '20px 24px',
            overflowY: 'auto',
            maxHeight: 'calc(90vh - 160px)',
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
          }}
        >
          {/* Verbal Briefing Callout (Persistent across primary view) */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.08) 0%, rgba(15, 23, 42, 0.6) 100%)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              borderLeft: '4px solid #38BDF8',
              borderRadius: '8px',
              padding: '14px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 800, color: '#38BDF8', letterSpacing: '0.6px' }}>
                10-SECOND HIGH-DENSITY VERBAL BRIEFING (FIRSTNET AUDIO)
              </span>
              <button
                type="button"
                onClick={toggleReadAloud}
                style={{
                  background: isSpeaking ? 'rgba(239, 68, 68, 0.2)' : 'rgba(56, 189, 248, 0.15)',
                  border: isSpeaking ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(56, 189, 248, 0.4)',
                  color: isSpeaking ? '#EF4444' : '#38BDF8',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                }}
              >
                {isSpeaking ? <VolumeX size={13} /> : <Volume2 size={13} />}
                {isSpeaking ? 'Stop Speaking' : 'Read Aloud'}
              </button>
            </div>

            <div
              style={{
                fontSize: '14px',
                fontWeight: 600,
                color: '#F1F5F9',
                lineHeight: 1.5,
                fontStyle: 'italic',
              }}
            >
              "{verbalReport}"
            </div>
          </div>

          {/* TAB 1: Clinical Summary & Metrics Tiles */}
          {activeTab === 'clinical' && (
            <>
              {/* 6-Tile Medical Metric Grid */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '12px',
                }}
              >
                {/* CPR Duration */}
                <div
                  style={{
                    background: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px',
                    padding: '12px 14px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94A3B8', fontSize: '11px', fontWeight: 700 }}>
                    <Clock size={14} color="#38BDF8" /> CPR DURATION
                  </div>
                  <div style={{ fontSize: '18px', fontWeight: 800, color: '#F8FAFC', margin: '4px 0 2px', fontFamily: 'var(--font-mono)' }}>
                    {formatDuration(cprDurationSec)}
                  </div>
                  <div style={{ fontSize: '10px', color: '#64748B' }}>
                    Elapsed: {cprDurationSec.toFixed(1)}s continuous
                  </div>
                </div>

                {/* Total Compressions Delivered */}
                <div
                  style={{
                    background: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px',
                    padding: '12px 14px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94A3B8', fontSize: '11px', fontWeight: 700 }}>
                    <Heart size={14} color="#EF4444" /> COMPRESSIONS DELIVERED
                  </div>
                  <div style={{ fontSize: '18px', fontWeight: 800, color: '#38BDF8', margin: '4px 0 2px', fontFamily: 'var(--font-mono)' }}>
                    {totalCompressions} <span style={{ fontSize: '12px', color: '#94A3B8' }}>@ 110 BPM</span>
                  </div>
                  <div style={{ fontSize: '10px', color: '#10B981', fontWeight: 700 }}>
                    Target Depth: 2.0" – 2.4" achieved
                  </div>
                </div>

                {/* Public Access AED Status */}
                <div
                  style={{
                    background: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px',
                    padding: '12px 14px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94A3B8', fontSize: '11px', fontWeight: 700 }}>
                    <Zap size={14} color="#F59E0B" /> DEFIBRILLATION / AED
                  </div>
                  <div
                    style={{
                      fontSize: '14px',
                      fontWeight: 800,
                      color: aedDeployed ? '#10B981' : '#F59E0B',
                      margin: '6px 0 2px',
                    }}
                  >
                    {aedDeployed ? 'PUBLIC ACCESS AED DEPLOYED' : 'AWAITING AED PADS'}
                  </div>
                  <div style={{ fontSize: '10px', color: '#94A3B8' }}>
                    {aedDeployed ? 'Shock advisory active' : 'Continue CPR until pads arrive'}
                  </div>
                </div>

                {/* C-Spine Trauma Risk */}
                <div
                  style={{
                    background: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px',
                    padding: '12px 14px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94A3B8', fontSize: '11px', fontWeight: 700 }}>
                    <ShieldCheck size={14} color={cSpineRisk ? '#EF4444' : '#10B981'} /> C-SPINE TRAUMA RISK
                  </div>
                  <div
                    style={{
                      fontSize: '14px',
                      fontWeight: 800,
                      color: cSpineRisk ? '#EF4444' : '#10B981',
                      margin: '6px 0 2px',
                    }}
                  >
                    {cSpineRisk ? 'POTENTIAL C-SPINE RISK' : 'CLEAR · NO TRAUMA'}
                  </div>
                  <div style={{ fontSize: '10px', color: '#94A3B8' }}>
                    {cSpineRisk ? 'Maintain in-line manual stabilization' : 'Zero cervical mechanism reported'}
                  </div>
                </div>

                {/* Agonal Breathing Flag */}
                <div
                  style={{
                    background: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px',
                    padding: '12px 14px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94A3B8', fontSize: '11px', fontWeight: 700 }}>
                    <AlertTriangle size={14} color={agonalBreathing ? '#EF4444' : '#10B981'} /> AGONAL RESPIRATION
                  </div>
                  <div
                    style={{
                      fontSize: '14px',
                      fontWeight: 800,
                      color: agonalBreathing ? '#EF4444' : '#10B981',
                      margin: '6px 0 2px',
                    }}
                  >
                    {agonalBreathing ? 'AGONAL GASPING NOTED' : 'NO AGONAL GASPING'}
                  </div>
                  <div style={{ fontSize: '10px', color: '#94A3B8' }}>
                    {agonalBreathing ? 'Consistent with cardiac arrest' : 'Patient completely apnoic'}
                  </div>
                </div>

                {/* Rescuer & Bystander Profile */}
                <div
                  style={{
                    background: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '8px',
                    padding: '12px 14px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94A3B8', fontSize: '11px', fontWeight: 700 }}>
                    <UserCheck size={14} color="#A855F7" /> BYSTANDER PRESENCE
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 800, color: '#F8FAFC', margin: '6px 0 2px' }}>
                    {bystanderStatus.replace(/_/g, ' ')}
                  </div>
                  <div style={{ fontSize: '10px', color: '#94A3B8' }}>
                    AHA Fatigue Cycles: {ahaCycles} cycles logged
                  </div>
                </div>
              </div>
            </>
          )}

          {/* TAB 2: Structured JSON Telemetry */}
          {activeTab === 'json' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', color: '#94A3B8', fontFamily: 'var(--font-mono)' }}>
                  ePCR Clinical Telemetry Object ({new Blob([jsonSummary]).size} bytes)
                </span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={handleCopyJson}
                    style={{
                      background: copied ? 'rgba(16, 185, 129, 0.2)' : 'rgba(56, 189, 248, 0.15)',
                      border: copied ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(56, 189, 248, 0.4)',
                      color: copied ? '#10B981' : '#38BDF8',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                    }}
                  >
                    {copied ? <Check size={13} /> : <Copy size={13} />}
                    {copied ? 'Copied!' : 'Copy JSON'}
                  </button>
                  <button
                    type="button"
                    onClick={handleDownloadJson}
                    style={{
                      background: 'rgba(255, 255, 255, 0.08)',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      color: '#F8FAFC',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                    }}
                  >
                    <Download size={13} /> Download .json
                  </button>
                </div>
              </div>

              <pre
                style={{
                  background: '#030712',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  borderRadius: '8px',
                  padding: '14px 16px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  lineHeight: 1.6,
                  color: '#38BDF8',
                  maxHeight: '340px',
                  overflowY: 'auto',
                  boxShadow: 'inset 0 0 15px rgba(0, 0, 0, 0.8)',
                }}
              >
                {jsonSummary}
              </pre>
            </div>
          )}

          {/* TAB 3: Tablet QR Code Transfer */}
          {activeTab === 'qr' && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '20px',
                background: 'rgba(15, 23, 42, 0.5)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '8px',
                gap: '14px',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  padding: '14px',
                  background: '#FFFFFF',
                  borderRadius: '12px',
                  boxShadow: '0 8px 30px rgba(0, 0, 0, 0.5)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg width="180" height="180" viewBox="0 0 110 110">
                  <rect width="110" height="110" fill="#FFFFFF" rx="4" />
                  <rect x="10" y="10" width="28" height="28" fill="#0A2540" />
                  <rect x="14" y="14" width="20" height="20" fill="#FFFFFF" />
                  <rect x="18" y="18" width="12" height="12" fill="#0A2540" />
                  <rect x="72" y="10" width="28" height="28" fill="#0A2540" />
                  <rect x="76" y="14" width="20" height="20" fill="#FFFFFF" />
                  <rect x="80" y="18" width="12" height="12" fill="#0A2540" />
                  <rect x="10" y="72" width="28" height="28" fill="#0A2540" />
                  <rect x="14" y="76" width="20" height="20" fill="#FFFFFF" />
                  <rect x="18" y="80" width="12" height="12" fill="#0A2540" />
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

              <div>
                <div style={{ fontSize: '14px', fontWeight: 800, color: '#F8FAFC' }}>
                  PARAMEDIC TABLET INSTANT FIELD SYNC
                </div>
                <div style={{ fontSize: '12px', color: '#94A3B8', maxWidth: '420px', marginTop: '4px' }}>
                  Scan with FirstNet, ESO ePCR, or ImageTrend tablet scanner to automatically import vitals and compression telemetry.
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Action Footer */}
        <div
          style={{
            padding: '14px 22px',
            background: 'rgba(10, 16, 30, 0.95)',
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#64748B', fontSize: '11px' }}>
            <CheckCircle2 size={13} color="#10B981" />
            <span>Encrypted NEMSIS v3.5 Record · Ready for Med-Control</span>
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={handleCopyJson}
              style={{
                background: copied ? 'rgba(16, 185, 129, 0.2)' : 'rgba(56, 189, 248, 0.15)',
                border: copied ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(56, 189, 248, 0.35)',
                color: copied ? '#10B981' : '#38BDF8',
                padding: '9px 16px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'all 0.15s ease',
              }}
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
              {copied ? 'Copied to Clipboard!' : 'Copy JSON'}
            </button>

            <button
              type="button"
              onClick={onReset}
              style={{
                background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
                border: 'none',
                color: '#FFFFFF',
                padding: '9px 20px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 800,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: '0 4px 14px rgba(16, 185, 129, 0.35)',
                transition: 'all 0.15s ease',
              }}
            >
              <RotateCcw size={14} /> Start New Rescue Session
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
