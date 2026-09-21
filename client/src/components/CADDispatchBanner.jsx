import React, { useEffect } from 'react';
import { MapPin, ShieldAlert, Zap } from 'lucide-react';

/**
 * CADDispatchBanner
 * Displays the 911 CAD dispatch status, GPS location, and AED locator radar.
 */
export function CADDispatchBanner({ cadInfo = {}, onLocationResolved }) {
  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          try {
            const res = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`
            );
            const data = await res.json();
            if (data?.display_name) {
              const address = data.display_name.split(',').slice(0, 3).join(',').trim();
              if (onLocationResolved) onLocationResolved(address);
            }
          } catch (e) {
            if (onLocationResolved) onLocationResolved(`${lat.toFixed(4)}, ${lon.toFixed(4)}`);
          }
        },
        () => {
          if (onLocationResolved) onLocationResolved('201 Mission St, Financial District, SF');
        },
        { timeout: 6000 }
      );
    }
  }, [onLocationResolved]);

  return (
    <div
      className="hud-card"
      style={{
        width: '100%',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 18px',
        gap: '12px',
        fontSize: '12px',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        background: 'linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, rgba(56, 189, 248, 0.1) 100%)',
      }}
    >
      {/* CAD Dispatch Unit */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#10B981',
            boxShadow: '0 0 10px #10B981',
            animation: 'pulseBlink 1.4s infinite',
          }}
        />
        <ShieldAlert size={15} color="#10B981" />
        <span style={{ fontWeight: 800, color: '#10B981' }}>
          {cadInfo.status ? `SIMULATED CAD: ${cadInfo.status}` : 'SIMULATED 911 CAD STANDBY'}
        </span>
        <span style={{ color: '#94A3B8' }}>| {cadInfo.unit || 'Unit: Pending'}</span>
      </div>

      {/* GPS Location */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <MapPin size={14} color="#94A3B8" />
        <span style={{ color: '#94A3B8' }}>GPS:</span>
        <span style={{ fontWeight: 700, color: '#F8FAFC' }}>
          {cadInfo.address || 'Acquiring GPS...'}
        </span>
      </div>

      {/* AED Radar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Zap size={14} color="#38BDF8" />
        <span style={{ color: '#94A3B8' }}>AED Radar:</span>
        <span style={{ fontWeight: 700, color: '#38BDF8' }}>
          {cadInfo.aed || 'Lobby Box A (45m away)'}
        </span>
      </div>
    </div>
  );
}
