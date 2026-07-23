"""
Multi-layer animated text overlays for video — add as many text "pop-ups"
as you want, each with its own timing, font, color, size, position, and
enter/exit animation (fade or slide from a direction). Pure FFmpeg drawtext,
no external rendering engine needed.
"""

import subprocess

FONT_MAP = {
    "Arial": "arial.ttf",
    "Arial Bold": "arialbd.ttf",
    "Times New Roman": "times.ttf",
    "Georgia": "georgia.ttf",
    "Impact": "impact.ttf",
    "Comic Sans MS": "comic.ttf",
}

ANIMATIONS = ["Fade", "Slide from left", "Slide from right", "Slide from top", "Slide from bottom", "None"]


def _escape_text(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("'", "\u2019")
    text = text.replace("%", "\\%")
    return text


def _font_path(font_choice: str) -> str:
    filename = FONT_MAP.get(font_choice, "arial.ttf")
    return f"C\\:/Windows/Fonts/{filename}"


def _hex_to_ffmpeg_color(hex_str: str) -> str:
    return "0x" + hex_str.lstrip("#").upper()


def _position_expr(position: str) -> tuple[str, str]:
    x_expr = "(w-text_w)/2"
    if position == "top":
        y_expr = "h*0.12"
    elif position == "bottom":
        y_expr = "h*0.80"
    else:
        y_expr = "(h-text_h)/2"
    return x_expr, y_expr


def _fade_alpha_expr(start: float, end: float, anim_dur: float) -> str:
    if anim_dur <= 0:
        return "1"
    return (
        f"if(lt(t,{start}+{anim_dur}),(t-{start})/{anim_dur},"
        f"if(lt(t,{end}-{anim_dur}),1,"
        f"max(0,({end}-t)/{anim_dur})))"
    )


def _slide_expr(start: float, end: float, anim_dur: float, target_expr: str, offscreen_expr: str) -> str:
    if anim_dur <= 0:
        return target_expr
    return (
        f"if(lt(t,{start}+{anim_dur}),"
        f"({offscreen_expr})+(({target_expr})-({offscreen_expr}))*(t-{start})/{anim_dur},"
        f"if(lt(t,{end}-{anim_dur}),({target_expr}),"
        f"({target_expr})+(({offscreen_expr})-({target_expr}))*(t-({end}-{anim_dur}))/{anim_dur}))"
    )


def _build_layer_filter(layer: dict) -> str:
    start = float(layer["start"])
    end = float(layer["end"])
    duration = max(0.1, end - start)

    anim_dur = min(float(layer.get("anim_duration", 0.4)), duration / 2)
    animation = layer.get("animation", "Fade")

    font = _font_path(layer.get("font_choice", "Arial"))
    color = _hex_to_ffmpeg_color(layer.get("color_hex", "#FFFFFF"))
    text = _escape_text(layer["text"])
    font_size = int(layer.get("font_size", 44))

    x_target, y_target = _position_expr(layer.get("position", "center"))

    if animation == "Fade":
        x_expr, y_expr = x_target, y_target
        alpha_expr = _fade_alpha_expr(start, end, anim_dur)
    elif animation == "Slide from left":
        x_expr = _slide_expr(start, end, anim_dur, x_target, "-text_w")
        y_expr = y_target
        alpha_expr = "1"
    elif animation == "Slide from right":
        x_expr = _slide_expr(start, end, anim_dur, x_target, "w")
        y_expr = y_target
        alpha_expr = "1"
    elif animation == "Slide from top":
        x_expr = x_target
        y_expr = _slide_expr(start, end, anim_dur, y_target, "-text_h")
        alpha_expr = "1"
    elif animation == "Slide from bottom":
        x_expr = x_target
        y_expr = _slide_expr(start, end, anim_dur, y_target, "h")
        alpha_expr = "1"
    else:
        x_expr, y_expr, alpha_expr = x_target, y_target, "1"

    return (
        f"drawtext=fontfile='{font}':text='{text}':fontsize={font_size}:fontcolor={color}:"
        f"borderw=2:bordercolor=black@0.6:"
        f"x='{x_expr}':y='{y_expr}':"
        f"enable='between(t,{start},{end})':alpha='{alpha_expr}'"
    )


def apply_text_layers(video_path: str, layers: list[dict], output_path: str) -> None:
    if not layers:
        raise ValueError("No text layers provided.")

    filters = [_build_layer_filter(layer) for layer in layers]
    vf = ",".join(filters)

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