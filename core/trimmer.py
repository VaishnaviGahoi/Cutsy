"""
Thin wrapper around FFmpeg for trimming and reading video duration.
Requires ffmpeg/ffprobe to be installed and on PATH.
"""

import subprocess
import json


def get_video_duration(video_path: str) -> float:
    """Returns duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path,
    ]
    output = subprocess.check_output(cmd)
    data = json.loads(output)
    return float(data["format"]["duration"])


def trim_video(input_path: str, start: float, end: float, output_path: str) -> None:
    """
    Cuts [start, end] from input_path and writes to output_path.
    Re-encodes (rather than stream-copy) so the cut points are frame-accurate.
    """
    duration = max(0.1, end - start)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def get_video_resolution(video_path: str) -> tuple[int, int]:
    """Returns (width, height) of the video's first stream using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        video_path,
    ]
    output = subprocess.check_output(cmd)
    data = json.loads(output)
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"])