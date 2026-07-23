"""
Word-by-word highlighted captions (karaoke-style) -- the same effect used by
CapCut/Opus Clip-style Reels. Built as an .ass subtitle file using libass's
native karaoke (\\kf) tags, then burned in via FFmpeg's subtitles filter.
"""

FONT_CHOICES = ["Arial", "Impact", "Georgia", "Times New Roman", "Comic Sans MS"]
POSITIONS = {"bottom": 2, "center": 5, "top": 8}


def _hex_to_ass_color(hex_str: str) -> str:
    hex_str = hex_str.lstrip("#")
    r, g, b = hex_str[0:2], hex_str[2:4], hex_str[4:6]
    return f"&H00{b}{g}{r}".upper()


def _format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _escape_ass_text(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\n", " ")


def generate_karaoke_ass(
    segments: list[dict],
    ass_path: str,
    video_width: int,
    video_height: int,
    highlight_color: str = "#FFD400",
    base_color: str = "#FFFFFF",
    font: str = "Arial",
    font_size: int = 48,
    bold: bool = True,
    position: str = "bottom",
) -> None:
    primary = _hex_to_ass_color(highlight_color)
    secondary = _hex_to_ass_color(base_color)
    alignment = POSITIONS.get(position, 2)
    bold_flag = -1 if bold else 0

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
Collisions: Normal
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,{font},{font_size},{primary},{secondary},&H00000000,&H80000000,{bold_flag},0,0,0,100,100,0,0,1,2,1,{alignment},20,20,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = [header]

    for seg in segments:
        words = seg.get("words") or []
        if not words:
            continue

        start_ts = _format_ass_time(seg["start"])
        end_ts = _format_ass_time(seg["end"])

        parts = []
        for w in words:
            duration_cs = max(1, int(round((w["end"] - w["start"]) * 100)))
            word_text = _escape_ass_text(w["text"])
            parts.append(f"{{\\kf{duration_cs}}}{word_text} ")

        text = "".join(parts).strip()
        lines.append(f"Dialogue: 0,{start_ts},{end_ts},Karaoke,,0,0,0,,{text}\n")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def burn_karaoke_captions(video_path: str, ass_path: str, output_path: str, fonts_dir: str = "C:/Windows/Fonts") -> None:
    """Burns the karaoke .ass captions directly into the video."""
    import subprocess

    escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    escaped_fonts_dir = fonts_dir.replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles='{escaped_ass}':fontsdir='{escaped_fonts_dir}'",
        "-c:a", "copy",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)