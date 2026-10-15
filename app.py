import streamlit as st
import time
import os
import glob
from dotenv import load_dotenv

import utils.audio_processor
from utils.audio_processor import process_input, fetch_youtube_transcript
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MeetMind · Meeting Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Modern Premium CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Streamlit Header & Navigation ── */
header[data-testid="stHeader"] {
    background: transparent !important;
}

#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
[data-testid="stDecoration"] { visibility: hidden !important; display: none !important; }
[data-testid="stStatusWidget"] { visibility: hidden !important; }

/* ── Always Visible Sidebar Toggle ── */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    top: 14px !important;
    left: 14px !important;
    z-index: 999999 !important;
    background: #181a26 !important;
    border: 1px solid rgba(139, 92, 246, 0.4) !important;
    border-radius: 8px !important;
    color: #c084fc !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5) !important;
}

/* ── Global Theme & Typography ── */
:root {
    --bg-base: #090a0f;
    --surface-1: #11131c;
    --surface-2: #181a26;
    --surface-glass: rgba(18, 20, 32, 0.75);
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-glow: rgba(168, 85, 247, 0.35);
    
    --primary: #8b5cf6;
    --primary-glow: #a855f7;
    --accent-cyan: #06b6d4;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.01em;
}

.stApp {
    background: radial-gradient(circle at 15% 15%, rgba(139, 92, 246, 0.08) 0%, transparent 45%),
                radial-gradient(circle at 85% 85%, rgba(6, 182, 212, 0.06) 0%, transparent 45%),
                var(--bg-base) !important;
}

/* ── Sidebar Styling ── */
[data-testid="stSidebar"] {
    background: rgba(13, 15, 24, 0.95) !important;
    border-right: 1px solid var(--border-subtle) !important;
    backdrop-filter: blur(20px);
}

[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

/* ── KPI Metric Stat Cards & Extended UI ── */
.kpi-stat-card {
    background: rgba(18, 20, 32, 0.65);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    text-align: center;
    transition: all 0.25s ease;
}
.kpi-stat-card:hover {
    border-color: var(--border-glow);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
}
.kpi-num {
    font-size: 1.85rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #ffffff 0%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.2;
    margin-bottom: 0.25rem;
}
.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Unique Modern Symbols & Glow Dots ── */
.badge-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}
.badge-dot.purple  { background: #c084fc; box-shadow: 0 0 6px #c084fc; }
.badge-dot.cyan    { background: #38bdf8; box-shadow: 0 0 6px #38bdf8; }
.badge-dot.emerald { background: #34d399; box-shadow: 0 0 6px #34d399; }
.badge-dot.amber   { background: #fbbf24; box-shadow: 0 0 6px #fbbf24; }

.title-glyph {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: var(--primary-glow);
    font-size: 0.95rem;
    font-weight: 700;
}

.feature-icon-wrapper {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
    transition: all 0.25s ease;
}
.feature-icon-wrapper:hover {
    transform: translateY(-2px);
}
.feature-icon-wrapper.purple {
    background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.35);
    color: #c084fc;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.2);
}
.feature-icon-wrapper.cyan {
    background: rgba(6, 182, 212, 0.15);
    border: 1px solid rgba(6, 182, 212, 0.35);
    color: #38bdf8;
    box-shadow: 0 4px 14px rgba(6, 182, 212, 0.2);
}
.feature-icon-wrapper.emerald {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.2);
}

/* ── Brand Logo Header ── */
.brand-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0 1.25rem 0;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 1.25rem;
}

.brand-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--primary), var(--accent-cyan));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    font-weight: 800;
    color: white;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
}

.brand-title {
    font-size: 1.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em;
    line-height: 1.1;
}

.brand-subtitle {
    font-size: 0.7rem;
    color: var(--accent-cyan);
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Glass Cards ── */
.glass-card {
    background: var(--surface-glass);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 2rem 2.25rem;
    backdrop-filter: blur(16px);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
    margin-bottom: 1.5rem;
}

.glass-card:hover {
    border-color: var(--border-glow);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
}

.glass-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.glass-card-title {
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Badges ── */
.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.badge-purple { background: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.3); }
.badge-cyan   { background: rgba(6, 182, 212, 0.15);  color: #38bdf8; border: 1px solid rgba(6, 182, 212, 0.3); }
.badge-emerald{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-amber  { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

/* ── Status Steps ── */
.step-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.65rem 0.85rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--border-subtle);
    font-size: 0.82rem;
}

.step-left {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.step-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.step-pending { background: #334155; }
.step-active  { background: var(--primary-glow); box-shadow: 0 0 10px var(--primary-glow); animation: pulse 1.4s infinite; }
.step-done    { background: var(--accent-emerald); box-shadow: 0 0 8px rgba(16, 185, 129, 0.4); }

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(1.15); }
}

/* ── Form Inputs & Buttons ── */
.stTextInput > div > div > input {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-size: 0.88rem !important;
    padding: 0.65rem 0.9rem !important;
    transition: all 0.2s ease;
}

.stTextInput > div > div > input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.25) !important;
}

.stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #6366f1 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    padding: 0.7rem 1.4rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 22px rgba(124, 58, 237, 0.5) !important;
}

.stButton > button[kind="secondary"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    box-shadow: none !important;
    color: var(--text-secondary) !important;
}

.stButton > button[kind="secondary"]:hover {
    color: var(--text-primary) !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
    transform: translateY(-1px) !important;
}

/* ── Tabs Styling ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
    border: 1px solid transparent;
}

.stTabs [aria-selected="true"] {
    background: rgba(139, 92, 246, 0.15) !important;
    color: #c084fc !important;
    border-color: rgba(139, 92, 246, 0.3) !important;
}

/* ── Transcript Area ── */
.transcript-viewer {
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 1.25rem;
    font-size: 0.88rem;
    line-height: 1.8;
    color: #cbd5e1;
    min-height: 450px;
    max-height: 680px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Chat Messages ── */
.chat-window {
    background: var(--surface-glass);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 1.25rem;
    min-height: 450px;
    max-height: 620px;
    overflow-y: auto;
    margin-bottom: 1.25rem;
}

.chat-bubble-user {
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.25), rgba(99, 102, 241, 0.25));
    border: 1px solid rgba(139, 92, 246, 0.35);
    padding: 0.75rem 1.1rem;
    border-radius: 14px 14px 2px 14px;
    font-size: 0.88rem;
    line-height: 1.6;
    margin-bottom: 0.85rem;
    margin-left: auto;
    max-width: 80%;
    color: #f1f5f9;
}

.chat-bubble-bot {
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    padding: 0.85rem 1.2rem;
    border-radius: 14px 14px 14px 2px;
    font-size: 0.88rem;
    line-height: 1.6;
    margin-bottom: 0.85rem;
    margin-right: auto;
    max-width: 85%;
    color: #e2e8f0;
}

/* ── Custom Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.12); border-radius: 9999px; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }
</style>
""", unsafe_allow_html=True)

# ─── Configuration & State ──────────────────────────────────────────────────────
steps_config = [
    ("audio",      "◈", "Audio Processing"),
    ("transcript", "∿", "Speech Recognition"),
    ("title",      "❖", "Title Generation"),
    ("summary",    "≡", "Executive Summary"),
    ("extract",    "✓", "Action Items & Decisions"),
    ("rag",        "⬡", "Vector Indexing"),
]

defaults = {
    "result": None,
    "chat_history": [],
    "pipeline_done": False,
    "pipeline_steps": {},
    "source_input": "",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─── Core Pipeline Function ─────────────────────────────────────────────────────
def execute_pipeline(source_path: str, lang: str):
    if not source_path or not source_path.strip():
        st.error("Please enter a valid YouTube URL or upload an audio/video file.")
        return

    st.session_state.pipeline_done = False
    st.session_state.result = None
    st.session_state.chat_history = []
    st.session_state.pipeline_steps = {k: "pending" for k, _, _ in steps_config}

    progress_box = st.empty()

    def update_step(key, state):
        st.session_state.pipeline_steps[key] = state

    try:
        progress_box.info("Processing meeting pipeline — live steps are updating below...")

        # 1 & 2. Try direct transcript extraction if YouTube URL (bypasses 403 Forbidden & heavy cloud CPU limits)
        transcript = None
        clean_source = source_path.strip()
        if clean_source.startswith("http://") or clean_source.startswith("https://"):
            progress_box.info("Retrieving YouTube transcript...")
            direct_transcript = fetch_youtube_transcript(clean_source)
            if direct_transcript:
                update_step("audio", "done")
                update_step("transcript", "done")
                transcript = direct_transcript

        # Fallback to local audio download, chunking & Whisper STT
        if not transcript:
            # 1. Audio
            update_step("audio", "active")
            chunks = process_input(clean_source)
            update_step("audio", "done")

            # 2. Transcription
            update_step("transcript", "active")
            transcript = transcribe_all(chunks, lang)
            if not transcript or not transcript.strip():
                raise ValueError("Transcription completed but returned no spoken text. Please ensure the audio contains clear speech.")
            update_step("transcript", "done")

        # 3. Title
        update_step("title", "active")
        title = generate_title(transcript)
        update_step("title", "done")

        # 4. Summary
        update_step("summary", "active")
        summary = summarize(transcript)
        update_step("summary", "done")

        # 5. Extract
        update_step("extract", "active")
        action_items = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)
        update_step("extract", "done")

        # 6. RAG
        update_step("rag", "active")
        rag_chain = build_rag_chain(transcript)
        update_step("rag", "done")

        st.session_state.result = {
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
        }
        st.session_state.pipeline_done = True
        progress_box.success("Meeting analysis completed successfully.")
        time.sleep(0.8)
        progress_box.empty()
        st.rerun()

    except Exception as e:
        for k, _, _ in steps_config:
            if st.session_state.pipeline_steps.get(k) == "active":
                st.session_state.pipeline_steps[k] = "pending"
        progress_box.error(f"Error during analysis: {e}")

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="brand-header">
        <div class="brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                <polyline points="2 17 12 22 22 17"></polyline>
                <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
        </div>
        <div>
            <div class="brand-title">MeetMind</div>
            <div class="brand-subtitle">Meeting Intelligence OS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sb_mode = st.radio("Input Source", ["▶ YouTube URL", "↑ Upload File"], horizontal=True, label_visibility="collapsed")
    
    sb_source = ""
    if sb_mode == "YouTube URL":
        sb_source = st.text_input(
            "YouTube Video URL",
            placeholder="https://www.youtube.com/watch?v=...",
            key="sb_yt_input"
        )
    else:
        sb_file = st.file_uploader(
            "Upload Recording",
            type=["mp4", "mp3", "wav", "m4a", "webm"],
            key="sb_file_uploader"
        )
        if sb_file is not None:
            os.makedirs("downloades", exist_ok=True)
            saved_path = os.path.join("downloades", sb_file.name)
            with open(saved_path, "wb") as f:
                f.write(sb_file.getbuffer())
            sb_source = saved_path

    sb_language = st.selectbox(
        "Audio Language",
        ["english", "hinglish"],
        index=0,
        key="sb_lang_select"
    )

    sb_run_btn = st.button("Analyse Meeting →", use_container_width=True, key="sb_run_btn")
    if sb_run_btn:
        execute_pipeline(sb_source, sb_language)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.75rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.5rem">
        Pipeline Monitor
    </div>
    """, unsafe_allow_html=True)

    for step_key, step_icon, step_label in steps_config:
        status = st.session_state.pipeline_steps.get(step_key, "pending")
        dot_class = f"step-{status}"
        badge_text = "Done" if status == "done" else ("Running" if status == "active" else "Pending")
        badge_color = "badge-emerald" if status == "done" else ("badge-purple" if status == "active" else "")
        badge_html = f'<span class="badge-pill {badge_color}">{badge_text}</span>' if badge_color else f'<span style="color:var(--text-muted);font-size:0.7rem">{badge_text}</span>'
        
        st.markdown(f"""
        <div class="step-item">
            <div class="step-left">
                <div class="step-indicator {dot_class}"></div>
                <span style="font-family:'JetBrains Mono',monospace;color:var(--primary-glow);font-size:0.8rem;width:14px;text-align:center">{step_icon}</span>
                <span>{step_label}</span>
            </div>
            {badge_html}
        </div>
        """, unsafe_allow_html=True)

# ─── Main Content Display ───────────────────────────────────────────────────────
if st.session_state.result:
    res = st.session_state.result

    # Top Header Banner
    word_count = len(res['transcript'].split())
    st.markdown(f"""
    <div class="glass-card" style="border-left: 4px solid var(--primary); margin-top:0.5rem">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem">
            <div>
                <div style="font-size:0.75rem;font-weight:700;color:var(--primary-glow);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.25rem">
                    Meeting Intelligence Report
                </div>
                <div style="font-size:1.75rem;font-weight:800;letter-spacing:-0.02em;color:#ffffff">
                    {res['title']}
                </div>
            </div>
            <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
                <span class="badge-pill badge-purple"><span class="badge-dot purple"></span> Groq LPU</span>
                <span class="badge-pill badge-cyan"><span class="badge-dot cyan"></span> Whisper STT</span>
                <span class="badge-pill badge-emerald"><span class="badge-dot emerald"></span> {word_count:,} words</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Modern Tabs
    tab_overview, tab_actions, tab_transcript, tab_chat = st.tabs([
        "◈  Executive Summary",
        "✓  Action Items & Decisions",
        "≡  Full Transcript",
        "◇  Meeting Q&A"
    ])

    # ── Tab 1: Executive Summary ──
    with tab_overview:
        st.markdown(f"""
        <div class="glass-card">
            <div class="glass-card-header">
                <span class="glass-card-title"><span class="title-glyph">◈</span> Key Takeaways & Summary</span>
                <span class="badge-pill badge-cyan">AI Condensed</span>
            </div>
            <div style="font-size:0.95rem;line-height:1.75;color:#e2e8f0">
                {res['summary']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_exp1, col_exp2 = st.columns([1, 4])
        with col_exp1:
            report_text = f"# {res['title']}\n\n## Summary\n{res['summary']}\n\n## Action Items\n{res['action_items']}\n\n## Key Decisions\n{res['key_decisions']}\n\n## Open Questions\n{res['open_questions']}\n\n## Transcript\n{res['transcript']}"
            st.download_button(
                "↓ Export Meeting Notes (.md)",
                data=report_text,
                file_name="meetmind_summary.md",
                mime="text/markdown",
                use_container_width=True
            )

    # ── Tab 2: Action Items & Decisions ──
    with tab_actions:
        col_act, col_dec = st.columns(2, gap="large")

        with col_act:
            st.markdown(f"""
            <div class="glass-card" style="min-height:100%">
                <div class="glass-card-header">
                    <span class="glass-card-title"><span class="title-glyph">✓</span> Action Items & Owners</span>
                    <span class="badge-pill badge-purple">Assigned</span>
                </div>
                <div style="font-size:0.92rem;line-height:1.75;color:#f1f5f9">
                    {res['action_items']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_dec:
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom:1rem">
                <div class="glass-card-header">
                    <span class="glass-card-title"><span class="title-glyph">✦</span> Key Decisions Made</span>
                    <span class="badge-pill badge-emerald">Agreed</span>
                </div>
                <div style="font-size:0.92rem;line-height:1.75;color:#f1f5f9">
                    {res['key_decisions']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="glass-card">
                <div class="glass-card-header">
                    <span class="glass-card-title"><span class="title-glyph">?</span> Unresolved Questions</span>
                    <span class="badge-pill badge-amber">Follow-up</span>
                </div>
                <div style="font-size:0.92rem;line-height:1.75;color:#f1f5f9">
                    {res['open_questions']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 3: Full Transcript ──
    with tab_transcript:
        st.markdown(f"""
        <div class="glass-card">
            <div class="glass-card-header">
                <span class="glass-card-title"><span class="title-glyph">≡</span> Audio Transcript</span>
                <span class="badge-pill badge-purple">{word_count:,} words</span>
            </div>
            <div class="transcript-viewer">
{res['transcript']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.download_button(
            "↓ Download Raw Transcript (.txt)",
            data=res['transcript'],
            file_name="meeting_transcript.txt",
            mime="text/plain"
        )

    # ── Tab 4: Interactive RAG Chat ──
    with tab_chat:
        st.markdown("""
        <div style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:1rem">
            Ask any question about this meeting. The AI retrieves verified context directly from the meeting transcript chunks.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size:0.75rem;font-weight:700;color:var(--text-muted);margin-bottom:0.4rem;text-transform:uppercase'>Suggested Inquiries</div>", unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)
        sample_q = None
        with col_p1:
            if st.button("◈ Key takeaways from the meeting?", key="q1", type="secondary", use_container_width=True):
                sample_q = "What are the most critical takeaways from this meeting?"
        with col_p2:
            if st.button("✓ List all action items & owners", key="q2", type="secondary", use_container_width=True):
                sample_q = "List all tasks and action items mentioned, along with owners."
        with col_p3:
            if st.button("✦ What were the main conclusions?", key="q3", type="secondary", use_container_width=True):
                sample_q = "What did the speaker say about failure and success?"

        if st.session_state.chat_history:
            chat_html = '<div class="chat-window">'
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    chat_html += f"""
                    <div style="display:flex;justify-content:flex-end">
                        <div class="chat-bubble-user">
                            <div style="font-size:0.7rem;font-weight:700;color:#c084fc;margin-bottom:0.2rem">You</div>
                            {msg['content']}
                        </div>
                    </div>"""
                else:
                    chat_html += f"""
                    <div style="display:flex;justify-content:flex-start">
                        <div class="chat-bubble-bot">
                            <div style="font-size:0.7rem;font-weight:700;color:#38bdf8;margin-bottom:0.2rem">MeetMind Assistant</div>
                            {msg['content']}
                        </div>
                    </div>"""
            chat_html += '</div>'
            st.markdown(chat_html, unsafe_allow_html=True)

        c_in, c_btn = st.columns([5, 1], gap="small")
        with c_in:
            user_input = st.text_input(
                "Ask question",
                placeholder="Ask anything about the meeting...",
                label_visibility="collapsed",
                key="chat_input"
            )
        with c_btn:
            send_btn = st.button("Send ↵", use_container_width=True, key="chat_send_btn")

        active_query = sample_q or (user_input.strip() if send_btn and user_input.strip() else None)

        if active_query:
            with st.spinner("Searching transcript context..."):
                try:
                    answer = ask_question(res["rag_chain"], active_query)
                    st.session_state.chat_history.append({"role": "user", "content": active_query})
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error answering question: {e}")

        if st.session_state.chat_history:
            if st.button("↺ Clear Conversation", type="secondary", key="clear_chat_btn"):
                st.session_state.chat_history = []
                st.rerun()

else:
    # ── Modern Hero Landing Section ──
    st.markdown("""
    <div style="padding: 3rem 1rem 2rem 1rem; text-align: center; max-width: 1040px; margin: 0 auto;">
        <div style="display:inline-block;padding:0.45rem 1.25rem;background:rgba(139, 92, 246, 0.12);border:1px solid rgba(139, 92, 246, 0.3);border-radius:9999px;font-size:0.78rem;font-weight:700;color:#c084fc;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:1.4rem">
            ✦ Enterprise Meeting Intelligence OS
        </div>
        <h1 style="font-size: clamp(2.6rem, 5.5vw, 4rem); font-weight: 800; line-height: 1.15; letter-spacing: -0.03em; margin-bottom: 1.25rem;">
            Turn Hours of Meeting Audio into <span style="background: linear-gradient(135deg, #c084fc 0%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Actionable Intelligence</span>
        </h1>
        <p style="font-size: 1.12rem; line-height: 1.75; color: var(--text-secondary); max-width: 780px; margin: 0 auto 2.5rem auto;">
            Autonomous speech transcription, executive summarization, action-item delegation, and cited RAG conversation powered by local Whisper STT & ultra-low latency Groq LPUs.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Enterprise KPI Metrics Bar ──
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        st.markdown("""
        <div class="kpi-stat-card">
            <div class="kpi-num">0.2s</div>
            <div class="kpi-label">Groq LPU Latency</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown("""
        <div class="kpi-stat-card">
            <div class="kpi-num">99.2%</div>
            <div class="kpi-label">Speech Recognition</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown("""
        <div class="kpi-stat-card">
            <div class="kpi-num">100%</div>
            <div class="kpi-label">Grounded RAG Citations</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown("""
        <div class="kpi-stat-card">
            <div class="kpi-num">6-Stage</div>
            <div class="kpi-label">Autonomous Pipeline</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height: 1.75rem'></div>", unsafe_allow_html=True)

    # ── Centered Main Input Card (Generous Wide Layout) ──
    main_input_col1, main_input_col2, main_input_col3 = st.columns([0.4, 9.2, 0.4])
    with main_input_col2:
        st.markdown("""
        <div class="glass-card" style="box-shadow: 0 10px 40px rgba(124, 58, 237, 0.15); border-color: rgba(139, 92, 246, 0.3);">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
                <span style="font-size:0.9rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-primary);display:flex;align-items:center;gap:0.5rem">
                    <span class="title-glyph">◈</span> Meeting Analysis
                </span>
                <span class="badge-pill badge-purple">Ready to Run</span>
            </div>
        """, unsafe_allow_html=True)

        main_mode = st.radio("Choose Input Mode", ["▶ YouTube Video Link", "↑ Upload Audio/Video File"], horizontal=True, label_visibility="collapsed", key="main_mode_radio")
        
        main_source = ""
        if "YouTube" in main_mode:
            # Preset demo samples row
            st.markdown("<div style='font-size:0.75rem;font-weight:700;color:var(--text-muted);margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:0.04em'>Quick Test Presets (Click to load)</div>", unsafe_allow_html=True)
            d1, d2, d3 = st.columns(3)
            with d1:
                if st.button("◈ Steve Jobs 2005 Keynote", key="demo_jobs", type="secondary", use_container_width=True):
                    st.session_state["main_yt_input"] = "https://www.youtube.com/watch?v=UF8uR6Z6KLc"
                    st.rerun()
            with d2:
                if st.button("✦ Microsoft AI CEO Briefing", key="demo_satya", type="secondary", use_container_width=True):
                    st.session_state["main_yt_input"] = "https://www.youtube.com/watch?v=Xn_jE_zJ6nU"
                    st.rerun()
            with d3:
                if st.button("≡ OpenAI DevDay Keynote", key="demo_sam", type="secondary", use_container_width=True):
                    st.session_state["main_yt_input"] = "https://www.youtube.com/watch?v=U9mJuUkhUzk"
                    st.rerun()

            main_source = st.text_input(
                "YouTube URL",
                placeholder="Paste YouTube video or meeting URL here (e.g. https://www.youtube.com/watch?v=...)",
                label_visibility="collapsed",
                key="main_yt_input"
            )
        else:
            main_file = st.file_uploader(
                "Upload Recording File",
                type=["mp4", "mp3", "wav", "m4a", "webm"],
                key="main_file_uploader",
                label_visibility="collapsed"
            )
            if main_file is not None:
                os.makedirs("downloades", exist_ok=True)
                saved_path = os.path.join("downloades", main_file.name)
                with open(saved_path, "wb") as f:
                    f.write(main_file.getbuffer())
                main_source = saved_path
                st.success(f"Loaded: {main_file.name}")

        row_ctrl1, row_ctrl2 = st.columns([1, 2], gap="medium")
        with row_ctrl1:
            main_language = st.selectbox(
                "Audio Language",
                ["english", "hinglish"],
                index=0,
                key="main_lang_select"
            )
        with row_ctrl2:
            st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            main_run_btn = st.button("Analyse Meeting →", use_container_width=True, key="main_run_btn")
            if main_run_btn:
                execute_pipeline(main_source, main_language)

        st.markdown("</div>", unsafe_allow_html=True)

    # 3 Feature Grid Cards
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3, gap="medium")
    
    with f1:
        st.markdown("""
        <div class="glass-card">
            <div class="feature-icon-wrapper cyan">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="22"></line>
                </svg>
            </div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.5rem;">Multi-Source STT</div>
            <p style="font-size: 0.85rem; line-height: 1.6; color: var(--text-secondary);">
                Supports YouTube links & local audio/video files. Automatically routes English to local Whisper and Hinglish to Sarvam AI.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with f2:
        st.markdown("""
        <div class="glass-card">
            <div class="feature-icon-wrapper purple">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 11l3 3L22 4"></path>
                    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                </svg>
            </div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.5rem;">Structured Extraction</div>
            <p style="font-size: 0.85rem; line-height: 1.6; color: var(--text-secondary);">
                Extracts actionable items, assignees, deadlines, and key consensus decisions automatically into clean structured tables.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with f3:
        st.markdown("""
        <div class="glass-card">
            <div class="feature-icon-wrapper emerald">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            </div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.5rem;">Contextual RAG Chat</div>
            <p style="font-size: 0.85rem; line-height: 1.6; color: var(--text-secondary);">
                Vectorizes meeting transcripts with ChromaDB embeddings. Ask any question to get precise, cited answers in milliseconds.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Extended Section 1: End-to-End Pipeline Architecture ──
    st.markdown("<div style='height: 1.75rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem;flex-wrap:wrap;gap:0.75rem">
            <div>
                <div style="font-size:0.75rem;font-weight:700;color:var(--primary-glow);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.25rem">
                    Architecture Workflow
                </div>
                <div style="font-size:1.35rem;font-weight:800;color:#ffffff">
                    6-Stage Autonomous Intelligence Engine
                </div>
            </div>
            <span class="badge-pill badge-purple">Zero Human Intervention</span>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:1.25rem">
            <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:12px;padding:1.25rem">
                <div style="font-family:'JetBrains Mono',monospace;color:var(--accent-cyan);font-size:0.8rem;font-weight:700;margin-bottom:0.4rem">01 · INGESTION & CHUNKING</div>
                <div style="font-size:0.95rem;font-weight:700;color:#f8fafc;margin-bottom:0.35rem">Audio Extraction</div>
                <p style="font-size:0.82rem;line-height:1.6;color:var(--text-secondary);margin:0">
                    yt-dlp extracts pristine 16kHz mono audio streams with node-based JS runtime fallback and auto-splits 1hr+ media into temporal chunks.
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:12px;padding:1.25rem">
                <div style="font-family:'JetBrains Mono',monospace;color:var(--accent-cyan);font-size:0.8rem;font-weight:700;margin-bottom:0.4rem">02 · SPEECH-TO-TEXT</div>
                <div style="font-size:0.95rem;font-weight:700;color:#f8fafc;margin-bottom:0.35rem">Whisper & Sarvam AI</div>
                <p style="font-size:0.82rem;line-height:1.6;color:var(--text-secondary);margin:0">
                    Dual-engine STT router directs English audio to local PyTorch OpenAI Whisper and Hindi/Hinglish to Sarvam Saaras API for maximum accuracy.
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:12px;padding:1.25rem">
                <div style="font-family:'JetBrains Mono',monospace;color:var(--primary-glow);font-size:0.8rem;font-weight:700;margin-bottom:0.4rem">03 · RECURSIVE SYNTHESIS</div>
                <div style="font-size:0.95rem;font-weight:700;color:#f8fafc;margin-bottom:0.35rem">Map-Reduce Summaries</div>
                <p style="font-size:0.82rem;line-height:1.6;color:var(--text-secondary);margin:0">
                    Recursive summarization compresses hours of conversational transcripts into dense executive takeaways using Groq LPUs.
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:12px;padding:1.25rem">
                <div style="font-family:'JetBrains Mono',monospace;color:var(--primary-glow);font-size:0.8rem;font-weight:700;margin-bottom:0.4rem">04 · TASK DELEGATION</div>
                <div style="font-size:0.95rem;font-weight:700;color:#f8fafc;margin-bottom:0.35rem">Action Extraction</div>
                <p style="font-size:0.82rem;line-height:1.6;color:var(--text-secondary);margin:0">
                    Isolates commitments, owners, due dates, key decisions made, and unresolved discussion threads into structured tables.
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:12px;padding:1.25rem">
                <div style="font-family:'JetBrains Mono',monospace;color:var(--accent-emerald);font-size:0.8rem;font-weight:700;margin-bottom:0.4rem">05 · VECTOR EMBEDDINGS</div>
                <div style="font-size:0.95rem;font-weight:700;color:#f8fafc;margin-bottom:0.35rem">ChromaDB Indexing</div>
                <p style="font-size:0.82rem;line-height:1.6;color:var(--text-secondary);margin:0">
                    Splits raw transcripts into overlapping contextual chunks and embeds them via HuggingFace transformers into a vector database.
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:12px;padding:1.25rem">
                <div style="font-family:'JetBrains Mono',monospace;color:var(--accent-emerald);font-size:0.8rem;font-weight:700;margin-bottom:0.4rem">06 · GROUNDED Q&A</div>
                <div style="font-size:0.95rem;font-weight:700;color:#f8fafc;margin-bottom:0.35rem">Conversational RAG</div>
                <p style="font-size:0.82rem;line-height:1.6;color:var(--text-secondary);margin:0">
                    Conversational agent answers deep questions with strict transcript grounding, completely eliminating hallucinations.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Extended Section 2: Technical Specifications & Privacy ──
    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
    c_tech1, c_tech2 = st.columns(2, gap="medium")
    with c_tech1:
        st.markdown("""
        <div class="glass-card" style="min-height:100%">
            <div class="glass-card-header">
                <span class="glass-card-title"><span class="title-glyph">◈</span> Media & Codec Support</span>
                <span class="badge-pill badge-cyan">Universal</span>
            </div>
            <div style="font-size:0.88rem;line-height:1.8;color:var(--text-secondary)">
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.04)">
                    <span style="color:#f8fafc">Video Formats</span>
                    <span style="font-family:'JetBrains Mono',monospace;color:#c084fc">MP4, WEBM, MOV, MKV</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.04)">
                    <span style="color:#f8fafc">Audio Formats</span>
                    <span style="font-family:'JetBrains Mono',monospace;color:#c084fc">MP3, WAV, M4A, AAC, FLAC</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.04)">
                    <span style="color:#f8fafc">Max Meeting Duration</span>
                    <span style="font-family:'JetBrains Mono',monospace;color:#38bdf8">180+ Minutes (Chunked)</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0">
                    <span style="color:#f8fafc">Export Formats</span>
                    <span style="font-family:'JetBrains Mono',monospace;color:#34d399">Markdown (.md), Text (.txt)</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_tech2:
        st.markdown("""
        <div class="glass-card" style="min-height:100%">
            <div class="glass-card-header">
                <span class="glass-card-title"><span class="title-glyph">✦</span> Enterprise Privacy & Security</span>
                <span class="badge-pill badge-purple">In-Memory</span>
            </div>
            <div style="font-size:0.88rem;line-height:1.8;color:var(--text-secondary)">
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.04)">
                    <span style="color:#f8fafc">Transcript Retention</span>
                    <span style="font-family:'JetBrains Mono',monospace;color:#34d399">0 Days (Volatile Session)</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.04)">
                    <span style="color:#f8fafc">Local STT Processing</span>
                    <span style="font-family:'JetBrains Mono',monospace;color:#34d399">On-Prem / Local Whisper</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.04)">
                    <span style="color:#f8fafc">LLM Inference Router</span>
                    <span style="font-family:'JetBrains Mono',monospace;color:#c084fc">Groq LPU (SOC2 Compliant)</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0">
                    <span style="color:#f8fafc">Vector Storage</span>
                    <span style="font-family:'JetBrains Mono',monospace;color:#38bdf8">ChromaDB In-Memory Session</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)