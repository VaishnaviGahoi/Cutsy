"""
Feeds the transcript + user's plain-English request to an LLM (Groq's free tier,
Llama 3.1 8B Instant) and asks it to pick the best start/end timestamps.
"""

import os
import json
import re
from groq import Groq

_CLIENT = None


def _get_client():
    global _CLIENT
    if _CLIENT is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Copy .env.example to .env and add your key "
                "(free at https://console.groq.com/keys)."
            )
        _CLIENT = Groq(api_key=api_key)
    return _CLIENT


def _format_transcript(segments: list[dict]) -> str:
    lines = [f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments]
    return "\n".join(lines)


def select_segment(segments: list[dict], user_prompt: str, video_duration: float) -> dict:
    """
    Returns {"start": float, "end": float, "reason": str}
    """
    client = _get_client()
    transcript_text = _format_transcript(segments)

    system_prompt = (
        "You are a video editing assistant. You are given a timestamped transcript "
        "of a video and a user's request. Pick the single best start and end time "
        "(in seconds) that satisfies the request. "
        "Rules:\n"
        f"- start and end must be within 0 and {video_duration:.1f} seconds.\n"
        "- end must be greater than start.\n"
        "- Respond with ONLY a JSON object, no other text, in this exact format:\n"
        '{"start": <number>, "end": <number>, "reason": "<one short sentence>"}'
    )

    user_message = (
        f"Video duration: {video_duration:.1f} seconds\n\n"
        f"Transcript:\n{transcript_text}\n\n"
        f"User request: {user_prompt}"
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if the model adds them despite instructions
    raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: whole-video if parsing fails, so the app never hard-crashes
        return {"start": 0.0, "end": video_duration, "reason": "Fallback: used full video (parse error)."}

    start = max(0.0, float(data.get("start", 0)))
    end = min(video_duration, float(data.get("end", video_duration)))
    if end <= start:
        start, end = 0.0, video_duration

    return {"start": start, "end": end, "reason": data.get("reason", "")}
