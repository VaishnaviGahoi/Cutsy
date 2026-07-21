# Cutsy — Day 1: AI Video Trimmer

Part of a 7-day build series: **Cutsy**, a free, open-source alternative
to paid AI video editors, built one feature at a time.

**What it does:** upload a video, type what you want in plain English
("give me the best 30 seconds"), and the AI transcribes it, picks the
best segment, and cuts it — no timeline, no editing skills.

**Pipeline:** Whisper (transcript) → Groq/Llama 3.1 (picks the segment) → FFmpeg (cuts it)

100% free stack — no paid API required beyond Groq's free tier.

---

## 1. Install FFmpeg (required, one-time)

FFmpeg does the actual video cutting. It's not a Python package — install it at the OS level.

**Windows:**
1. Download from https://www.gyan.dev/ffmpeg/builds/ (get the "essentials" build)
2. Unzip, add the `bin` folder to your PATH
3. Verify: open a new terminal, run `ffmpeg -version`

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

## 2. Set up the Python project

```bash
cd cutsy-day1
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Get a free Groq API key

1. Go to https://console.groq.com/keys
2. Sign up (free), create an API key
3. Copy `.env.example` to `.env` and paste your key in:
```
GROQ_API_KEY=gsk_your_actual_key_here
```

## 4. Run it

```bash
streamlit run app.py
```

It'll open in your browser at `http://localhost:8501`. Upload a short
test video (under 2-3 minutes is best for a quick first run — the
Whisper model downloads automatically the first time you transcribe,
~150MB, then it's cached and works offline).

---

## How it works (for your LinkedIn/Instagram post)

1. **Transcription** — `faster-whisper` runs locally on your machine,
   turns speech into a timestamped transcript. No API cost, works offline
   after the first model download.
2. **Segment selection** — the transcript + your request get sent to
   Groq's free Llama 3.1 8B endpoint, which returns a JSON object with
   the best `start`/`end` timestamps and a one-line reason.
3. **Cutting** — FFmpeg re-encodes just that segment to a new file.
   This is the same tool every pro editor uses under the hood.

This is the exact same pattern as tools like Vyra — a chat interface
sitting on top of "tools" the AI can call (transcribe, select, cut).
Cutsy's Day 6 will wrap these same functions as an MCP server so
Claude Desktop can call them directly.

## Suggested demo clip for your post

Use a video where you talk for 60-90 seconds about 2-3 different things
(e.g. "here's my morning routine... here's what I had for breakfast...
here's my workout"). Prompt: *"give me just the part about the workout"*.
It's a clean, legible demo of the AI actually understanding content,
not just cutting the first N seconds.

## Known limitations (mention these — it builds credibility, not weakness)

- Works best on videos where someone is talking (relies on speech for context)
- Whisper's "base" model is fast but not perfect on heavy accents/noise —
  swap to "small" or "medium" in `core/transcribe.py` for more accuracy
  (slower, still free)
- No silent b-roll understanding yet — that's a good "what's next" tease

## Next in the series

- Day 2: Auto-captions, styled and burned in
- Day 3: Animated text overlays / title cards
- Day 4: Cut to the beat (audio-reactive editing)
- Day 5: Match a reference video's style
- Day 6: Wrap everything as an MCP server (Claude Desktop drives the editor directly)
- Day 7: Full combined agent + polished demo
