import { useState, useEffect, useRef } from 'react';

/**
 * Screen Wake Lock hook for mobile rescue sessions.
 * Keeps the screen awake during active emergency triage and CPR coaching,
 * preventing mobile devices from sleeping after 30 seconds of inactivity.
 * Automatically re-acquires the wake lock on visibility changes.
 */
export function useWakeLock(isActive = false) {
  const [isLocked, setIsLocked] = useState(false);
  const wakeLockRef = useRef(null);

  const requestLock = async () => {
    if (typeof window === 'undefined' || !('wakeLock' in navigator)) {
      return false;
    }
    try {
      if (!wakeLockRef.current) {
        wakeLockRef.current = await navigator.wakeLock.request('screen');
        setIsLocked(true);
        wakeLockRef.current.addEventListener('release', () => {
          setIsLocked(false);
          wakeLockRef.current = null;
        });
      }
      return true;
    } catch (err) {
      console.warn('[WakeLock] Unable to acquire screen wake lock:', err.message);
      setIsLocked(false);
      return false;
    }
  };

  const releaseLock = async () => {
    if (wakeLockRef.current) {
      try {
        await wakeLockRef.current.release();
      } catch (err) {
        console.warn('[WakeLock] Error releasing screen wake lock:', err.message);
      } finally {
        wakeLockRef.current = null;
        setIsLocked(false);
      }
    }
  };

  useEffect(() => {
    if (isActive) {
      requestLock();
    } else {
      releaseLock();
    }

    // Re-acquire lock if tab becomes visible again while emergency is active
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && isActive) {
        requestLock();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      releaseLock();
    };
  }, [isActive]);

  return { isLocked, requestLock, releaseLock };
}
