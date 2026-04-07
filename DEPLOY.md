# J.A.R.V.I.S. v2 — Deployment Guide
## Railway (backend) + Netlify (dashboard) + Laptop Agent

---

## Architecture

```
Your Phone (Telegram)
      ↕
  Railway ←──── WebSocket ────→ Your Laptop (agent/run.bat)
  (Python)                           (hardware control)
      ↕
  Netlify
  (Dashboard)
```

- **Railway** — Python backend, Telegram bot, always online, free tier
- **Netlify** — React dashboard, static hosting, always online, free tier
- **agent/run.bat** — runs on your laptop when you want hardware control

---

## Step 1 — Get Telegram credentials

1. Open Telegram → search **@BotFather** → send `/newbot`
2. Pick a name and username → copy the **bot token**
3. Open Telegram → search **@userinfobot** → send `/start` → copy your **user ID**

---

## Step 2 — Deploy backend to Railway

1. Go to **https://railway.app** → sign up (free, no credit card)
2. Click **New Project → Deploy from GitHub repo**
   - Or: Install Railway CLI: `npm i -g @railway/cli` → `railway login`
3. Point Railway at the **`backend/`** folder of this project
4. In Railway dashboard → your service → **Variables** tab, add:

   | Key | Value |
   |-----|-------|
   | `TELEGRAM_BOT_TOKEN` | your token from BotFather |
   | `TELEGRAM_USER_ID` | your numeric user ID |
   | `JARVIS_SECRET` | any long random string (e.g. `MySecretABC123xyz`) |
   | `FRONTEND_URL` | leave blank for now, fill in after Netlify deploy |

5. Railway will build and deploy automatically
6. Copy your Railway URL — looks like `https://jarvis-abc123.up.railway.app`

**That's it for the backend.** Your bot is live. Message it on Telegram — it will respond.

### Deploy via CLI (alternative)
```bash
cd backend
railway login
railway init
railway up
```

---

## Step 3 — Deploy frontend to Netlify

1. Go to **https://netlify.com** → sign up (free)
2. Click **Add new site → Import an existing project**
3. Connect your GitHub repo, set:
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `frontend/build`
4. In Netlify → **Site settings → Environment variables**, add:

   | Key | Value |
   |-----|-------|
   | `REACT_APP_API_URL` | your Railway URL (e.g. `https://jarvis-abc123.up.railway.app`) |
   | `REACT_APP_SECRET` | same value as `JARVIS_SECRET` on Railway |

5. Trigger a redeploy → your dashboard is live at `https://your-site.netlify.app`

### Deploy via CLI (alternative)
```bash
cd frontend
# Create .env file:
echo "REACT_APP_API_URL=https://your-railway-url.up.railway.app" > .env
echo "REACT_APP_SECRET=MySecretABC123xyz" >> .env
npm install
npm run build
npx netlify-cli deploy --prod --dir=build
```

---

## Step 4 — Update Railway FRONTEND_URL

Go back to Railway → Variables → set:
```
FRONTEND_URL=https://your-site.netlify.app
```
This keeps CORS clean.

---

## Step 5 — Run the laptop agent

The agent connects your laptop hardware to the cloud.

1. Open the `agent/` folder on your laptop
2. Copy `.env.example` to `.env` and fill in:
   ```
   JARVIS_SERVER_URL=https://your-railway-url.up.railway.app
   JARVIS_SECRET=MySecretABC123xyz
   ```
3. **Double-click `run.bat`** (Windows) or:
   ```bash
   # Mac/Linux:
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python agent.py
   ```

When connected, the terminal shows:
```
==================================================
  J.A.R.V.I.S. AGENT — ONLINE
  Server: https://your-railway-url.up.railway.app
==================================================
```

The dashboard header changes from `LAPTOP OFFLINE` → `LAPTOP ONLINE`.

---

## Step 6 — Iron Hand (phone gyro mouse)

Open this URL on your phone:
```
https://your-railway-url.up.railway.app/ironhand
```

- Tap **CALIBRATE** while holding phone naturally
- Tap **TOGGLE ACTIVE**
- Tilt phone → cursor moves on your laptop
- Tap → left click
- Double tap → double click
- Long press → right click
- Shake → scroll down

---

## Usage

### Dashboard
`https://your-site.netlify.app` — open from any browser, anywhere

### Telegram bot
Send any of these to your bot:
```
open chrome          — launch app
play lofi beats      — YouTube search and play
pause / fullscreen   — playback control
set volume 70        — volume
screenshot           — get screenshot in chat
click / right click  — mouse
type Hello World     — keyboard input
lock screen / sleep  — power
iron hand on         — enable gyro mouse
kill chrome          — terminate process
shutdown in 5 minutes
```

---

## File Structure

```
jarvis/
├── backend/              → deploy this to Railway
│   ├── main.py           — FastAPI server + WebSockets
│   ├── core/
│   │   ├── state.py      — agent connection state
│   │   ├── nlp.py        — natural language parser
│   │   ├── bot.py        — Telegram bot
│   │   ├── youtube.py    — YouTube search
│   │   └── ironhand_ui.py— phone gyro page
│   ├── requirements.txt
│   ├── railway.toml
│   └── .env.example
│
├── frontend/             → deploy this to Netlify
│   ├── src/App.jsx       — complete Iron Man HUD dashboard
│   ├── netlify.toml
│   └── .env.example
│
└── agent/                → run this on your laptop
    ├── agent.py          — hardware control agent
    ├── run.bat           — Windows double-click launcher
    ├── requirements.txt
    └── .env.example
```

---

## Troubleshooting

**Bot not responding**
- Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_USER_ID` in Railway variables
- Railway logs: your Railway dashboard → Deployments → View logs

**Dashboard shows "LAPTOP OFFLINE"**
- Run `agent/run.bat` on your laptop
- Make sure `JARVIS_SERVER_URL` in agent `.env` matches your Railway URL exactly
- Make sure `JARVIS_SECRET` matches on both sides

**Iron Hand cursor not moving**
- iOS: must use Safari (Chrome blocks DeviceMotion)
- Tap CALIBRATE after enabling
- Laptop and phone can be on different networks — it routes through Railway

**CORS errors in browser console**
- Set `FRONTEND_URL` in Railway variables to your Netlify URL
- Redeploy Railway service

**Railway build failing**
- Check `backend/requirements.txt` has all packages
- Check Railway logs for the specific error

**Netlify build failing**
- Make sure `REACT_APP_API_URL` and `REACT_APP_SECRET` are set in Netlify env vars
- Base directory must be set to `frontend`
