"""
Speed ramping (slow-mo/fast-mo), audio noise reduction, and chroma key
(green screen background replacement) -- all pure FFmpeg, no paid tools.
"""

import subprocess


def _atempo_chain(factor: float) -> str:
    """FFmpeg's atempo only accepts 0.5-2.0 per instance; chain it for any factor."""
    filters = []
    remaining = factor
    while remaining < 0.5 or remaining > 2.0:
        if remaining < 0.5:
            filters.append("atempo=0.5")
            remaining /= 0.5
        else:
            filters.append("atempo=2.0")
            remaining /= 2.0
    filters.append(f"atempo={remaining:.6f}")
    return ",".join(filters)


def apply_speed_ramp(video_path: str, output_path: str, speed_factor: float) -> None:
    """speed_factor > 1.0 = faster, < 1.0 = slower (slow-mo)."""
    atempo = _atempo_chain(speed_factor)
    filter_complex = f"[0:v]setpts=PTS/{speed_factor}[v];[0:a]{atempo}[a]"

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def reduce_noise(video_path: str, output_path: str, strength: int = 12) -> None:
    """Cleans up background hiss/hum using FFmpeg's afftdn filter."""
    strength = max(1, min(40, strength))
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-af", f"afftdn=nr={strength}:nf=-25",
        "-c:v", "copy",
        "-c:a", "aac",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def apply_chroma_key(
    video_path: str,
    output_path: str,
    video_width: int,
    video_height: int,
    video_duration: float,
    key_color: str = "0x00FF00",
    similarity: float = 0.3,
    blend: float = 0.1,
    background_type: str = "color",
    background_value: str = "#000000",
) -> None:
    """Removes a green/blue screen and composites onto a color, image, or video."""
    inputs = ["-i", video_path]

    if background_type == "image":
        bg_input = ["-loop", "1", "-i", background_value]
    elif background_type == "video":
        bg_input = ["-i", background_value]
    else:
        hexcolor = background_value.lstrip("#")
        bg_input = ["-f", "lavfi", "-i", f"color=c=0x{hexcolor}:s={video_width}x{video_height}:d={video_duration}"]

    filter_complex = (
        f"[0:v]colorkey={key_color}:{similarity}:{blend}[fg];"
        f"[1:v]scale={video_width}:{video_height}[bg];"
        f"[bg][fg]overlay=shortest=1[outv]"
    )

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        *bg_input,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "0:a?",
        "-t", str(video_duration),
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)