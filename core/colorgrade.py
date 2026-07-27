"""
One-click color grading presets -- cinematic looks built from FFmpeg's
native curves/eq/colorbalance filters. No external LUT files needed.
"""

import subprocess

PRESETS = {
    "Cinematic":        "curves=preset=medium_contrast,eq=saturation=0.9:contrast=1.05",
    "Vintage":          "curves=preset=vintage,eq=saturation=0.8",
    "Vibrant":          "eq=saturation=1.5:contrast=1.1:brightness=0.02",
    "Black & White":    "hue=s=0,eq=contrast=1.15",
    "Warm":             "colorbalance=rs=0.15:bs=-0.1,eq=saturation=1.05",
    "Cool":             "colorbalance=rs=-0.1:bs=0.15,eq=saturation=1.0",
    "Teal & Orange":    "colorbalance=rs=-0.12:bs=0.12:rh=0.12:bh=-0.08,eq=contrast=1.08:saturation=0.95",
    "Faded / Pastel":   "curves=preset=lighter,eq=saturation=0.75:contrast=0.9",
    "Cross Process":    "curves=preset=cross_process,eq=saturation=1.1",
    "High-Contrast B&W": "hue=s=0,curves=preset=strong_contrast",
}


def apply_color_preset(video_path: str, output_path: str, preset_name: str) -> None:
    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}")

    vf = PRESETS[preset_name]
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-c:a", "copy",
        "-preset", "fast",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)