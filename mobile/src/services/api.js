// Change this to your laptop's LAN IP when testing on a physical phone via
// Expo Go (localhost won't work from a real device). Find it with:
// ipconfig  (look for "IPv4 Address" under Wi-Fi)
export const API_BASE_URL = "http://192.168.1.100:8000";

const REQUEST_TIMEOUT_MS = 20000;

async function fetchWithTimeout(url, options) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return res;
  } catch (err) {
    if (err.name === "AbortError") {
      // A silent hang almost always means the phone can't reach the server —
      // most commonly Windows Firewall blocking inbound connections to
      // uvicorn, the phone being on a different Wi-Fi network, or a stale IP
      // in API_BASE_URL above.
      throw new Error(
        `No response after ${REQUEST_TIMEOUT_MS / 1000}s. Check that: (1) the backend is running, ` +
          `(2) API_BASE_URL matches your laptop's current IP, (3) Windows Firewall allows inbound ` +
          `connections on port 8000, and (4) your phone is on the same Wi-Fi as your laptop.`
      );
    }
    throw err;
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
