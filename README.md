# Trail Coach 🏔

AI-powered activity analysis for your Whistler UTMB 50K training.
Connects to Intervals.icu and uses Claude to generate coaching comments.

## Deploy to Railway (free)

### 1. Create a GitHub repo
- Go to github.com → New repository → name it `trail-coach` → Create
- Upload all these files (drag and drop onto the repo page)

### 2. Deploy on Railway
- Go to railway.app and sign up (free, no credit card)
- Click **New Project → Deploy from GitHub repo**
- Select your `trail-coach` repo
- Railway will detect the Procfile and deploy automatically

### 3. Add environment variables
In Railway, go to your project → **Variables** tab → add:

| Variable       | Value                        |
|----------------|------------------------------|
| `ANTHROPIC_KEY`| your Anthropic API key       |
| `ATHLETE_ID`   | i538470 (already default)    |
| `INTERVALS_KEY`| a0saq97m6rjehw9qq5b2fvv7    |

### 4. Get your URL
Railway gives you a public URL like `https://trail-coach-production.up.railway.app`.
Open it on your phone — done!

## Local development

```bash
pip install -r requirements.txt
export ANTHROPIC_KEY=your_key_here
python app.py
```
Then open http://localhost:5000

## Files
- `app.py` — Flask backend (proxies Intervals.icu + Anthropic APIs)
- `templates/index.html` — Mobile-optimised frontend
- `requirements.txt` — Python dependencies
- `Procfile` — Tells Railway how to run the app
