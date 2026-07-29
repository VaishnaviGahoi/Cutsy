"""
Picture-in-picture: overlays a second video clip in a corner of the main
video, with a choice of shape and which clip's audio to keep.
"""

import subprocess

POSITIONS = {
    "bottom-right": ("W-w-{m}", "H-h-{m}"),
    "bottom-left":  ("{m}", "H-h-{m}"),
    "top-right":    ("W-w-{m}", "{m}"),
    "top-left":     ("{m}", "{m}"),
}


def apply_pip(main_path: str, overlay_path: str, output_path: str,
              position: str = "bottom-right", scale: float = 0.3, margin: int = 20,
              shape: str = "rectangle", audio_source: str = "main") -> None:
    """
    shape: "rectangle" | "square" | "circle"
    audio_source: "main" | "overlay"
    """
    x_tpl, y_tpl = POSITIONS.get(position, POSITIONS["bottom-right"])
    x_expr = x_tpl.format(m=margin)
    y_expr = y_tpl.format(m=margin)

    if shape == "circle":
        overlay_chain = (
            f"[1:v]scale=iw*{scale}:-1,"
            f"crop='min(iw,ih)':'min(iw,ih)',"
            f"format=yuva420p,"
            f"geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':"
            f"a='if(lte(pow(X-W/2,2)+pow(Y-H/2,2),pow(W/2,2)),255,0)'[ovr]"
        )
    elif shape == "square":
        overlay_chain = (
            f"[1:v]scale=iw*{scale}:-1,"
            f"crop='min(iw,ih)':'min(iw,ih)'[ovr]"
        )
    else:
        overlay_chain = f"[1:v]scale=iw*{scale}:-1[ovr]"

    filter_complex = f"{overlay_chain};[0:v][ovr]overlay={x_expr}:{y_expr}:shortest=1[outv]"
    audio_map = "1:a?" if audio_source == "overlay" else "0:a?"

    cmd = [
        "ffmpeg", "-y",
        "-i", main_path, "-i", overlay_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", audio_map,
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)