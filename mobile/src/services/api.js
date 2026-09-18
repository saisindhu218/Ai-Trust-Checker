// Change this to your laptop's LAN IP when testing on a physical phone via
// Expo Go (localhost won't work from a real device). If you're using the
// web preview or an Android emulator on the SAME machine, localhost is fine
// (the emulator alias 10.0.2.2 is handled by Expo automatically for you
// only in bare React Native, so on Expo Go just use your LAN IP).
//
// Find your IP with: ipconfig  (look for "IPv4 Address" under Wi-Fi)
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://192.168.0.109:8000";
const API_ACCESS_TOKEN = process.env.EXPO_PUBLIC_API_ACCESS_TOKEN || "";

const REQUEST_TIMEOUT_MS = 20000;

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const headers = {
      ...(options.headers || {}),
      ...(API_ACCESS_TOKEN ? { "X-API-Key": API_ACCESS_TOKEN } : {}),
    };
    return await fetch(url, { ...options, headers, signal: controller.signal });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The server took too long to respond. Check that the backend is running and reachable from this device.");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function analyzeText(text) {
  const res = await fetchWithTimeout(`${API_BASE_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(`Server error: ${res.status}`);
  }
  return res.json();
}

export async function fetchHistory() {
  const res = await fetchWithTimeout(`${API_BASE_URL}/history`);
  if (!res.ok) {
    throw new Error(`Server error: ${res.status}`);
  }
  return res.json();
}
