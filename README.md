# AI Trust Checker — v1 (MVP)

Text-only scam/phishing checker. Paste a suspicious message, get a risk
score, category, red flags, and recommended action — backed by a
rule-based pattern engine plus optional Gemini free-tier reasoning.

**What's in v1:** text input only. Screenshot/OCR, URL analysis, and
full misinformation fact-checking were deliberately left out of this
first version — they're each a substantial subsystem on their own, and
scam-pattern detection on text is the highest-value, most tractable
piece to get right first. See "What's next" at the bottom.

This is built to run entirely on **your existing tools** — nothing new
to install beyond Python packages and (for the mobile app) `npm install`
inside this project folder. It does **not** touch your global
Node/Expo/Java/Android SDK setup, and it never launches Android Studio
or a Gradle build — the mobile app runs through **Expo Go** on your
phone, which just needs your existing Node + Expo CLI.

Everything here is free-tier: Gemini's free API tier, SQLite (a local
file, no database server), and Expo Go (free app on your phone). No
paid services required.

---

## 1. One-time setup

### 1a. Get a free Gemini API key
Go to https://aistudio.google.com/app/apikey, sign in, and create a key.
This is free with rate limits — no card required for the free tier.

### 1b. Backend (Python / FastAPI)

Open PowerShell in this project folder:

```powershell
cd "E:\AI Trust Checker\backend"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Now open `.env` in a text editor and paste your Gemini key:
```
GEMINI_API_KEY=your_key_here
```

Run the backend:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Leave this window open. Visit http://localhost:8000/health in a browser
— you should see `{"status":"ok"}`.

> Uses your existing **Python 3.11.8** — no version change needed.

### 1c. Find your laptop's LAN IP (needed for the phone app)

In a **new** PowerShell window:
```powershell
ipconfig
```
Look under "Wireless LAN adapter Wi-Fi" for `IPv4 Address`, e.g. `192.168.1.42`.

Open `mobile/src/services/api.js` and change this line to your actual IP:
```js
export const API_BASE_URL = "http://192.168.1.42:8000";
```

Your phone and laptop must be on the **same Wi-Fi network**.

### 1d. Mobile app (Expo)

New PowerShell window:
```powershell
cd "E:\AI Trust Checker\mobile"
npm install
npx expo start
```

A QR code appears in the terminal. Install **Expo Go** from the Play
Store on your phone, open it, and scan the QR code. The app loads
directly — no APK build, no Android Studio, no emulator.

> Uses your existing **Node v22.17.0 / npx expo (v57 CLI)** — this
> project's own `package.json` pins Expo `~54.0.0` to match what's
> already cached on your machine from `indiaassist-ai`, so `npm install`
> shouldn't need to download a different major version.

### 1e. (Optional) Web version — Streamlit

New PowerShell window:
```powershell
cd "E:\AI Trust Checker\web"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GEMINI_API_KEY="your_key_here"
streamlit run streamlit_app.py
```
Opens automatically at http://localhost:8501. This version talks to the
rule engine and Gemini **directly** — it does not need the FastAPI
backend (1b) running at all. Good for quick testing without your phone.

---

## 2. Testing it

Try pasting these into either the mobile app or the Streamlit page:

- `Your SBI account will be blocked today. Click this link immediately to verify.` → should score HIGH, category Phishing
- `Congratulations! You have won a lucky draw prize. Pay a small processing fee to claim.` → HIGH, Lottery/Prize Scam
- `Hey are we still meeting for lunch tomorrow at 1pm?` → LOW, no flags

If the AI step fails (bad key, no internet, rate limit), the app still
returns a rule-based result — it just says "Rule-based only" instead of
"AI-assisted" at the bottom of the card, rather than breaking.

---

## 3. What I could and couldn't verify myself

I wrote and ran the rule engine directly and confirmed it correctly
scores the sample messages above. I could **not** run the FastAPI
server, `npm install`, or the Expo/Streamlit apps themselves in my own
environment — no internet access there, and no Android tooling. So:
run through section 2 above once things are running, and if anything
errors, paste me the exact error and I'll fix it.

---

## 4. What's next (v2 ideas, not built yet)

- Screenshot input (on-device OCR via ML Kit, or pytesseract on the backend)
- URL risk heuristics (no VirusTotal/Safe Browsing — see reasoning below)
- Evidence retrieval for misinformation claims (PIB/govt source lookup)
- Scan history screen in the mobile app (the backend already stores
  history in SQLite and exposes `GET /history` — just needs a UI screen)
- Share-to-app (Android share sheet → pre-filled input)

Deliberately **not** using VirusTotal's public API or Google Safe
Browsing API for URL checks if you ever monetize this — both explicitly
restrict free/public-tier use in commercial products. Build your own
heuristics first (HTTPS, suspicious TLD, redirect chains, brand-domain
mismatch), add a paid threat-intel provider later if needed.

---

## 5. Project structure

```
ai-trust-checker/
├── backend/          FastAPI + SQLite, rule engine, Gemini wrapper
│   └── app/
│       ├── main.py
│       ├── scam_rules.py
│       ├── ai_provider.py
│       └── schemas.py
├── mobile/            Expo React Native app (Expo Go, no native build)
│   └── src/
│       ├── screens/HomeScreen.js
│       ├── components/ResultCard.js
│       └── services/api.js
└── web/                Streamlit version (imports backend/app directly)
    └── streamlit_app.py
```
