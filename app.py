import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from core.transcribe import transcribe_video, transcribe_video_words
from core.selector import select_segment
from core.trimmer import trim_video, get_video_duration, get_video_resolution
from core.captions import generate_srt, burn_captions
from core.overlays import apply_text_layers, FONT_MAP, ANIMATIONS
from core.karaoke import generate_karaoke_ass, burn_karaoke_captions, FONT_CHOICES as KARAOKE_FONTS
from core.beatsync import detect_beats, build_jump_cut_segments, render_jump_cuts
from core.enhance import apply_speed_ramp, reduce_noise, apply_chroma_key

import base64


@st.cache_data
def _load_logo_b64(path: str) -> str | None:
    """Reads a logo image and returns a base64 data URI, or None if missing."""
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except FileNotFoundError:
        return None


NAV_LOGO_URI = _load_logo_b64("assets/logo_nav1.png")
HERO_LOGO_URI = _load_logo_b64("assets/logo_nav1.png")

st.set_page_config(page_title="Cutsy", page_icon="✂️", layout="wide")

# ---------- STYLING ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

:root {
    --color-1: #FF3EA5;      /* hot pink gradient start */
    --color-2: #7C3AED;      /* violet gradient end */
    --accent: #22D3EE;       /* cyan contrast accent */
    --accent-rgb: 34, 211, 238;
    --warm-rgb: 255, 62, 165;
    --bg-1: #0a0f2e;
    --bg-2: #08081a;
    --bg-3: #030308;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: radial-gradient(circle at 20% 0%, var(--bg-1) 0%, var(--bg-2) 45%, var(--bg-3) 100%); }
.cutsy-hero { text-align: center; padding: 2.5rem 0 1.5rem 0; }
.cutsy-logo {
    font-size: 2.8rem; font-weight: 800;
    background: linear-gradient(90deg, var(--color-1), var(--color-2), var(--accent));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: -1px;
}
.cutsy-tagline { color: #9ca3af; font-size: 1.05rem; margin-top: 0.4rem; }
.cutsy-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
    border: 1px solid rgba(255,255,255,0.08); border-radius: 18px;
    padding: 1.6rem; margin-bottom: 1.2rem;
    box-shadow: 0 8px 32px rgba(var(--accent-rgb), 0.07);
}
.cutsy-label { color: #e5e7eb; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem; }
[data-testid="stFileUploader"] section {
    background: rgba(255,255,255,0.03); border: 1.5px dashed rgba(var(--accent-rgb), 0.4); border-radius: 14px;
}
.stTextInput input {
    background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important; color: #f3f4f6 !important; padding: 0.7rem 1rem !important;
}
.stTextInput input:focus { border: 1px solid var(--accent) !important; box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.18) !important; }
div.stButton > button {
    background: linear-gradient(90deg, var(--color-1), var(--color-2)); color: white; border: none;
    border-radius: 12px; padding: 0.7rem 1.6rem; font-weight: 700; font-size: 1rem; width: 100%;
    box-shadow: 0 4px 20px rgba(var(--warm-rgb), 0.35);
}
div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 26px rgba(var(--warm-rgb), 0.5); }
div.stButton > button:disabled { background: rgba(255,255,255,0.08); color: #6b7280; box-shadow: none; }
[data-testid="stStatusWidget"] { background: rgba(255,255,255,0.03); border-radius: 14px; border: 1px solid rgba(255,255,255,0.08); }
.stAlert {
    background: linear-gradient(90deg, rgba(var(--accent-rgb),0.14), rgba(255,201,60,0.08)) !important;
    border: 1px solid rgba(var(--accent-rgb), 0.28) !important; border-radius: 14px !important;
}
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.04); border-radius: 10px 10px 0 0; padding: 10px 20px; color: #9ca3af;
}
.stTabs [aria-selected="true"] { background: rgba(var(--accent-rgb), 0.16); color: #f3f4f6 !important; }
footer, [data-testid="stDecoration"] { display: none; }

/* ---- Landing page additions ---- */
html { scroll-behavior: smooth; }

.cutsy-navbar {
    position: sticky; top: 0; z-index: 999;
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 2rem;
    background: rgba(10, 10, 18, 0.85);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin: -1rem -1rem 0 -1rem;
}
.cutsy-nav-logo {
    font-size: 1.4rem; font-weight: 800;
    background: linear-gradient(90deg, var(--color-1), var(--color-2), var(--accent));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.cutsy-nav-links a {
    color: #d1d5db; text-decoration: none; margin-left: 1.8rem; font-size: 0.95rem; font-weight: 500;
    transition: color 0.15s ease;
}
.cutsy-nav-links a:hover { color: var(--accent); }
.cutsy-nav-cta {
    background: linear-gradient(90deg, var(--color-1), var(--color-2)); color: white !important;
    padding: 0.5rem 1.2rem; border-radius: 10px; margin-left: 1.8rem !important;
}

.cutsy-hero-big { text-align: center; padding: 5rem 1rem 3rem 1rem; }
.cutsy-hero-big .cutsy-logo-big {
    font-size: 4rem; font-weight: 800; letter-spacing: -2px;
    background: linear-gradient(90deg, var(--color-1), var(--color-2), var(--accent));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.cutsy-hero-sub { color: #9ca3af; font-size: 1.2rem; margin: 1rem auto 2rem auto; max-width: 560px; }
.cutsy-hero-ctas a {
    display: inline-block; text-decoration: none; margin: 0 0.5rem;
    padding: 0.8rem 1.8rem; border-radius: 12px; font-weight: 700; font-size: 1rem;
}
.cutsy-cta-primary { background: linear-gradient(90deg, var(--color-1), var(--color-2)); color: white !important; box-shadow: 0 4px 24px rgba(var(--warm-rgb),0.4); }
.cutsy-cta-secondary { background: rgba(255,255,255,0.06); color: #e5e7eb !important; border: 1px solid rgba(255,255,255,0.15); }

.cutsy-section { padding: 3rem 1rem; }
.cutsy-section-title { text-align: center; font-size: 2rem; font-weight: 800; color: #f3f4f6; margin-bottom: 0.5rem; }
.cutsy-section-sub { text-align: center; color: #9ca3af; margin-bottom: 2.5rem; }

.cutsy-feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.2rem; }
.cutsy-feature-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
    border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 1.6rem;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.cutsy-feature-card:hover { transform: translateY(-4px); border-color: rgba(var(--accent-rgb), 0.45); }
.cutsy-feature-icon { font-size: 1.8rem; margin-bottom: 0.6rem; }
.cutsy-feature-title { font-weight: 700; color: #f3f4f6; margin-bottom: 0.4rem; }
.cutsy-feature-desc { color: #9ca3af; font-size: 0.9rem; line-height: 1.5; }

.cutsy-about-box {
    max-width: 700px; margin: 0 auto; text-align: center;
    color: #c4c4c8; font-size: 1.05rem; line-height: 1.7;
}

.cutsy-footer {
    text-align: center; padding: 3rem 1rem 2rem 1rem; margin-top: 2rem;
    border-top: 1px solid rgba(255,255,255,0.08); color: #6b7280;
}
.cutsy-footer a { color: var(--accent); text-decoration: none; margin: 0 0.6rem; }
.cutsy-footer a:hover { text-decoration: underline; }

/* ---- Logo invert & styling ---- */
.cutsy-nav-logo-img, .cutsy-hero-logo-img {
    filter: invert(1) brightness(2) !important;
    background: transparent !important;
    display: inline-block;
}

/* ---- Animated demo carousel ---- */
.cutsy-demo-frame {
    max-width: 600px; margin: 3rem auto 0 auto; position: relative; height: 200px;
    border-radius: 20px; overflow: hidden;
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}
.cutsy-demo-slide {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center; text-align: center;
    opacity: 0; animation: cutsyDemoFade 16s infinite;
}
.cutsy-demo-slide:nth-child(1) { animation-delay: 0s; }
.cutsy-demo-slide:nth-child(2) { animation-delay: 4s; }
.cutsy-demo-slide:nth-child(3) { animation-delay: 8s; }
.cutsy-demo-slide:nth-child(4) { animation-delay: 12s; }
@keyframes cutsyDemoFade {
    0%   { opacity: 0; transform: translateY(12px); }
    3%   { opacity: 1; transform: translateY(0); }
    22%  { opacity: 1; transform: translateY(0); }
    27%  { opacity: 0; transform: translateY(-12px); }
    100% { opacity: 0; }
}
.cutsy-demo-icon { font-size: 2.8rem; margin-bottom: 0.6rem; }
.cutsy-demo-text { font-size: 1.25rem; font-weight: 700; color: #f3f4f6; }
.cutsy-demo-sub { color: #9ca3af; font-size: 0.9rem; margin-top: 0.3rem; }
</style>
""", unsafe_allow_html=True)

# ---------- NAV BAR ----------
nav_logo_html = (
    f'<img src="{NAV_LOGO_URI}" class="cutsy-nav-logo-img" height="55">'
    if NAV_LOGO_URI else '<div class="cutsy-nav-logo">✂️ Cutsy</div>'
)
st.markdown(f"""
<div class="cutsy-navbar">
    {nav_logo_html}
    <div class="cutsy-nav-links">
        <a href="#features">Features</a>
        <a href="#how-it-works">How it works</a>
        <a href="#about">About</a>
        <a href="#contact">Contact</a>
        <a href="#editor" class="cutsy-nav-cta">Try it free</a>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- BIG HERO ----------
hero_logo_html = (
    f'<img src="{HERO_LOGO_URI}" class="cutsy-hero-logo-img" width="380">'
    if HERO_LOGO_URI else '<div class="cutsy-logo-big">✂️ Cutsy</div>'
)
st.markdown(f"""
<div class="cutsy-hero-big">
    {hero_logo_html}
    <div class="cutsy-hero-sub">What if editing a video was just chatting?</div>
    <div class="cutsy-hero-ctas">
        <a href="#editor" class="cutsy-cta-primary">Try it now</a>
        <a href="https://github.com/VaishnaviGahoi/Cutsy" target="_blank" class="cutsy-cta-secondary">View on GitHub</a>
    </div>
    <div class="cutsy-demo-frame">
        <div class="cutsy-demo-slide">
            <div class="cutsy-demo-icon">📤</div>
            <div class="cutsy-demo-text">Upload your video</div>
            <div class="cutsy-demo-sub">Any format, any length</div>
        </div>
        <div class="cutsy-demo-slide">
            <div class="cutsy-demo-icon">🧠</div>
            <div class="cutsy-demo-text">Describe what you want</div>
            <div class="cutsy-demo-sub">"give me the best 30 seconds"</div>
        </div>
        <div class="cutsy-demo-slide">
            <div class="cutsy-demo-icon">✨</div>
            <div class="cutsy-demo-text">AI edits it instantly</div>
            <div class="cutsy-demo-sub">Trim, caption, sync to the beat</div>
        </div>
        <div class="cutsy-demo-slide">
            <div class="cutsy-demo-icon">⬇️</div>
            <div class="cutsy-demo-text">Download & post</div>
            <div class="cutsy-demo-sub">No watermark, totally free</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- FEATURES ----------
st.markdown("""
<div class="cutsy-section" id="features">
    <div class="cutsy-section-title">Upload your video. Describe the edit. Let AI do the rest.</div>
    <div class="cutsy-section-sub">  </div>
    <div class="cutsy-feature-grid">
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">✂️</div>
            <div class="cutsy-feature-title">Smart Trim</div>
            <div class="cutsy-feature-desc">Describe the cut you want in plain English -- the AI finds the exact moment and trims it for you.</div>
        </div>
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">💬</div>
            <div class="cutsy-feature-title">Auto Captions</div>
            <div class="cutsy-feature-desc">Speech-to-text captions, timed and burned directly into your video, ready to post.</div>
        </div>
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">🎬</div>
            <div class="cutsy-feature-title">Text Overlays</div>
            <div class="cutsy-feature-desc">Add as many timed text layers as you want -- pick the font, color, position, and animation for each.</div>
        </div>
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">🎤</div>
            <div class="cutsy-feature-title">Karaoke Captions</div>
            <div class="cutsy-feature-desc">Word-by-word highlighted captions -- the same effect behind every viral Reels edit.</div>
        </div>
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">🥁</div>
            <div class="cutsy-feature-title">Beat Sync</div>
            <div class="cutsy-feature-desc">Detects the beat in your video's audio and jump-cuts your footage exactly on rhythm.</div>
        </div>
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">⏩</div>
            <div class="cutsy-feature-title">Speed Ramp</div>
            <div class="cutsy-feature-desc">Slow it down for drama or speed it up for a snappy montage -- full control over pacing.</div>
        </div>
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">🔇</div>
            <div class="cutsy-feature-title">Noise Reduction</div>
            <div class="cutsy-feature-desc">Cleans up background hiss, hum, and fan noise from your audio in one click.</div>
        </div>
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">🟢</div>
            <div class="cutsy-feature-title">Chroma Key</div>
            <div class="cutsy-feature-desc">Remove a green screen and drop in any color, image, or video as your new background.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- HOW IT WORKS ----------
st.markdown("""
<div class="cutsy-section" id="how-it-works">
    <div class="cutsy-section-title">How it works</div>
    <div class="cutsy-feature-grid">
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">1️⃣</div>
            <div class="cutsy-feature-title">Upload</div>
            <div class="cutsy-feature-desc">Drop in any video -- MP4, MOV, MKV, AVI, or WEBM.</div>
        </div>
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">2️⃣</div>
            <div class="cutsy-feature-title">Pick a feature</div>
            <div class="cutsy-feature-desc">Trim, caption, overlay text, or sync to the beat -- chain as many as you want.</div>
        </div>
        <div class="cutsy-feature-card">
            <div class="cutsy-feature-icon">3️⃣</div>
            <div class="cutsy-feature-title">Download</div>
            <div class="cutsy-feature-desc">Get your finished video, ready to post -- no watermark, no paywall.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- ABOUT ----------
st.markdown("""
<div class="cutsy-section" id="about">
    <div class="cutsy-section-title">About Cutsy</div>
    <div class="cutsy-about-box">
        Cutsy is being built in public, one feature a day, as a free
        alternative to premium AI video editors. Every feature you see
        here shipped in a single day -- no funding, no team, just an
        open build log. It's free today, and it'll stay free as it grows.
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- CONTACT / FOOTER ----------
st.markdown("""
<div class="cutsy-footer" id="contact">
    <div style="margin-bottom: 0.8rem; color: #9ca3af;">Built by Vaishnavi -- follow the build.</div>
    <a href="https://github.com/VaishnaviGahoi/Cutsy" target="_blank">GitHub</a>
    <a href="https://cutsyeditor.streamlit.app/" target="_blank">Live App</a>
    <div style="margin-top: 1rem; font-size: 0.85rem;">© 2026 Cutsy. Free and open-source.</div>
</div>
""", unsafe_allow_html=True)

# ---------- EDITOR SECTION ----------
st.markdown('<div id="editor"></div>', unsafe_allow_html=True)
st.markdown('<div class="cutsy-section-title" style="padding-top: 2rem;">Try it now</div>', unsafe_allow_html=True)

# ---------- SHARED STATE ----------
if "working_video_path" not in st.session_state:
    st.session_state.working_video_path = None
if "segments" not in st.session_state:
    st.session_state.segments = None
if "tmpdir" not in st.session_state:
    st.session_state.tmpdir = tempfile.mkdtemp()

# ---------- UPLOAD (shared across all tabs) ----------
st.markdown('<div class="cutsy-card">', unsafe_allow_html=True)
st.markdown('<div class="cutsy-label">📹 Upload your video</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(" ", type=["mp4", "mov", "mkv", "avi", "webm"], label_visibility="collapsed")

if uploaded_file is not None:
    raw_path = os.path.join(st.session_state.tmpdir, uploaded_file.name)
    with open(raw_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    if st.session_state.working_video_path is None:
        st.session_state.working_video_path = raw_path
        st.session_state.segments = None

if st.session_state.working_video_path:
    st.video(st.session_state.working_video_path)
    if st.button("🔄 Reset / upload a different video"):
        st.session_state.working_video_path = None
        st.session_state.segments = None
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ---------- TABS ----------
tab_trim, tab_captions, tab_titles, tab_karaoke, tab_beatsync, tab_speed, tab_noise, tab_chroma = st.tabs(
    ["✂️ Trim", "💬 Captions", "🎬 Text Overlays", "🎤 Karaoke Captions", "🥁 Beat Sync",
     "⏩ Speed Ramp", "🔇 Noise Reduction", "🟢 Chroma Key"]
)


def ensure_transcript():
    if st.session_state.segments is None:
        with st.spinner("Transcribing audio..."):
            st.session_state.segments = transcribe_video(st.session_state.working_video_path)
    return st.session_state.segments


with tab_trim:
    if not st.session_state.working_video_path:
        st.info("Upload a video above to get started.")
    else:
        st.markdown('<div class="cutsy-card">', unsafe_allow_html=True)
        st.markdown('<div class="cutsy-label">💬 What do you want?</div>', unsafe_allow_html=True)
        trim_prompt = st.text_input(
            " ", placeholder='e.g. "give me the best 30 seconds"',
            label_visibility="collapsed", key="trim_prompt",
        )
        trim_go = st.button("✨ Generate cut", disabled=not trim_prompt, key="trim_go")
        st.markdown('</div>', unsafe_allow_html=True)

        if trim_go and trim_prompt:
            with st.status("Working on it...", expanded=True) as status:
                st.write("🎙️ Transcribing audio...")
                segments = ensure_transcript()

                st.write("⏱️ Checking video length...")
                duration = get_video_duration(st.session_state.working_video_path)

                st.write("🧠 Picking the best segment...")
                result = select_segment(segments, trim_prompt, duration)

                st.write(f"✅ Selected {result['start']:.1f}s → {result['end']:.1f}s")
                st.write("✂️ Cutting with FFmpeg...")

                output_path = os.path.join(st.session_state.tmpdir, "trimmed.mp4")
                trim_video(st.session_state.working_video_path, result["start"], result["end"], output_path)

                st.session_state.working_video_path = output_path
                st.session_state.segments = None

                status.update(label="Done!", state="complete")

            st.success(f"💡 {result['reason']}")
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button("⬇️ Download trimmed video", data=f.read(),
                                    file_name="cutsy_trimmed.mp4", mime="video/mp4")

with tab_captions:
    if not st.session_state.working_video_path:
        st.info("Upload a video above to get started.")
    else:
        st.markdown('<div class="cutsy-card">', unsafe_allow_html=True)
        st.markdown('<div class="cutsy-label">💬 Add captions to your video</div>', unsafe_allow_html=True)
        st.caption("Auto-generated from speech and burned directly into the video.")
        caption_go = st.button("✨ Generate captions", key="caption_go")
        st.markdown('</div>', unsafe_allow_html=True)

        if caption_go:
            with st.status("Working on it...", expanded=True) as status:
                st.write("🎙️ Transcribing audio...")
                segments = ensure_transcript()

                st.write("📝 Building subtitle file...")
                srt_path = os.path.join(st.session_state.tmpdir, "captions.srt")
                generate_srt(segments, srt_path)

                st.write("🔥 Burning captions into video...")
                output_path = os.path.join(st.session_state.tmpdir, "captioned.mp4")
                burn_captions(st.session_state.working_video_path, srt_path, output_path)

                st.session_state.working_video_path = output_path

                status.update(label="Done!", state="complete")

            st.success("Captions added.")
            st.video(output_path)
            col1, col2 = st.columns(2)
            with col1:
                with open(output_path, "rb") as f:
                    st.download_button("⬇️ Download captioned video", data=f.read(),
                                        file_name="cutsy_captioned.mp4", mime="video/mp4")
            with col2:
                with open(srt_path, "rb") as f:
                    st.download_button("⬇️ Download .srt file", data=f.read(),
                                        file_name="captions.srt", mime="text/plain")

with tab_titles:
    if not st.session_state.working_video_path:
        st.info("Upload a video above to get started.")
    else:
        if "text_layers" not in st.session_state:
            st.session_state.text_layers = []

        video_duration = get_video_duration(st.session_state.working_video_path)

        st.markdown('<div class="cutsy-card">', unsafe_allow_html=True)
        st.markdown('<div class="cutsy-label">Add a text pop-up</div>', unsafe_allow_html=True)
        st.caption(f"Video is {video_duration:.1f}s long. Add as many timed text layers as you want.")

        with st.form("add_layer_form", clear_on_submit=True):
            layer_text = st.text_input("Text", placeholder="e.g. MY TRIP TO GOA")

            col1, col2 = st.columns(2)
            with col1:
                layer_start = st.number_input("Start (seconds)", min_value=0.0,
                                               max_value=float(video_duration), value=0.0, step=0.5)
            with col2:
                layer_end = st.number_input("End (seconds)", min_value=0.1,
                                             max_value=float(video_duration), value=min(3.0, video_duration), step=0.5)

            col3, col4, col5 = st.columns(3)
            with col3:
                layer_font = st.selectbox("Font", list(FONT_MAP.keys()))
            with col4:
                layer_size = st.slider("Font size", 20, 100, 44)
            with col5:
                layer_color = st.color_picker("Color", "#FFFFFF")

            col6, col7, col8 = st.columns(3)
            with col6:
                layer_position = st.selectbox("Position", ["center", "top", "bottom"])
            with col7:
                layer_animation = st.selectbox("Animation", ANIMATIONS)
            with col8:
                layer_anim_duration = st.slider("Transition speed (s)", 0.1, 1.5, 0.4, 0.1)

            add_layer = st.form_submit_button("Add this text layer")

            if add_layer and layer_text and layer_end > layer_start:
                st.session_state.text_layers.append({
                    "text": layer_text,
                    "start": layer_start,
                    "end": layer_end,
                    "font_choice": layer_font,
                    "font_size": layer_size,
                    "color_hex": layer_color,
                    "position": layer_position,
                    "animation": layer_animation,
                    "anim_duration": layer_anim_duration,
                })
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.text_layers:
            st.markdown('<div class="cutsy-card">', unsafe_allow_html=True)
            st.markdown('<div class="cutsy-label">Text layers</div>', unsafe_allow_html=True)

            for i, layer in enumerate(st.session_state.text_layers):
                col_a, col_b = st.columns([5, 1])
                with col_a:
                    st.write(
                        f"**\"{layer['text']}\"** -- {layer['start']:.1f}s to {layer['end']:.1f}s -- "
                        f"{layer['font_choice']} -- {layer['animation']} -- {layer['position']}"
                    )
                with col_b:
                    if st.button("Remove", key=f"remove_{i}"):
                        st.session_state.text_layers.pop(i)
                        st.rerun()

            col_gen, col_clear = st.columns(2)
            with col_gen:
                generate_go = st.button("Render all text layers", key="render_layers")
            with col_clear:
                if st.button("Clear all layers"):
                    st.session_state.text_layers = []
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            if generate_go:
                with st.status("Rendering text overlays...", expanded=True) as status:
                    st.write(f"Compositing {len(st.session_state.text_layers)} text layer(s)...")
                    output_path = os.path.join(st.session_state.tmpdir, "overlaid.mp4")
                    apply_text_layers(
                        st.session_state.working_video_path,
                        st.session_state.text_layers,
                        output_path,
                    )
                    st.session_state.working_video_path = output_path
                    st.session_state.segments = None
                    status.update(label="Done!", state="complete")

                st.success("Text overlays added.")
                st.video(output_path)
                with open(output_path, "rb") as f:
                    st.download_button("Download video with text overlays", data=f.read(),
                                        file_name="cutsy_overlaid.mp4", mime="video/mp4")
        else:
            st.info("No text layers yet -- add one above.")

with tab_karaoke:
    if not st.session_state.working_video_path:
        st.info("Upload a video above to get started.")
    else:
        st.markdown('<div class="cutsy-card">', unsafe_allow_html=True)
        st.markdown('<div class="cutsy-label">Karaoke-style captions</div>', unsafe_allow_html=True)
        st.caption("Each word highlights the instant it's spoken -- the Reels/TikTok caption style.")

        col1, col2 = st.columns(2)
        with col1:
            base_color = st.color_picker("Base color (unspoken)", "#FFFFFF", key="karaoke_base")
        with col2:
            highlight_color = st.color_picker("Highlight color (spoken)", "#FFD400", key="karaoke_highlight")

        col3, col4, col5 = st.columns(3)
        with col3:
            karaoke_font = st.selectbox("Font", KARAOKE_FONTS, key="karaoke_font")
        with col4:
            karaoke_size = st.slider("Font size", 24, 80, 48, key="karaoke_size")
        with col5:
            karaoke_position = st.selectbox("Position", ["bottom", "center", "top"], key="karaoke_position")

        karaoke_bold = st.checkbox("Bold", value=True, key="karaoke_bold")

        karaoke_go = st.button("Generate karaoke captions", key="karaoke_go")
        st.markdown('</div>', unsafe_allow_html=True)

        if karaoke_go:
            with st.status("Working on it...", expanded=True) as status:
                st.write("Transcribing with word-level timing...")
                word_segments = transcribe_video_words(st.session_state.working_video_path)

                st.write("Building karaoke subtitle file...")
                vid_w, vid_h = get_video_resolution(st.session_state.working_video_path)
                ass_path = os.path.join(st.session_state.tmpdir, "karaoke.ass")
                generate_karaoke_ass(
                    word_segments, ass_path,
                    video_width=vid_w,
                    video_height=vid_h,
                    highlight_color=highlight_color,
                    base_color=base_color,
                    font=karaoke_font,
                    font_size=karaoke_size,
                    bold=karaoke_bold,
                    position=karaoke_position,
                )

                st.write("Burning captions into video...")
                output_path = os.path.join(st.session_state.tmpdir, "karaoke.mp4")
                burn_karaoke_captions(st.session_state.working_video_path, ass_path, output_path)

                st.session_state.working_video_path = output_path
                status.update(label="Done!", state="complete")

            st.success("Karaoke captions added.")
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button("Download video with karaoke captions", data=f.read(),
                                    file_name="cutsy_karaoke.mp4", mime="video/mp4")

with tab_beatsync:
    if not st.session_state.working_video_path:
        st.info("Upload a video above to get started.")
    else:
        if "detected_beats" not in st.session_state:
            st.session_state.detected_beats = None
        if "detected_tempo" not in st.session_state:
            st.session_state.detected_tempo = None

        st.markdown('<div class="cutsy-card">', unsafe_allow_html=True)
        st.markdown('<div class="cutsy-label">Cut to the beat</div>', unsafe_allow_html=True)
        st.caption("Detects the beat in your video's own audio, then jump-cuts through your footage exactly on rhythm.")

        detect_go = st.button("Detect beats", key="detect_beats_go")

        if detect_go:
            with st.spinner("Analyzing audio for beats..."):
                tmp_wav = os.path.join(st.session_state.tmpdir, "beat_analysis.wav")
                tempo, beats = detect_beats(st.session_state.working_video_path, tmp_wav)
                st.session_state.detected_tempo = tempo
                st.session_state.detected_beats = beats

        if st.session_state.detected_beats:
            st.success(f"Detected tempo: {st.session_state.detected_tempo:.0f} BPM -- {len(st.session_state.detected_beats)} beats found.")

            col1, col2 = st.columns(2)
            with col1:
                beats_per_cut = st.selectbox("Cut every N beats", [1, 2, 4], index=1, key="beats_per_cut")
            with col2:
                jump_seconds = st.slider("Jump ahead per cut (seconds)", 0.5, 5.0, 2.0, 0.5, key="jump_seconds")

            render_go = st.button("Generate beat-cut edit", key="beatcut_go")

            if render_go:
                with st.status("Rendering jump cuts...", expanded=True) as status:
                    st.write("Building cut points from detected beats...")
                    duration = get_video_duration(st.session_state.working_video_path)
                    segments = build_jump_cut_segments(
                        duration, st.session_state.detected_beats,
                        beats_per_cut=beats_per_cut, jump_seconds=jump_seconds,
                    )

                    st.write(f"Cutting and stitching {len(segments)} beat-synced segments...")
                    output_path = os.path.join(st.session_state.tmpdir, "beatcut.mp4")
                    render_jump_cuts(st.session_state.working_video_path, segments, output_path)

                    st.session_state.working_video_path = output_path
                    st.session_state.segments = None
                    st.session_state.detected_beats = None  # timeline shifted, force re-detect if reused
                    status.update(label="Done!", state="complete")

                st.success("Beat-synced edit complete.")
                st.video(output_path)
                with open(output_path, "rb") as f:
                    st.download_button("Download beat-cut video", data=f.read(),
                                        file_name="cutsy_beatcut.mp4", mime="video/mp4")
        st.markdown('</div>', unsafe_allow_html=True)

with tab_speed:
    if not st.session_state.working_video_path:
        st.info("Upload a video above to get started.")
    else:
        st.markdown('<div class="cutsy-card">', unsafe_allow_html=True)
        st.markdown('<div class="cutsy-label">Speed ramp</div>', unsafe_allow_html=True)
        st.caption("Slow it down for drama, or speed it up for a snappy montage feel.")

        speed_factor = st.select_slider(
            "Speed",
            options=[0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0],
            value=1.0,
            format_func=lambda x: f"{x}x" if x != 1.0 else "Normal (1x)",
            key="speed_factor",
        )
        speed_go = st.button("Apply speed change", disabled=(speed_factor == 1.0), key="speed_go")
        st.markdown('</div>', unsafe_allow_html=True)

        if speed_go:
            with st.status("Working on it...", expanded=True) as status:
                st.write(f"Rendering at {speed_factor}x speed...")
                output_path = os.path.join(st.session_state.tmpdir, "speed.mp4")
                apply_speed_ramp(st.session_state.working_video_path, output_path, speed_factor)
                st.session_state.working_video_path = output_path
                st.session_state.segments = None
                status.update(label="Done!", state="complete")

            st.success(f"Speed changed to {speed_factor}x.")
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button("Download speed-adjusted video", data=f.read(),
                                    file_name="cutsy_speed.mp4", mime="video/mp4")

with tab_noise:
    if not st.session_state.working_video_path:
        st.info("Upload a video above to get started.")
    else:
        st.markdown('<div class="cutsy-card">', unsafe_allow_html=True)
        st.markdown('<div class="cutsy-label">Noise reduction</div>', unsafe_allow_html=True)
        st.caption("Cleans up background hiss, hum, and fan noise from your audio.")

        noise_strength = st.slider("Cleanup strength", 1, 40, 12, key="noise_strength")
        noise_go = st.button("Reduce background noise", key="noise_go")
        st.markdown('</div>', unsafe_allow_html=True)

        if noise_go:
            with st.status("Working on it...", expanded=True) as status:
                st.write("Cleaning up audio...")
                output_path = os.path.join(st.session_state.tmpdir, "denoised.mp4")
                reduce_noise(st.session_state.working_video_path, output_path, strength=noise_strength)
                st.session_state.working_video_path = output_path
                status.update(label="Done!", state="complete")

            st.success("Background noise reduced.")
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button("Download cleaned video", data=f.read(),
                                    file_name="cutsy_denoised.mp4", mime="video/mp4")

with tab_chroma:
    if not st.session_state.working_video_path:
        st.info("Upload a video above to get started.")
    else:
        st.markdown('<div class="cutsy-card">', unsafe_allow_html=True)
        st.markdown('<div class="cutsy-label">Chroma key (green screen)</div>', unsafe_allow_html=True)
        st.caption("Removes a solid-color background and replaces it with a color, image, or video.")

        col1, col2 = st.columns(2)
        with col1:
            key_color_name = st.selectbox("Screen color to remove", ["Green", "Blue"], key="key_color_name")
        with col2:
            similarity = st.slider("Key sensitivity", 0.1, 0.6, 0.3, 0.05, key="chroma_similarity")

        bg_type = st.selectbox("Replace with", ["Solid color", "Image", "Video"], key="chroma_bg_type")

        bg_value = None
        bg_type_key = "color"
        if bg_type == "Solid color":
            bg_value = st.color_picker("Background color", "#000000", key="chroma_bg_color")
            bg_type_key = "color"
        elif bg_type == "Image":
            bg_file = st.file_uploader("Background image", type=["jpg", "jpeg", "png"], key="chroma_bg_image")
            bg_type_key = "image"
            if bg_file is not None:
                bg_value = os.path.join(st.session_state.tmpdir, "chroma_bg_" + bg_file.name)
                with open(bg_value, "wb") as f:
                    f.write(bg_file.getbuffer())
        else:
            bg_file = st.file_uploader("Background video", type=["mp4", "mov", "mkv"], key="chroma_bg_video")
            bg_type_key = "video"
            if bg_file is not None:
                bg_value = os.path.join(st.session_state.tmpdir, "chroma_bg_" + bg_file.name)
                with open(bg_value, "wb") as f:
                    f.write(bg_file.getbuffer())

        chroma_go = st.button("Apply chroma key", disabled=(bg_value is None), key="chroma_go")
        st.markdown('</div>', unsafe_allow_html=True)

        if chroma_go and bg_value:
            with st.status("Working on it...", expanded=True) as status:
                st.write("Reading video info...")
                vid_w, vid_h = get_video_resolution(st.session_state.working_video_path)
                vid_duration = get_video_duration(st.session_state.working_video_path)

                st.write("Keying out background and compositing...")
                key_hex = "0x00FF00" if key_color_name == "Green" else "0x0000FF"
                output_path = os.path.join(st.session_state.tmpdir, "chroma.mp4")
                apply_chroma_key(
                    st.session_state.working_video_path, output_path,
                    video_width=vid_w, video_height=vid_h, video_duration=vid_duration,
                    key_color=key_hex, similarity=similarity, blend=0.1,
                    background_type=bg_type_key, background_value=bg_value,
                )
                st.session_state.working_video_path = output_path
                st.session_state.segments = None
                status.update(label="Done!", state="complete")

            st.success("Background replaced.")
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button("Download chroma-keyed video", data=f.read(),
                                    file_name="cutsy_chroma.mp4", mime="video/mp4")
