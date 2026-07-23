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

st.set_page_config(page_title="Cutsy", page_icon="✂️", layout="centered")

# ---------- STYLING ----------
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: radial-gradient(circle at 20% 0%, #1a0f2e 0%, #0a0a12 45%, #050507 100%); }
.cutsy-hero { text-align: center; padding: 2.5rem 0 1.5rem 0; }
.cutsy-logo { 
    font-size: 2.8rem; font-weight: 800; 
    background: linear-gradient(90deg, #ff5f8f, #a855f7, #6366f1); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    background-clip: text; letter-spacing: -1px;
}
.cutsy-tagline { color: #9ca3af; font-size: 1.05rem; margin-top: 0.4rem; }
.cutsy-card { 
    background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); 
    border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; 
    padding: 1.6rem; margin-bottom: 1.2rem; 
    box-shadow: 0 8px 32px rgba(168, 85, 247, 0.06);
}
.cutsy-label { color: #e5e7eb; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem; }
[data-testid="stFileUploader"] section { 
    background: rgba(255,255,255,0.03); border: 1.5px dashed rgba(168, 85, 247, 0.35); border-radius: 14px;
}
.stTextInput input { 
    background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; 
    border-radius: 12px !important; color: #f3f4f6 !important; padding: 0.7rem 1rem !important;
}
.stTextInput input:focus { border: 1px solid #a855f7 !important; box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.15) !important; }
div.stButton > button { 
    background: linear-gradient(90deg, #ff5f8f, #a855f7); color: white; border: none; 
    border-radius: 12px; padding: 0.7rem 1.6rem; font-weight: 700; font-size: 1rem; width: 100%; 
    box-shadow: 0 4px 20px rgba(168, 85, 247, 0.3);
}
div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 26px rgba(168, 85, 247, 0.45); }
div.stButton > button:disabled { background: rgba(255,255,255,0.08); color: #6b7280; box-shadow: none; }
[data-testid="stStatusWidget"] { background: rgba(255,255,255,0.03); border-radius: 14px; border: 1px solid rgba(255,255,255,0.08); }
.stAlert { 
    background: linear-gradient(90deg, rgba(168,85,247,0.12), rgba(255,95,143,0.08)) !important; 
    border: 1px solid rgba(168, 85, 247, 0.25) !important; border-radius: 14px !important;
}
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { 
    background: rgba(255,255,255,0.04); border-radius: 10px 10px 0 0; padding: 10px 20px; color: #9ca3af;
}
.stTabs [aria-selected="true"] { background: rgba(168, 85, 247, 0.15); color: #f3f4f6 !important; }
footer, [data-testid="stDecoration"] { display: none; }
</style>""", unsafe_allow_html=True)

# ---------- HERO ----------
st.markdown("""<div class="cutsy-hero">
    <div class="cutsy-logo">✂️ Cutsy</div>
    <div class="cutsy-tagline">Edit your video by just describing what you want.</div>
</div>""", unsafe_allow_html=True)

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
tab_trim, tab_captions, tab_titles, tab_karaoke = st.tabs(
    ["✂️ Trim", "💬 Captions", "🎬 Text Overlays", "🎤 Karaoke Captions"]
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