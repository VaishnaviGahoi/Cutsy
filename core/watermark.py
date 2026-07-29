"""
Adds a logo/watermark image overlay in a corner of the video, with
adjustable size and opacity.
"""

import subprocess

POSITIONS = {
    "bottom-right": ("W-w-{m}", "H-h-{m}"),
    "bottom-left":  ("{m}", "H-h-{m}"),
    "top-right":    ("W-w-{m}", "{m}"),
    "top-left":     ("{m}", "{m}"),
}


def add_watermark(
    video_path: str,
    watermark_path: str,
    output_path: str,
    position: str = "bottom-right",
    scale: float = 0.15,
    margin: int = 20,
    opacity: float = 0.8,
) -> None:
    x_tpl, y_tpl = POSITIONS.get(position, POSITIONS["bottom-right"])
    x_expr = x_tpl.format(m=margin)
    y_expr = y_tpl.format(m=margin)

    filter_complex = (
        f"[1:v]scale=iw*{scale}:-1,format=rgba,colorchannelmixer=aa={opacity}[wm];"
        f"[0:v][wm]overlay={x_expr}:{y_expr}[outv]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-loop", "1", "-i", watermark_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "0:a?",
        "-shortest",
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)