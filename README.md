# AI Trust Checker

An AI-powered scam detection application that analyzes suspicious SMS, WhatsApp, and email messages and provides a risk score, scam category, red flags, and recommended action.

## Features

* Analyze suspicious SMS, WhatsApp, and email messages
* Detect scam and phishing patterns
* Generate risk score and risk level
* Identify suspicious red flags
* Provide recommended safety actions
* Rule-based detection with optional Gemini AI reasoning
* Mobile application for quick message checking
* Web application for browser-based testing
* Scan history using SQLite

## Tech Stack

* **Mobile:** React Native + Expo
* **Web:** Streamlit
* **Backend:** Python + FastAPI
* **AI:** Google Gemini API
* **Database:** SQLite

## Setup

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

Run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Mobile

```bash
cd mobile
npm install
npx expo start
```

Open the application using **Expo Go**.

Update the backend IP in:

```text
mobile/src/services/api.js
```

Make sure your phone and laptop are connected to the same Wi-Fi network.

### Web

```bash
cd web
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Demo

Paste a suspicious message such as:

```text
Your SBI account will be blocked today.
Click this link immediately to verify your account.
```

The application analyzes the message and displays:

* **Risk Score**
* **Risk Level**
* **Category**
* **Red Flags**
* **Recommended Action**

You can also test normal messages such as:

```text
Hey, are we still meeting for lunch tomorrow at 1pm?
```

which should produce a low-risk result.

## URLs

* **Backend:** http://localhost:8000
* **Web:** http://localhost:8501
* **Mobile:** Expo Go

## Project Structure

```text
AI-Trust-Checker/
├── backend/
├── mobile/
└── web/
```
## Output 
<img width="50%" alt="AI Trust Checker" src="https://github.com/user-attachments/assets/32b5d333-8eeb-421f-b813-d77e8e167bdd" />  |  <img width="960" height="510" alt="Image" src="https://github.com/user-attachments/assets/a46b6d47-dae8-44ba-92a2-ca42e6a62810" />

## About

AI Trust Checker helps users identify potentially fraudulent messages before clicking links, sharing sensitive information, or making payments.

## Author

Rachabattuni Sai Sindhu
MCA - Jain (Deemed-to-be) University
