import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from core.transcribe import transcribe_video
from core.selector import select_segment
from core.trimmer import trim_video, get_video_duration
from core.captions import generate_srt, burn_captions

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
tab_trim, tab_captions = st.tabs(["✂️ Trim", "💬 Captions"])

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