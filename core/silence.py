"""
Auto silence removal -- detects dead air in the audio track and cuts it
out automatically, using FFmpeg's silencedetect filter plus the same
trim+concat approach as beat-sync jump cuts.
"""

import re
import subprocess


def detect_silence(video_path: str, silence_thresh_db: float = -35, min_silence_duration: float = 0.5) -> list[tuple[float, float]]:
    """Returns a list of (start, end) tuples for detected silent stretches."""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-af", f"silencedetect=noise={silence_thresh_db}dB:d={min_silence_duration}",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    log = result.stderr

    starts = [float(m) for m in re.findall(r"silence_start:\s*([\-\d\.]+)", log)]
    ends = [float(m) for m in re.findall(r"silence_end:\s*([\-\d\.]+)", log)]

    intervals = list(zip(starts, ends))
    if len(starts) > len(ends):
        intervals.append((starts[-1], None))
    return intervals


def build_keep_segments(
    video_duration: float,
    silence_intervals: list[tuple[float, float]],
    padding: float = 0.1,
) -> list[tuple[float, float]]:
    """Inverts silence intervals into the segments to KEEP, with small padding."""
    cleaned = [(s, e if e is not None else video_duration) for s, e in silence_intervals]
    cleaned.sort()

    keep_segments = []
    cursor = 0.0
    for s, e in cleaned:
        s_padded = max(cursor, s + padding)
        e_padded = max(s_padded, e - padding)
        if s_padded > cursor + 0.05:
            keep_segments.append((cursor, s_padded))
        cursor = max(cursor, e_padded)

    if cursor < video_duration - 0.05:
        keep_segments.append((cursor, video_duration))

    return keep_segments if keep_segments else [(0.0, video_duration)]