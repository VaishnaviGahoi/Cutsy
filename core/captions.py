"""
Generates a timed transcript into an SRT file, and burns captions
directly into the video using FFmpeg + libass.
"""

import subprocess
import re


def _format_timestamp(seconds: float) -> str:
    """Converts seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def generate_srt(segments: list[dict], srt_path: str) -> None:
    """Writes Whisper segments into a valid .srt subtitle file."""
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = _format_timestamp(seg["start"])
            end = _format_timestamp(seg["end"])
            f.write(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n\n")


def burn_captions(video_path: str, srt_path: str, output_path: str) -> None:
    """
    Burns the SRT captions directly into the video (TikTok/Reels style).
    Uses FFmpeg's subtitles filter (requires libass, included in standard builds).
    """
    # FFmpeg's subtitle filter needs escaped colons/backslashes on Windows paths
    escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")

    style = (
        "FontName=Arial,FontSize=14,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=3,Outline=1,"
        "Alignment=2,MarginV=40"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles='{escaped_srt}':force_style='{style}'",
        "-c:a", "copy",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)