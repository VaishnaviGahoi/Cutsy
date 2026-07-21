"""
Transcribes a video's audio into timestamped segments using faster-whisper.
Runs fully locally and offline once the model is downloaded — free, no API key needed.
"""

from faster_whisper import WhisperModel

_MODEL = None


def _get_model():
    """Load the whisper model once and reuse it across calls."""
    global _MODEL
    if _MODEL is None:
        # "base" is a good speed/accuracy tradeoff for short clips on CPU.
        # Use "small" or "medium" for better accuracy if you have the compute.
        _MODEL = WhisperModel("base", device="cpu", compute_type="int8")
    return _MODEL


def transcribe_video(video_path: str) -> list[dict]:
    """
    Returns a list of segments: [{"start": float, "end": float, "text": str}, ...]
    """
    model = _get_model()
    segments, _info = model.transcribe(video_path, beam_size=5, vad_filter=True)

    results = []
    for seg in segments:
        results.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
    return results
