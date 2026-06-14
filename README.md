# Job Search Command Center — Live Backend

A Python/Flask backend that fetches live finance job openings from the **JSearch API**
(aggregates Google for Jobs across Indeed, LinkedIn, etc.), caches them, refreshes
every 6 hours automatically, and serves them to your front-end.

**Covers:** Saudi Arabia · UAE · Singapore · Malaysia
**Roles:** financial analyst, investment analyst, graduate analyst, credit analyst

---

## What this gives you

Genuinely live, auto-updating job data — the thing a standalone HTML file can't do.
Once deployed, it runs on its own, refreshes on a schedule, and your front-end just
reads the results. It's also a real Python + API + deployment project you can put on
your resume and GitHub.

---

## Step 1 — Get your free JSearch API key (5 minutes)

1. Go to https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
2. Sign up (free) and **Subscribe** to the **Basic (Free)** plan — gives you a monthly
   quota that's plenty for personal use.
3. Copy your **X-RapidAPI-Key** from the dashboard.

> I cannot create this account or hold the key for you — this 5-minute step is yours.
> The key is a secret: never paste it into the front-end or commit it to GitHub.

## Step 2 — Test it locally (optional but recommended)

```bash
pip install -r requirements.txt
export RAPIDAPI_KEY="paste_your_key_here"     # Windows: set RAPIDAPI_KEY=...
python app.py
```
Open http://localhost:5000/api/jobs — you should see JSON with live jobs after ~30s
(it fetches on startup). http://localhost:5000/api/health shows whether the key loaded.

## Step 3 — Deploy free on Render

1. Push this folder to a new **GitHub repository**.
2. Go to https://render.com → sign up → **New + → Web Service** → connect your repo.
3. Render auto-detects Python. Confirm:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
   - Plan: **Free**
4. Under **Environment**, add a variable:
   - Key: `RAPIDAPI_KEY`  Value: *your key from Step 1*
5. Click **Create Web Service**. After it builds, you'll get a URL like
   `https://job-tracker-backend.onrender.com`.
6. Test: visit `https://your-url.onrender.com/api/jobs`

> **Free-tier note:** Render's free web services sleep after ~15 min of inactivity and
> take ~30–60s to wake on the next request. That's fine for personal use — the first
> load may be slow, then it's fast. Your data still refreshes every 6 hours while awake.

## Step 4 — Connect your front-end

Open `index.html`, find the line near the top of the script:

```js
const BACKEND_URL = "https://YOUR-RENDER-URL.onrender.com";
```

Replace it with your actual Render URL. Open `index.html` in a browser — the
**Live Openings** tab now pulls real, auto-refreshing data from your backend.

You can host the front-end free too (GitHub Pages, Netlify, or just open the file
locally — it only needs to *read* from your backend URL).

---

## How it works (for your resume / interviews)

- **`app.py`** — Flask server. On boot it starts a background thread that calls
  JSearch for 4 role-queries × 4 countries, de-duplicates the results, and caches
  them in memory. A scheduler re-runs this every 6 hours. Two JSON endpoints
  (`/api/jobs`, `/api/health`) serve the data.
- **JSearch API** — aggregates Google for Jobs, so one call pulls listings that
  originate across Indeed, LinkedIn, company sites, etc. — legally, via the API.
- **Front-end** — reads `/api/jobs` and renders it; no scraping, no CORS issues,
  because the backend (not the browser) talks to the job API.

**One-line resume bullet:**
> Built and deployed a Python/Flask backend that aggregates live job-market data via
> the JSearch API, with scheduled auto-refresh and a JSON API consumed by a web
> front-end (hosted on Render).

---

## Customising

- **Change roles:** edit the `QUERIES` list in `app.py`.
- **Change countries:** edit the `COUNTRIES` dict.
- **Change refresh frequency:** edit `REFRESH_SECONDS`.
- **Filter to fresh-grad only:** add keyword filters in `fetch_one()` before appending.
