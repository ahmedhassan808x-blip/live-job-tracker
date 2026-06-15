"""
Job Search Command Center — Live Backend
=========================================
Fetches live finance job openings from the JSearch API (RapidAPI),
caches them, refreshes on a schedule, and serves them to the front-end.

Covers: Saudi Arabia, UAE, Singapore, Malaysia.

SETUP (one time):
  1. Get a free RapidAPI key: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
  2. Set it as an environment variable named RAPIDAPI_KEY
     (locally: export RAPIDAPI_KEY="your_key"; on Render: add it in the dashboard)
  3. Run locally:  python app.py
     Deploy:       gunicorn app:app
"""

import os
import time
import threading
import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # lets your front-end (any origin) read the API

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"

# ---- What we search for, per country ----
# JSearch takes a free-text query + country code. We run a few queries per
# country to cover the role types relevant to a fresh finance grad.
COUNTRIES = {
    "Saudi Arabia": {"code": "sa", "city": "Riyadh"},
    "UAE":          {"code": "ae", "city": "Dubai"},
    "Singapore":    {"code": "sg", "city": "Singapore"},
    "Malaysia":     {"code": "my", "city": "Kuala Lumpur"},
}

QUERIES = [
    "financial analyst",
    "investment analyst",
    "graduate analyst finance",
    "credit analyst",
]

# ---- In-memory cache ----
CACHE = {"data": {}, "updated_at": None, "status": "starting"}
CACHE_LOCK = threading.Lock()
REFRESH_SECONDS = 6 * 60 * 60  # refresh every 6 hours


def fetch_one(query, country_code):
    """Call JSearch for a single query + country. Returns a list of job dicts."""
    if not RAPIDAPI_KEY:
        return []
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    params = {
        "query": query,
        "country": country_code,
        "page": "1",
        "num_pages": "1",
        "date_posted": "month",   # only recent postings
    }
    try:
        r = requests.get(JSEARCH_URL, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        results = r.json().get("data", []) or []
    except Exception as e:
        print(f"[fetch error] {query}/{country_code}: {e}")
        return []

    jobs = []
    for j in results:
        if not isinstance(j, dict):
            continue
        posted = j.get("job_posted_at_datetime_utc") or ""
        jobs.append({
            "title": j.get("job_title") or "",
            "company": j.get("employer_name") or "",
            "city": j.get("job_city") or j.get("job_country") or "",
            "posted": posted[:10],
            "type": j.get("job_employment_type") or "",
            "url": j.get("job_apply_link") or j.get("job_google_link") or "",
            "remote": j.get("job_is_remote", False),
            "query": query,
        })
    return jobs


def dedupe(jobs):
    """Remove duplicate postings (same title+company)."""
    seen, out = set(), []
    for j in jobs:
        key = (j["title"].lower().strip(), j["company"].lower().strip())
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


def refresh_all():
    """Fetch every query for every country and update the cache."""
    print("[refresh] starting…")
    data = {}
    for country, meta in COUNTRIES.items():
        all_jobs = []
        for q in QUERIES:
            all_jobs.extend(fetch_one(q, meta["code"]))
            time.sleep(1.2)  # be gentle on the free rate limit
        data[country] = dedupe(all_jobs)
        print(f"[refresh] {country}: {len(data[country])} jobs")
    with CACHE_LOCK:
        CACHE["data"] = data
        CACHE["updated_at"] = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
        CACHE["status"] = "ok" if RAPIDAPI_KEY else "no_api_key"
    print("[refresh] done.")


def background_loop():
    """Kept for local use; not relied upon on Render."""
    while True:
        try:
            refresh_all()
        except Exception as e:
            print(f"[loop error] {e}")
        time.sleep(REFRESH_SECONDS)


def ensure_fresh():
    """Fetch jobs right now if the cache is empty. Safe to call on every request."""
    with CACHE_LOCK:
        empty = not CACHE["data"]
    if empty and RAPIDAPI_KEY:
        try:
            refresh_all()
        except Exception as e:
            print(f"[ensure_fresh error] {e}")


# ---- API endpoints ----
@app.route("/api/jobs")
def api_jobs():
    ensure_fresh()
    with CACHE_LOCK:
        return jsonify({
            "updated_at": CACHE["updated_at"],
            "status": CACHE["status"],
            "data": CACHE["data"],
        })


@app.route("/api/refresh")
def api_refresh():
    """Force a fresh fetch regardless of cache."""
    if not RAPIDAPI_KEY:
        return jsonify({"ok": False, "error": "no_api_key"})
    try:
        refresh_all()
        with CACHE_LOCK:
            total = sum(len(v) for v in CACHE["data"].values())
        return jsonify({"ok": True, "updated_at": CACHE["updated_at"], "total": total})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/health")
def health():
    return jsonify({"ok": True, "has_key": bool(RAPIDAPI_KEY),
                    "status": CACHE["status"], "build": "v3-ondemand"})


@app.route("/")
def home():
    if os.path.exists(os.path.join(os.path.dirname(__file__), "index.html")):
        return send_from_directory(os.path.dirname(__file__), "index.html")
    return jsonify({"message": "Job tracker backend running. See /api/jobs"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
