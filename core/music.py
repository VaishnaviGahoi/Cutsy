"""
Adds a background music track under a video's existing audio, with
independent volume control for each, looping the music if it's shorter
than the video.
"""

import subprocess


def add_background_music(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.5,
    original_volume: float = 1.0,
) -> None:
    filter_complex = (
        f"[0:a]volume={original_volume}[a0];"
        f"[1:a]volume={music_volume}[a1];"
        f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-stream_loop", "-1", "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)