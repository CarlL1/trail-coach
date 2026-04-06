import os
import base64
import requests
from flask import Flask, jsonify, request, render_template
from datetime import datetime, timedelta

app = Flask(__name__)

ATHLETE_ID    = os.environ.get("ATHLETE_ID", "i538470")
INTERVALS_KEY = os.environ.get("INTERVALS_KEY", "a0saq97m6rjehw9qq5b2fvv7")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY", "")
INTERVALS_BASE = "https://intervals.icu/api/v1"
ANTHROPIC_URL  = "https://api.anthropic.com/v1/messages"

PLAN_CONTEXT = """
You are a trail running coach analyzing activities for an athlete training for the Whistler UTMB 50K (August 22, 2026).
The athlete is based in Vancouver, BC, trains primarily on the North Shore Mountains, and is following an 18-week block periodization plan with climb-focused adaptations to address an uphill pace gap.
Key race details: ~50km, significant vert, technical mountain terrain.
Training blocks: Base → Build → Peak → Taper.

When analyzing an activity provide:
1. A brief performance assessment (2-3 sentences) comparing effort/metrics to what would be expected for their training phase
2. Key strengths observed in this session
3. One specific actionable focus for the next similar session
4. An overall training comment (encouraging but honest, like a real coach)

Keep the total response under 200 words. Be specific, use the actual data. Tone: knowledgeable, direct, supportive.
""".strip()

def intervals_headers():
    token = base64.b64encode(f"API_KEY:{INTERVALS_KEY}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/activities")
def get_activities():
    days = int(request.args.get("days", 30))
    end   = datetime.now()
    start = end - timedelta(days=days)
    try:
        r = requests.get(
            f"{INTERVALS_BASE}/athlete/{ATHLETE_ID}/activities",
            headers=intervals_headers(),
            params={
                "oldest": start.strftime("%Y-%m-%d"),
                "newest": end.strftime("%Y-%m-%d"),
                "limit": 50,
            },
            timeout=15,
        )
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/analyze", methods=["POST"])
def analyze():
    if not ANTHROPIC_KEY:
        return jsonify({"error": "ANTHROPIC_KEY not set in environment variables."}), 500

    activity = request.json
    if not activity:
        return jsonify({"error": "No activity data provided."}), 400

    dist_km  = round(activity.get("distance", 0) / 1000, 2) if activity.get("distance") else None
    elev_m   = round(activity.get("total_elevation_gain", 0)) if activity.get("total_elevation_gain") else None
    dur_min  = round(activity.get("moving_time", 0) / 60) if activity.get("moving_time") else None
    hr_avg   = round(activity.get("average_heartrate", 0)) if activity.get("average_heartrate") else None
    pace_str = None
    if activity.get("moving_time") and activity.get("distance") and activity["distance"] > 0:
        spk = activity["moving_time"] / (activity["distance"] / 1000)
        pace_str = f"{int(spk // 60)}:{int(spk % 60):02d}/km"

    date_str = ""
    try:
        raw = (activity.get("start_date_local") or activity.get("start_date", "")).replace("Z","")
        date_str = datetime.fromisoformat(raw).strftime("%A, %B %d %Y")
    except Exception:
        date_str = "unknown date"

    lines = [f"Activity: {activity.get('name','Untitled')} ({activity.get('type','Run')}) on {date_str}"]
    if dist_km:  lines.append(f"  Distance:       {dist_km} km")
    if elev_m:   lines.append(f"  Elevation gain: {elev_m} m")
    if dur_min:  lines.append(f"  Moving time:    {dur_min} min")
    if hr_avg:   lines.append(f"  Average HR:     {hr_avg} bpm")
    if pace_str: lines.append(f"  Average pace:   {pace_str}")
    if activity.get("suffer_score"):  lines.append(f"  Suffer score:   {activity['suffer_score']}")
    if activity.get("training_load"): lines.append(f"  Training load:  {activity['training_load']}")
    prompt = "\n".join(lines)

    try:
        r = requests.post(
            ANTHROPIC_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 600,
                "system": PLAN_CONTEXT,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        return jsonify({"comment": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/post-comment", methods=["POST"])
def post_comment():
    data = request.json
    activity_id = data.get("activity_id")
    comment     = data.get("comment")
    if not activity_id or not comment:
        return jsonify({"error": "Missing activity_id or comment"}), 400
    try:
        r = requests.put(
            f"{INTERVALS_BASE}/athlete/{ATHLETE_ID}/activities/{activity_id}",
            headers={**intervals_headers(), "Content-Type": "application/json"},
            json={"description": f"🤖 Coach Analysis\n\n{comment}"},
            timeout=15,
        )
        return jsonify({"ok": r.ok, "status": r.status_code})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
