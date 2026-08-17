"""
Run this once to find out exactly which Gemini models YOUR API key can call.

    cd backend
    .\\venv\\Scripts\\Activate.ps1
    python check_gemini.py

This asks Google directly, instead of us guessing model names one by one.
Paste the full output back to me and I'll set GEMINI_MODEL correctly.
"""

import os
import sys
import httpx

# Reads from the same .env your backend uses
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found. Make sure backend/.env has it set, "
          "and that you're running this from inside the backend/ folder.")
    sys.exit(1)

print(f"Using key ending in ...{API_KEY[-6:]}\n")

LIST_URL = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

print("Asking Google which models this key can access...\n")

try:
    resp = httpx.get(LIST_URL, timeout=15.0)
    print(f"HTTP status: {resp.status_code}\n")

    if resp.status_code != 200:
        print("Raw response (this tells us the actual problem):")
        print(resp.text[:2000])
        sys.exit(1)

    data = resp.json()
    models = data.get("models", [])

    if not models:
        print("Key is valid but no models were returned. Response:")
        print(data)
        sys.exit(0)

    print(f"Found {len(models)} models. Ones that support generateContent (usable for this app):\n")
    usable = []
    for m in models:
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            name = m["name"].replace("models/", "")
            print(f"  - {name}")
            usable.append(name)

    if not usable:
        print("  (none support generateContent)")
    else:
        # Prefer a flash model if one is available
        flash_candidates = [m for m in usable if "flash" in m and "lite" not in m]
        pick = flash_candidates[0] if flash_candidates else usable[0]
        print(f"\nRecommended: set GEMINI_MODEL={pick} in backend/.env")

except Exception as e:
    print(f"Request itself failed: {e}")
    print("This usually means no internet, or a typo in the key.")