"""
Auto Zoom / Ken Burns effect: a slow, cinematic zoom in or out over the
duration of the clip -- great for static/talking-head shots.
"""

import subprocess


def get_video_fps(video_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path,
    ]
    out = subprocess.check_output(cmd).decode().strip()
    if "/" in out:
        num, den = out.split("/")
        den_f = float(den)
        return float(num) / den_f if den_f != 0 else 30.0
    return float(out)


def apply_ken_burns(
    video_path: str,
    output_path: str,
    video_width: int,
    video_height: int,
    video_duration: float,
    direction: str = "in",
    zoom_amount: float = 0.15,
) -> None:
    fps = get_video_fps(video_path)
    total_frames = max(2, int(video_duration * fps))
    last_frame = total_frames - 1

    if direction == "in":
        z_expr = f"1+{zoom_amount}*on/{last_frame}"
    else:
        z_expr = f"(1+{zoom_amount})-{zoom_amount}*on/{last_frame}"

    vf = (
        f"scale=iw*2:-1,"
        f"zoompan=z='{z_expr}':d=1:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={video_width}x{video_height}:fps={fps}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", vf,
        "-c:v", "libx264", "-c:a", "copy",
        "-preset", "fast",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)