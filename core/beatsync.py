"""
Beat-synced jump cuts: detects the beat in a video's own audio track
(librosa), then re-cuts the footage so hard cuts land exactly on the
beat, jumping forward through the timeline at each cut for that
fast, punchy music-video edit style.
"""

import os
import subprocess
import numpy as np
import librosa

def extract_audio(video_path: str, wav_path: str) -> None:
    """Pulls a mono 22.05kHz WAV out of the video for beat analysis."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "22050",
        "-ac", "1",
        wav_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def detect_beats(video_path: str, tmp_wav_path: str) -> tuple[float, list[float]]:
    """
    Returns (tempo_bpm, beat_times_in_seconds).
    """
    extract_audio(video_path, tmp_wav_path)
    try:
        y, sr = librosa.load(tmp_wav_path, sr=22050, mono=True)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        tempo_value = float(np.asarray(tempo).reshape(-1)[0])
        return tempo_value, beat_times
    finally:
        if os.path.exists(tmp_wav_path):
            os.remove(tmp_wav_path)


def build_jump_cut_segments(
    video_duration: float,
    beat_times: list[float],
    beats_per_cut: int = 1,
    jump_seconds: float = 2.0,
) -> list[tuple[float, float]]:
    """
    Turns beat timestamps into (source_start, source_end) segments. Each
    segment's length matches the interval between chosen beats (cuts land
    on the beat), but its source position jumps forward through the
    original footage by `jump_seconds` each cut -- creating the jump-cut effect.
    """
    cut_points = beat_times[::max(1, beats_per_cut)]
    cut_points = [t for t in cut_points if t < video_duration]

    if len(cut_points) < 2:
        n = max(2, int(video_duration // max(0.5, jump_seconds)))
        cut_points = [i * (video_duration / n) for i in range(n + 1)]

    if cut_points[0] > 0:
        cut_points.insert(0, 0.0)
    if cut_points[-1] < video_duration:
        cut_points.append(video_duration)

    segments = []
    source_pos = 0.0
    for i in range(len(cut_points) - 1):
        seg_len = cut_points[i + 1] - cut_points[i]
        if seg_len <= 0.05:
            continue
        start = source_pos % max(0.1, video_duration - seg_len) if video_duration > seg_len else 0.0
        end = min(start + seg_len, video_duration)
        segments.append((start, end))
        source_pos += jump_seconds

    return segments


def render_jump_cuts(video_path: str, segments: list[tuple[float, float]], output_path: str) -> None:
    """Cuts and concatenates the given segments, frame-accurate, in one FFmpeg pass."""
    if not segments:
        raise ValueError("No segments to render.")

    filter_parts = []
    for i, (start, end) in enumerate(segments):
        filter_parts.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]")
        filter_parts.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")

    concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(len(segments)))
    filter_parts.append(f"{concat_inputs}concat=n={len(segments)}:v=1:a=1[outv][outa]")
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)