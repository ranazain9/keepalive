/**
 * One AudioContext for the whole app.
 *
 * Safari on iOS allows only a handful of AudioContexts per page, and it counts
 * closed ones until they are collected. The cockpit was creating them in four
 * places — the metronome, the companion chime, the clip voice, and a fresh one
 * on every tap of the microphone — so after a few taps the limit was reached
 * and the next Web Audio call failed with InvalidStateError. On a phone that
 * looked like a dead mic button.
 *
 * Everything shares this one instead. It is created on the first user gesture
 * and lives for the session; nothing closes it.
 */

let shared = null;

export function getSharedAudioContext() {
  if (shared && shared.state !== 'closed') return shared;

  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return null;

  shared = new AudioCtx();

  // On iOS, setting audioSession.type overrides the hardware silent switch.
  // CRITICAL: We must use 'play-and-record' instead of 'playback'.
  // Setting 'playback' locks the session to output-only, causing WebKit to throw
  // InvalidStateError ("AudioSession category is not compatible with audio capture")
  // whenever getUserMedia is called. 'play-and-record' allows both mic input and audio output.
  try {
    if (typeof navigator !== 'undefined' && 'audioSession' in navigator && navigator.audioSession) {
      navigator.audioSession.type = 'play-and-record';
    }
  } catch (e) {}

  return shared;
}

/**
 * Resume without awaiting. iOS only honours resume() inside a user gesture, and
 * an `await` ends the gesture — so callers resume synchronously in the handler
 * and may await a second attempt afterwards.
 */
export function resumeSharedAudioContext() {
  const ctx = getSharedAudioContext();
  if (!ctx) return null;
  if (ctx.state === 'suspended') {
    try {
      ctx.resume();
    } catch (e) {}
  }
  return ctx;
}

/** The one-sample silent buffer iOS actually unlocks playback on. */
export function primeAudioContext() {
  const ctx = resumeSharedAudioContext();
  if (!ctx) return null;
  try {
    const source = ctx.createBufferSource();
    source.buffer = ctx.createBuffer(1, 1, 22050);
    source.connect(ctx.destination);
    source.start(0);
  } catch (e) {}
  return ctx;
}
