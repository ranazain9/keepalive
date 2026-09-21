/**
 * Pre-recorded human voice for every line the engine speaks.
 *
 * The backend already names each line: a directive carries `asset_id`
 * (e.g. "cpr_adult_step1_call911") and the companion's scripted answers are
 * keyed by their FAQ id. Those names are the clip file names, so playing a line
 * is a lookup, not a synthesis.
 *
 * Nothing here calls an external service. The clips are static files in
 * client/public/audio, rendered once from protocols.py and micro_qa_engine.py,
 * so they cannot rate-limit, expire or fail while a judge is testing.
 *
 * If a line has no clip — a live Groq answer nobody scripted — play() returns
 * false and the caller falls back to speech synthesis, exactly as before.
 */

const MANIFEST_URL = '/audio/manifest.json';

let manifest = null;
let loading = null;
const buffers = new Map();
let ctx = null;
let master = null;

/** Words only, so punctuation and casing don't decide whether a clip matches. */
function normalise(text) {
  return (text || '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(Boolean)
    .join(' ');
}

let byText = new Map();

export async function loadClipVoice(audioContext) {
  if (audioContext && !ctx) {
    ctx = audioContext;
    master = ctx.createGain();
    master.connect(ctx.destination);
  }
  if (manifest) return manifest;
  if (loading) return loading;

  loading = fetch(MANIFEST_URL)
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`manifest ${r.status}`))))
    .then((m) => {
      manifest = m;
      byText = new Map();
      for (const [id, clip] of Object.entries(m.clips || {})) {
        byText.set(normalise(clip.text), id);
      }
      return m;
    })
    .catch((e) => {
      // No clips deployed: the caller keeps using speech synthesis.
      console.warn('[clipVoice] no manifest, falling back to speech synthesis:', e.message);
      manifest = { clips: {} };
      return manifest;
    });

  return loading;
}

/** The id for a line, by the backend's own asset id or by its exact words. */
export function resolveClipId(assetId, text) {
  if (!manifest) return null;
  if (assetId && manifest.clips[assetId]) return assetId;
  const hit = byText.get(normalise(text));
  return hit || null;
}

async function buffer(id) {
  if (buffers.has(id)) return buffers.get(id);
  const clip = manifest.clips[id];
  const bytes = await fetch(`/audio/${clip.file}`).then((r) => r.arrayBuffer());
  const decoded = await ctx.decodeAudioData(bytes);
  buffers.set(id, decoded);
  return decoded;
}

/**
 * Speak a line with the recorded voice.
 * Resolves true when the clip finished, false immediately if there is no clip
 * (or no audio context yet) so the caller can fall back.
 */
export async function playClip({ assetId, text, onStart, onEnd } = {}) {
  await loadClipVoice();
  if (!ctx) return false;

  const id = resolveClipId(assetId, text);
  if (!id) return false;

  let decoded;
  try {
    decoded = await buffer(id);
  } catch (e) {
    console.warn(`[clipVoice] ${id} failed to load:`, e.message);
    return false;
  }

  if (ctx.state === 'suspended') {
    try {
      await ctx.resume();
    } catch (e) {
      return false;
    }
  }

  return new Promise((resolve) => {
    const source = ctx.createBufferSource();
    source.buffer = decoded;
    source.connect(master);
    source.onended = () => {
      if (onEnd) onEnd(id);
      resolve(true);
    };
    if (onStart) onStart(id, manifest.clips[id]);
    source.start();
  });
}

/** Warm the lines the demo opens with, so the first one is instant. */
export function preloadClips(ids) {
  if (!ctx || !manifest) return;
  ids.filter((id) => manifest.clips[id]).forEach((id) => buffer(id).catch(() => {}));
}

export function hasClips() {
  return !!manifest && Object.keys(manifest.clips).length > 0;
}

// Fetch the manifest as soon as the app loads. It needs no AudioContext, and it
// has to be ready before the first directive arrives — a protocol line lands
// within a second of the page being used.
loadClipVoice();
