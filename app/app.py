import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import datetime

# --- CONFIG --------------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Research AI",
    page_icon="[PC]",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- STYLES --------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

:root {
    --bg: #0a0a0f;
    --surface: #111118;
    --surface2: #1a1a24;
    --border: #2a2a3a;
    --accent: #7c6af7;
    --accent2: #f7c26a;
    --accent3: #6af7c2;
    --text: #e8e8f0;
    --text-dim: #888899;
    --danger: #f7706a;
    --success: #6af7a0;
}

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

.stApp { background-color: var(--bg); }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Headers */
h1, h2, h3 { font-family: 'Syne', sans-serif; font-weight: 800; }
h1 { font-size: 2.2rem; letter-spacing: -1px; }
h2 { font-size: 1.4rem; color: var(--text-dim); }

/* Cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.card-accent { border-left: 3px solid var(--accent); }
.card-success { border-left: 3px solid var(--success); }
.card-danger  { border-left: 3px solid var(--danger); }
.card-warn    { border-left: 3px solid var(--accent2); }

/* Status badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-init      { background: #1e1e2e; color: var(--text-dim); border: 1px solid var(--border); }
.badge-progress  { background: #1a1a2e; color: var(--accent);   border: 1px solid var(--accent); }
.badge-complete  { background: #0f2e1a; color: var(--success);  border: 1px solid var(--success); }
.badge-failed    { background: #2e0f0f; color: var(--danger);   border: 1px solid var(--danger); }
.badge-error     { background: #2e0f0f; color: var(--danger);   border: 1px solid var(--danger); }

/* Job table */
.job-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.job-table th {
    background: var(--surface2);
    color: var(--text-dim);
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border);
}
.job-table td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    vertical-align: middle;
}
.job-table tr:hover td { background: var(--surface2); }

/* Mono text */
.mono { font-family: 'Space Mono', monospace; font-size: 0.8rem; }

/* Stream box */
.stream-box {
    background: #0d0d15;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    font-family: 'Space Mono', monospace;
    font-size: 0.78rem;
    color: var(--accent3);
    max-height: 480px;
    overflow-y: auto;
    line-height: 1.6;
}

/* Divider */
.divider { border: none; border-top: 1px solid var(--border); margin: 20px 0; }

/* Buttons */
.stButton > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    padding: 8px 22px !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
}

/* Metric cards */
.metric-row { display: flex; gap: 12px; margin-bottom: 16px; }
.metric {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
}
.metric-label { font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.metric-value { font-size: 1.6rem; font-weight: 800; color: var(--accent); }

/* Pill tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--surface) !important;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    color: var(--text-dim) !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: white !important;
}

/* Alerts */
.stAlert { border-radius: 8px !important; }

/* Radio buttons */
.stRadio [data-testid="stMarkdownContainer"] p { color: var(--text) !important; }

/* Hide streamlit branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# --- HELPERS -------------------------------------------------------------------
def badge(status: str) -> str:
    cls = {
        "initiated": "badge-init",
        "initializing": "badge-init",
        "in_progress": "badge-progress",
        "complete": "badge-complete",
        "failed": "badge-failed",
        "error": "badge-error",
    }.get(status.lower(), "badge-init")
    return f'<span class="badge {cls}">{status.upper()}</span>'


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def api_get(path: str, timeout: int = 10):
    try:
        r = requests.get(f"{BASE_URL}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "[X] Cannot connect to API. Is the server running on 127.0.0.1:8000?"
    except Exception as e:
        return None, str(e)


def api_post(path: str, payload: dict, timeout: int = 10):
    try:
        r = requests.post(f"{BASE_URL}{path}", json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "[X] Cannot connect to API."
    except Exception as e:
        return None, str(e)


def render_state_details(details: dict):
    """Renders the nested state_details schema into structured UI panels."""
    if not details or not isinstance(details, dict):
        st.info("No state details available yet.")
        return

    ex = details.get("execution_state", {})
    kn = details.get("knowledge_state", {})
    dr = details.get("drafting_state", {})
    me = details.get("memory_state", {})

    pct = ex.get("progress_percent", 0)
    try:
        pct_val = float(pct)
    except (TypeError, ValueError):
        pct_val = 0.0

    phase       = ex.get("phase", "-")
    node_hint   = ex.get("possible_active_node_hint", "-")
    has_error   = ex.get("has_error", False)
    error_msg   = ex.get("error_message")
    sect        = ex.get("section_tracker", {})
    cur_idx     = sect.get("current_index", -1)
    total_sec   = sect.get("total_sections", 0)
    summarizing = sect.get("is_summarizing", False)

    raw_e   = kn.get("raw_entries_collected", 0)
    synth_e = kn.get("synthesized_entries", 0)

    completed    = dr.get("completed_sections_count", 0)
    next_heading = dr.get("next_target_heading") or "-"
    pending_ord  = dr.get("pending_build_order", "-")

    log_sz     = me.get("global_log_size", 0)
    msg_ct     = me.get("messages_count", 0)
    has_output = me.get("has_final_output", False)

    st.markdown(f"""
    <div style="margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span style="font-size:0.8rem; color:#888899; text-transform:uppercase; letter-spacing:1px;">Progress -- {phase}</span>
            <span style="font-family:'Space Mono',monospace; font-size:0.82rem; color:var(--accent); font-weight:700;">{pct_val:.0f}%</span>
        </div>
        <div style="background:#1a1a24; border-radius:4px; height:8px; overflow:hidden;">
            <div style="width:{min(pct_val,100):.1f}%; height:100%; background:linear-gradient(90deg,#7c6af7,#6af7c2); border-radius:4px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="card" style="margin-bottom:10px;">
            <div style="font-size:0.7rem; color:#7c6af7; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; font-weight:700;">&gt; Execution</div>
            <table style="width:100%; font-size:0.78rem; border-collapse:collapse;">
                <tr><td style="color:#888899; padding:3px 0; width:50%;">Active Node</td><td style="color:#f7c26a; font-family:'Space Mono',monospace; font-size:0.7rem;">{str(node_hint)[:40]}</td></tr>
                <tr><td style="color:#888899; padding:3px 0;">Sections</td><td style="color:#e8e8f0;">{cur_idx + 1} / {total_sec}</td></tr>
                <tr><td style="color:#888899; padding:3px 0;">Summarizing</td><td style="color:{'#6af7c2' if summarizing else '#888899'};">{'Yes' if summarizing else 'No'}</td></tr>
                <tr><td style="color:#888899; padding:3px 0;">Error</td><td style="color:{'#f7706a' if has_error else '#6af7a0'};">{'[!] ' + str(error_msg)[:50] if has_error else '[OK] None'}</td></tr>
            </table>
        </div>
        <div class="card">
            <div style="font-size:0.7rem; color:#6af7c2; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; font-weight:700;">* Knowledge</div>
            <table style="width:100%; font-size:0.78rem; border-collapse:collapse;">
                <tr><td style="color:#888899; padding:3px 0;">Raw Entries</td><td style="color:#e8e8f0; font-weight:700; font-size:1rem;">{raw_e}</td></tr>
                <tr><td style="color:#888899; padding:3px 0;">Synthesized</td><td style="color:#6af7c2; font-weight:700; font-size:1rem;">{synth_e}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="card" style="margin-bottom:10px;">
            <div style="font-size:0.7rem; color:#f7c26a; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; font-weight:700;">~ Drafting</div>
            <table style="width:100%; font-size:0.78rem; border-collapse:collapse;">
                <tr><td style="color:#888899; padding:3px 0; width:50%;">Completed</td><td style="color:#e8e8f0; font-weight:700; font-size:1rem;">{completed}</td></tr>
                <tr><td style="color:#888899; padding:3px 0;">Next Heading</td><td style="color:#f7c26a; font-style:italic; font-size:0.75rem;">{str(next_heading)[:50]}</td></tr>
                <tr><td style="color:#888899; padding:3px 0;">Build Order</td><td style="color:#e8e8f0;">{pending_ord}</td></tr>
            </table>
        </div>
        <div class="card">
            <div style="font-size:0.7rem; color:#f7706a; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; font-weight:700;">= Memory</div>
            <table style="width:100%; font-size:0.78rem; border-collapse:collapse;">
                <tr><td style="color:#888899; padding:3px 0; width:50%;">Log Entries</td><td style="color:#e8e8f0; font-weight:700;">{log_sz}</td></tr>
                <tr><td style="color:#888899; padding:3px 0;">Messages</td><td style="color:#e8e8f0; font-weight:700;">{msg_ct}</td></tr>
                <tr><td style="color:#888899; padding:3px 0;">Final Output</td><td style="color:{'#6af7a0' if has_output else '#888899'};">{'[OK] Ready' if has_output else '-- Pending'}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)


# --- SIDEBAR -------------------------------------------------------------------
with st.sidebar:
    st.markdown("## [PC] Research AI")
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Health check — use filled circle HTML entity (safe, ASCII-range HTML)
    health, err = api_get("/health")
    if health:
        st.markdown('<span style="color:#6af7a0;">&#9679;</span> **API Online**', unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#f7706a;">&#9679;</span> **API Offline**', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["[>] Start Research", "[~] Live Monitor", "[=] Jobs Dashboard"],
        label_visibility="collapsed"
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(f'<span class="mono" style="color:#888899">endpoint: 127.0.0.1:8000</span>', unsafe_allow_html=True)


# ==============================================================================
# PAGE 1 -- START RESEARCH
# ==============================================================================
if page == "[>] Start Research":
    st.markdown("# Start Research")
    st.markdown("### Submit a new research job to the AI pipeline")
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    col_form, col_side = st.columns([3, 1])

    with col_form:

        # -- Section: user_req -------------------------------------------------
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:14px;">
            <div style="width:3px; height:22px; background:var(--accent); border-radius:2px;"></div>
            <span style="font-weight:800; font-size:1.05rem; letter-spacing:-0.3px;">Research Request</span>
            <span class="mono" style="font-size:0.7rem; color:#888899; margin-left:4px;">user_req</span>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            topic = st.text_input(
                "Topic *",
                placeholder="e.g. Machine learning",
                help="Primary research subject"
            )
            description = st.text_area(
                "Description",
                placeholder="e.g. History and Future.",
                height=80,
                help="Short description or angle for the research"
            )

            col_a, col_b = st.columns(2)
            with col_a:
                min_sections = st.number_input(
                    "Min Sections", min_value=1, max_value=30, value=7,
                    help="Minimum number of sections in the output document"
                )

            # Points to include -- dynamic list
            st.markdown('<div style="margin-top:8px; margin-bottom:4px; font-size:0.85rem; color:#888899;">Points to Include</div>', unsafe_allow_html=True)
            if "points_list" not in st.session_state:
                st.session_state.points_list = ["Energy usage", "Manufacturing challenges", "Cost parity timelines"]

            points_text = st.text_area(
                "points_to_include",
                value="\n".join(st.session_state.points_list),
                height=100,
                label_visibility="collapsed",
                placeholder="One point per line...",
                help="Each line becomes one item in points_to_include"
            )

            # Compulsory headings -- dynamic list
            st.markdown('<div style="margin-top:12px; margin-bottom:4px; font-size:0.85rem; color:#888899;">Compulsory Headings</div>', unsafe_allow_html=True)
            if "headings_list" not in st.session_state:
                st.session_state.headings_list = [
                    "Executive Summary", "Introduction",
                    "Technical Challenges", "Economic Outlook", "Conclusion"
                ]

            headings_text = st.text_area(
                "compulsory_headings",
                value="\n".join(st.session_state.headings_list),
                height=120,
                label_visibility="collapsed",
                placeholder="One heading per line...",
                help="Each line becomes one required section heading"
            )

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # -- Section: config ---------------------------------------------------
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:14px;">
            <div style="width:3px; height:22px; background:var(--accent2); border-radius:2px;"></div>
            <span style="font-weight:800; font-size:1.05rem; letter-spacing:-0.3px;">Configuration</span>
            <span class="mono" style="font-size:0.7rem; color:#888899; margin-left:4px;">config</span>
        </div>
        """, unsafe_allow_html=True)

        cfg_col1, cfg_col2 = st.columns(2)

        with cfg_col1:
            st.markdown('<div style="font-size:0.82rem; color:#f7c26a; font-weight:700; margin-bottom:8px;">[cfg] LLM</div>', unsafe_allow_html=True)
            llm_model = st.text_input(
                "Model", value="gemini-2.5-flash",
                help="Model identifier string"
            )
            llm_provider = st.selectbox(
                "Provider",
                ["azureopenai", "gemini"],
                help="LLM backend provider"
            )
            llm_max_tokens = st.number_input(
                "Max Tokens", min_value=256, max_value=32000, value=3000, step=256
            )

        with cfg_col2:
            st.markdown('<div style="font-size:0.82rem; color:#6af7c2; font-weight:700; margin-bottom:8px;">[net] Graph</div>', unsafe_allow_html=True)
            research_enabled = st.toggle("Research Enabled", value=True)
            max_web_search = st.number_input(
                "Max Web Search Limit", min_value=0, max_value=50, value=1
            )
            max_web_crawl = st.number_input(
                "Max Web Crawl Limit", min_value=0, max_value=100, value=10
            )
            keep_raw_crawl = st.toggle("Keep Raw Crawl", value=True)

        debug_mode = st.toggle("Debug Mode", value=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # -- Payload preview ---------------------------------------------------
        def build_payload():
            points = [p.strip() for p in points_text.splitlines() if p.strip()]
            headings = [h.strip() for h in headings_text.splitlines() if h.strip()]
            return {
                "user_req": {
                    "topic": topic.strip(),
                    "description": description.strip(),
                    "points_to_include": points,
                    "min_sections": min_sections,
                    "compulsory_headings": headings,
                },
                "config": {
                    "llm": {
                        "model": llm_model.strip(),
                        "provider": llm_provider,
                        "max_tokens": llm_max_tokens,
                    },
                    "graph": {
                        "research_enabled": research_enabled,
                        "max_web_search_limit": max_web_search,
                        "max_web_crawl_limit": max_web_crawl,
                        "keep_raw_crawl": keep_raw_crawl,
                    },
                    "debug": debug_mode,
                },
            }

        with st.expander("[v] Preview Payload JSON"):
            try:
                st.json(build_payload())
            except Exception:
                st.warning("Fill in required fields to preview payload.")

        # -- Submit ------------------------------------------------------------
        if st.button("[>] Launch Research Job", use_container_width=True):
            if not topic.strip():
                st.error("Topic is required.")
            else:
                payload = build_payload()
                with st.spinner("Submitting job..."):
                    result, err = api_post("/research/start", payload)

                if err:
                    st.error(err)
                else:
                    st.success("[OK] Research job started!")
                    job_id = result.get("job_id", "")

                    st.markdown(f"""
                    <div class="card card-success">
                        <div class="mono" style="color:#6af7c2; font-size:0.85rem; margin-bottom:8px;">JOB CREATED</div>
                        <div style="font-size:1.1rem; font-weight:700; margin-bottom:12px;">{job_id}</div>
                        <table style="width:100%; font-size:0.82rem; color:#888899;">
                            <tr><td>Status</td><td class="mono">/research/jobs/{job_id}</td></tr>
                            <tr><td>Stream</td><td class="mono">/research/jobs/{job_id}/stream</td></tr>
                            <tr><td>Live feed</td><td class="mono">/research/jobs/{job_id}/feed</td></tr>
                            <tr><td>Events</td><td class="mono">/research/jobs/{job_id}/events</td></tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                    if "recent_jobs" not in st.session_state:
                        st.session_state.recent_jobs = []
                    st.session_state.recent_jobs.insert(0, job_id)

    # -- Right sidebar panel ---------------------------------------------------
    with col_side:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### [#] Recent Jobs")
        recent = st.session_state.get("recent_jobs", [])
        if recent:
            for jid in recent[:8]:
                st.markdown(
                    f'<div class="mono" style="font-size:0.72rem; color:#7c6af7; '
                    f'margin-bottom:8px; word-break:break-all; padding:6px 8px; '
                    f'background:#1a1a2e; border-radius:6px;">{jid}</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown('<span style="color:#888899; font-size:0.85rem;">No jobs started yet.</span>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### [?] Schema")
        st.markdown("""
<div class="mono" style="font-size:0.68rem; color:#888899; line-height:2;">
<b style="color:#e8e8f0;">user_req</b><br>
&nbsp;&nbsp;topic *<br>
&nbsp;&nbsp;description<br>
&nbsp;&nbsp;points_to_include[]<br>
&nbsp;&nbsp;min_sections<br>
&nbsp;&nbsp;compulsory_headings[]<br>
<b style="color:#e8e8f0;">config</b><br>
&nbsp;&nbsp;llm.model<br>
&nbsp;&nbsp;llm.provider<br>
&nbsp;&nbsp;llm.max_tokens<br>
&nbsp;&nbsp;graph.research_enabled<br>
&nbsp;&nbsp;graph.max_web_search_limit<br>
&nbsp;&nbsp;graph.max_web_crawl_limit<br>
&nbsp;&nbsp;graph.keep_raw_crawl<br>
&nbsp;&nbsp;debug
</div>
""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# PAGE 2 -- LIVE MONITOR
# ==============================================================================
elif page == "[~] Live Monitor":
    st.markdown("# Live Monitor")
    st.markdown("### Stream real-time updates for any research job")
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    job_id = st.text_input(
        "Job ID",
        placeholder="Paste a job UUID here...",
        value=st.session_state.get("recent_jobs", [""])[0] if st.session_state.get("recent_jobs") else "",
    )

    mode_tab1, mode_tab2, mode_tab3, mode_tab4 = st.tabs([
        "[#] Status Snapshot",
        "[~] Limited Stream",
        "[>] Live Feed",
        "[!] Events (Delta)",
    ])

    # -- TAB 1: Status Snapshot ------------------------------------------------
    with mode_tab1:
        st.caption("Single fetch from `/research/jobs/{id}` -- shows full structured state.")
        if st.button("[>] Fetch Status", key="snap_btn", use_container_width=False):
            if not job_id:
                st.error("Enter a Job ID.")
            else:
                with st.spinner("Fetching..."):
                    data, err = api_get(f"/research/jobs/{job_id}")
                if err:
                    st.error(err)
                else:
                    st.session_state["snap_data"] = data

        snap = st.session_state.get("snap_data")
        if snap:
            status = snap.get("status", "unknown")
            st.markdown(
                f'{badge(status)}&nbsp;&nbsp;<span class="mono" style="font-size:0.75rem; color:#888899;">{snap.get("job_id","")}</span>',
                unsafe_allow_html=True
            )
            st.markdown('<hr class="divider">', unsafe_allow_html=True)
            render_state_details(snap.get("state_details"))

    # -- TAB 2: Limited Stream -------------------------------------------------
    with mode_tab2:
        st.caption("Fixed-count SSE stream from `/research/jobs/{id}/stream`.")
        col_a, col_b, _ = st.columns([1, 1, 2])
        with col_a:
            interval_s = st.number_input("Interval (sec)", min_value=2, max_value=60, value=10, key="ls_interval")
        with col_b:
            num_updates = st.number_input("Max Updates", min_value=1, max_value=20, value=6, key="ls_updates")

        if st.button("[>] Start Limited Stream", key="limited_btn", use_container_width=False):
            if not job_id:
                st.error("Enter a Job ID.")
            else:
                status_ph  = st.empty()
                details_ph = st.empty()
                log_ph     = st.empty()
                logs = []

                try:
                    with requests.get(
                        f"{BASE_URL}/research/jobs/{job_id}/stream",
                        params={"interval_seconds": interval_s, "num_updates": num_updates},
                        stream=True, timeout=300,
                    ) as resp:
                        for raw_line in resp.iter_lines():
                            if raw_line:
                                line = raw_line.decode("utf-8")
                                if line.startswith("data:"):
                                    try:
                                        payload = json.loads(line[5:].strip())
                                        status  = payload.get("status", "?")
                                        details = payload.get("state_details", {})
                                        ex      = details.get("execution_state", {}) if details else {}
                                        pct     = ex.get("progress_percent", 0)
                                        phase   = ex.get("phase", "-")
                                        node    = ex.get("possible_active_node_hint", "-")

                                        status_ph.markdown(
                                            f'{badge(status)}&nbsp;&nbsp;<span class="mono" style="font-size:0.72rem; color:#f7c26a;">{phase}</span>',
                                            unsafe_allow_html=True
                                        )
                                        try:
                                            pct_f = float(pct)
                                        except:
                                            pct_f = 0.0
                                        details_ph.markdown(f"""
<div style="background:#1a1a24; border-radius:4px; height:6px; overflow:hidden; margin:6px 0 10px;">
    <div style="width:{min(pct_f,100):.1f}%; height:100%; background:linear-gradient(90deg,#7c6af7,#6af7c2); border-radius:4px;"></div>
</div>""", unsafe_allow_html=True)

                                        dr = details.get("drafting_state", {}) if details else {}
                                        kn = details.get("knowledge_state", {}) if details else {}
                                        logs.insert(0,
                                            f"[{ts()}] {status.upper():12s} | {phase:20s} | "
                                            f"{pct_f:5.1f}% | raw={kn.get('raw_entries_collected',0)} "
                                            f"synth={kn.get('synthesized_entries',0)} | "
                                            f"sections={dr.get('completed_sections_count',0)} | "
                                            f"node={str(node)[:30]}"
                                        )
                                        log_ph.markdown(
                                            f'<div class="stream-box">{"<br>".join(logs[:20])}</div>',
                                            unsafe_allow_html=True
                                        )
                                        if status in ["complete", "failed"]:
                                            break
                                    except json.JSONDecodeError:
                                        pass
                except Exception as e:
                    st.error(f"Stream error: {e}")
                st.success("Stream ended.")

    # -- TAB 3: Live Feed ------------------------------------------------------
    with mode_tab3:
        st.caption("Continuous SSE from `/research/jobs/{id}/feed` -- runs until terminal state.")
        col_a, _ = st.columns([1, 3])
        with col_a:
            poll_interval = st.number_input("Poll Interval (sec)", min_value=2, max_value=30, value=5, key="lf_interval")

        if st.button("[>] Start Live Feed", key="feed_btn", use_container_width=False):
            if not job_id:
                st.error("Enter a Job ID.")
            else:
                status_ph  = st.empty()
                details_ph = st.empty()
                log_ph     = st.empty()
                logs = []

                try:
                    with requests.get(
                        f"{BASE_URL}/research/jobs/{job_id}/feed",
                        params={"interval": poll_interval},
                        stream=True, timeout=600,
                    ) as resp:
                        for raw_line in resp.iter_lines():
                            if raw_line:
                                line = raw_line.decode("utf-8")
                                if line.startswith("data:"):
                                    try:
                                        payload = json.loads(line[5:].strip())
                                        status  = payload.get("status", "?")
                                        details = payload.get("state_details", {})
                                        ex      = details.get("execution_state", {}) if details else {}
                                        kn      = details.get("knowledge_state", {}) if details else {}
                                        dr      = details.get("drafting_state", {}) if details else {}
                                        me      = details.get("memory_state", {}) if details else {}
                                        pct     = ex.get("progress_percent", 0)
                                        phase   = ex.get("phase", "-")
                                        node    = ex.get("possible_active_node_hint", "-")
                                        sect    = ex.get("section_tracker", {})

                                        try:
                                            pct_f = float(pct)
                                        except:
                                            pct_f = 0.0

                                        status_ph.markdown(f"""
<div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:6px;">
    {badge(status)}
    <span style="font-family:'Space Mono',monospace; font-size:0.72rem; color:#f7c26a;">{phase}</span>
    <span style="font-family:'Space Mono',monospace; font-size:0.72rem; color:#888899;">{pct_f:.0f}%</span>
    <span style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#7c6af7;">{str(node)[:35]}</span>
</div>
<div style="background:#1a1a24; border-radius:4px; height:6px; overflow:hidden; margin-bottom:8px;">
    <div style="width:{min(pct_f,100):.1f}%; height:100%; background:linear-gradient(90deg,#7c6af7,#6af7c2); border-radius:4px;"></div>
</div>""", unsafe_allow_html=True)

                                        details_ph.markdown(f"""
<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:8px; margin-bottom:8px;">
    <div style="background:#111118; border:1px solid #2a2a3a; border-radius:8px; padding:10px;">
        <div style="font-size:0.65rem; color:#888899; margin-bottom:4px;">SECTIONS</div>
        <div style="font-size:1.1rem; font-weight:800; color:#7c6af7;">{sect.get('current_index',-1)+1}<span style="font-size:0.75rem; color:#555566;">/{sect.get('total_sections',0)}</span></div>
    </div>
    <div style="background:#111118; border:1px solid #2a2a3a; border-radius:8px; padding:10px;">
        <div style="font-size:0.65rem; color:#888899; margin-bottom:4px;">RAW / SYNTH</div>
        <div style="font-size:1.1rem; font-weight:800; color:#6af7c2;">{kn.get('raw_entries_collected',0)}<span style="font-size:0.75rem; color:#555566;">/{kn.get('synthesized_entries',0)}</span></div>
    </div>
    <div style="background:#111118; border:1px solid #2a2a3a; border-radius:8px; padding:10px;">
        <div style="font-size:0.65rem; color:#888899; margin-bottom:4px;">COMPLETED</div>
        <div style="font-size:1.1rem; font-weight:800; color:#f7c26a;">{dr.get('completed_sections_count',0)}</div>
    </div>
    <div style="background:#111118; border:1px solid #2a2a3a; border-radius:8px; padding:10px;">
        <div style="font-size:0.65rem; color:#888899; margin-bottom:4px;">LOG / MSG</div>
        <div style="font-size:1.1rem; font-weight:800; color:#f7706a;">{me.get('global_log_size',0)}<span style="font-size:0.75rem; color:#555566;">/{me.get('messages_count',0)}</span></div>
    </div>
</div>
<div style="font-size:0.72rem; color:#888899; font-family:'Space Mono',monospace; margin-bottom:4px;">
    Next: <span style="color:#f7c26a;">{str(dr.get('next_target_heading','-'))[:60]}</span>
    &nbsp;|&nbsp; Output: <span style="color:{'#6af7a0' if me.get('has_final_output') else '#555566'};">{'Ready' if me.get('has_final_output') else 'Pending'}</span>
</div>""", unsafe_allow_html=True)

                                        logs.insert(0, f"[{ts()}] {status.upper()} | {phase} | {pct_f:.0f}%")
                                        log_ph.markdown(
                                            f'<div class="stream-box" style="max-height:160px;">{"<br>".join(logs[:30])}</div>',
                                            unsafe_allow_html=True
                                        )
                                        if status in ["complete", "failed"]:
                                            break
                                    except json.JSONDecodeError:
                                        pass
                except Exception as e:
                    st.error(f"Stream error: {e}")
                st.success("[OK] Feed ended.")

    # -- TAB 4: Events (Delta) -------------------------------------------------
    with mode_tab4:
        st.caption("SSE from `/research/jobs/stream/{id}/events` -- emits only on state changes.")
        col_a, _ = st.columns([1, 3])
        with col_a:
            evt_interval = st.number_input("Check Interval (sec)", min_value=3, max_value=30, value=3, key="evt_interval")

        if st.button("[!] Start Event Stream", key="events_btn", use_container_width=False):
            if not job_id:
                st.error("Enter a Job ID.")
            else:
                events_ph = st.empty()
                events = []

                try:
                    with requests.get(
                        f"{BASE_URL}/research/jobs/stream/{job_id}/events",
                        params={"interval": max(evt_interval, 3)},
                        stream=True, timeout=600,
                    ) as resp:
                        for raw_line in resp.iter_lines():
                            if raw_line:
                                line = raw_line.decode("utf-8")
                                if line.startswith("data:"):
                                    try:
                                        payload = json.loads(line[5:].strip())
                                        status  = payload.get("status", "?")
                                        details = payload.get("state_details", {})
                                        ex      = details.get("execution_state", {}) if details else {}
                                        kn      = details.get("knowledge_state", {}) if details else {}
                                        dr      = details.get("drafting_state", {}) if details else {}
                                        pct     = ex.get("progress_percent", 0)
                                        phase   = ex.get("phase", "-")
                                        node    = ex.get("possible_active_node_hint", "-")
                                        sect    = ex.get("section_tracker", {})
                                        try:
                                            pct_f = float(pct)
                                        except:
                                            pct_f = 0.0

                                        color = {"complete": "#6af7a0", "failed": "#f7706a", "in_progress": "#7c6af7"}.get(status, "#888899")
                                        event_html = f"""
<div style="border-left:2px solid {color}; padding:8px 12px; margin-bottom:10px; background:#0d0d15; border-radius:0 6px 6px 0;">
    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
        <span style="font-size:0.68rem; color:#555566; font-family:'Space Mono',monospace;">[{ts()}] STATE CHANGE</span>
        {badge(status)}
    </div>
    <div style="background:#1a1a24; border-radius:3px; height:4px; overflow:hidden; margin-bottom:6px;">
        <div style="width:{min(pct_f,100):.1f}%; height:100%; background:{color}; border-radius:3px;"></div>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; font-size:0.72rem;">
        <div><span style="color:#555566;">phase</span> <span style="color:#f7c26a;">{phase}</span></div>
        <div><span style="color:#555566;">progress</span> <span style="color:{color};">{pct_f:.0f}%</span></div>
        <div><span style="color:#555566;">sections</span> <span style="color:#e8e8f0;">{sect.get('current_index',-1)+1}/{sect.get('total_sections',0)}</span></div>
        <div><span style="color:#555566;">completed</span> <span style="color:#e8e8f0;">{dr.get('completed_sections_count',0)}</span></div>
        <div><span style="color:#555566;">raw/synth</span> <span style="color:#6af7c2;">{kn.get('raw_entries_collected',0)}/{kn.get('synthesized_entries',0)}</span></div>
        <div><span style="color:#555566;">node</span> <span style="color:#7c6af7; font-family:'Space Mono',monospace; font-size:0.68rem;">{str(node)[:25]}</span></div>
    </div>
    <div style="font-size:0.7rem; color:#888899; margin-top:4px; font-style:italic;">Next: {str(dr.get('next_target_heading','-'))[:55]}</div>
</div>"""
                                        events.insert(0, event_html)
                                        events_ph.markdown(
                                            f'<div class="stream-box" style="color:unset;">{"".join(events[:15])}</div>',
                                            unsafe_allow_html=True
                                        )
                                        if status in ["complete", "failed"]:
                                            break
                                    except json.JSONDecodeError:
                                        pass
                except Exception as e:
                    st.error(f"Stream error: {e}")
                st.success("[OK] Event stream ended.")


# ==============================================================================
# PAGE 3 -- JOBS DASHBOARD
# ==============================================================================
elif page == "[=] Jobs Dashboard":

    st.markdown("# Jobs Dashboard")
    st.markdown("### All active jobs and their current states")
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    hdr_col1, hdr_col2, hdr_col3 = st.columns([1, 1, 1])
    with hdr_col1:
        do_refresh = st.button("[~] Refresh", use_container_width=True)
    with hdr_col3:
        if st.button("[X] Clear All Jobs", use_container_width=True):
            result, err = api_post("/jobs/clear-all", {})
            if err:
                st.error(err)
            else:
                st.success("All jobs cleared.")
                if "enriched_jobs" in st.session_state:
                    del st.session_state["enriched_jobs"]

    # -- Fetch job list --------------------------------------------------------
    jobs_resp, fetch_err = api_get("/jobs/active")

    if fetch_err:
        st.error(fetch_err)
        st.stop()

    all_jobs = jobs_resp.get("all_current_jobs") if jobs_resp else None

    if not all_jobs:
        st.markdown("""
        <div class="card" style="text-align:center; padding:48px;">
            <div style="font-size:2.5rem; margin-bottom:10px; color:#2a2a3a;">[ ]</div>
            <div style="color:#888899; font-size:1rem;">No active jobs found.</div>
            <div style="color:#555566; font-size:0.8rem; margin-top:6px;">Start a new research job to see it here.</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # -- Metrics bar -----------------------------------------------------------
    statuses  = list(all_jobs.values())
    total     = len(statuses)
    complete  = sum(1 for s in statuses if s == "complete")
    running   = sum(1 for s in statuses if s in ("in_progress", "initiated", "initializing"))
    failed    = sum(1 for s in statuses if s in ("failed", "error"))

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric"><div class="metric-label">Total Jobs</div><div class="metric-value">{total}</div></div>
        <div class="metric"><div class="metric-label">Complete</div><div class="metric-value" style="color:var(--success)">{complete}</div></div>
        <div class="metric"><div class="metric-label">Running</div><div class="metric-value" style="color:var(--accent)">{running}</div></div>
        <div class="metric"><div class="metric-label">Failed</div><div class="metric-value" style="color:var(--danger)">{failed}</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # -- Enrich toggle ---------------------------------------------------------
    enrich = st.checkbox("Load full state details for each job (one API call per job)", value=False)

    if enrich or do_refresh:
        enriched = {}
        with st.spinner("Fetching job states..."):
            for jid in all_jobs:
                d, _ = api_get(f"/research/jobs/{jid}")
                if d:
                    enriched[jid] = d
        st.session_state["enriched_jobs"] = enriched

    enriched_jobs = st.session_state.get("enriched_jobs", {})

    # -- Jobs table ------------------------------------------------------------
    h0, h1, h2, h3, h4 = st.columns([3, 1.2, 1.8, 1, 2])
    h0.markdown('<span style="font-size:0.7rem; color:#888899; text-transform:uppercase; letter-spacing:1px; font-family:\'Space Mono\',monospace;">Job ID</span>', unsafe_allow_html=True)
    h1.markdown('<span style="font-size:0.7rem; color:#888899; text-transform:uppercase; letter-spacing:1px; font-family:\'Space Mono\',monospace;">Status</span>', unsafe_allow_html=True)
    h2.markdown('<span style="font-size:0.7rem; color:#888899; text-transform:uppercase; letter-spacing:1px; font-family:\'Space Mono\',monospace;">Phase</span>', unsafe_allow_html=True)
    h3.markdown('<span style="font-size:0.7rem; color:#888899; text-transform:uppercase; letter-spacing:1px; font-family:\'Space Mono\',monospace;">Progress</span>', unsafe_allow_html=True)
    h4.markdown('<span style="font-size:0.7rem; color:#888899; text-transform:uppercase; letter-spacing:1px; font-family:\'Space Mono\',monospace;">Active Node</span>', unsafe_allow_html=True)
    st.markdown('<hr style="margin:4px 0 2px; border-color:#2a2a3a;">', unsafe_allow_html=True)

    for jid, jstatus in all_jobs.items():
        enriched_row  = enriched_jobs.get(jid, {})
        actual_status = enriched_row.get("status", jstatus) if enriched_row else jstatus
        details       = enriched_row.get("state_details", {}) if enriched_row else {}
        exec_state    = details.get("execution_state", {}) if details else {}
        phase         = exec_state.get("phase", "-") or "-"
        pct           = exec_state.get("progress_percent", None)
        node          = exec_state.get("possible_active_node_hint", "-") or "-"

        try:
            pct_f = float(pct) if pct is not None else None
            pct_display = f"{pct_f:.0f}%" if pct_f is not None else "-"
        except (TypeError, ValueError):
            pct_f, pct_display = None, "-"

        c0, c1, c2, c3, c4 = st.columns([3, 1.2, 1.8, 1, 2])
        c0.markdown(f'<span style="font-family:\'Space Mono\',monospace; font-size:0.68rem; color:#7c6af7; word-break:break-all;">{jid}</span>', unsafe_allow_html=True)
        c1.markdown(badge(actual_status), unsafe_allow_html=True)
        c2.markdown(f'<span style="font-size:0.78rem; color:#e8e8f0;">{phase}</span>', unsafe_allow_html=True)
        if pct_f is not None:
            c3.markdown(f"""
<div style="font-size:0.72rem; color:#f7c26a; font-family:'Space Mono',monospace; margin-bottom:2px;">{pct_display}</div>
<div style="background:#1a1a24; border-radius:3px; height:4px; overflow:hidden;">
    <div style="width:{min(pct_f,100):.1f}%; height:100%; background:linear-gradient(90deg,#7c6af7,#6af7c2); border-radius:3px;"></div>
</div>""", unsafe_allow_html=True)
        else:
            c3.markdown('<span style="color:#555566; font-size:0.78rem;">-</span>', unsafe_allow_html=True)
        c4.markdown(f'<span style="font-family:\'Space Mono\',monospace; font-size:0.68rem; color:#888899;">{str(node)[:35]}</span>', unsafe_allow_html=True)

        st.markdown('<hr style="margin:3px 0; border-color:#1a1a24;">', unsafe_allow_html=True)

    # -- Drill-down panel ------------------------------------------------------
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("#### [>] Job Inspector")

    selected_job = st.selectbox(
        "Select a job",
        options=list(all_jobs.keys()),
        format_func=lambda x: f"{x[:30]}...  [{all_jobs.get(x,'?')}]",
        label_visibility="collapsed"
    )

    if selected_job:
        fetch_col, _ = st.columns([1, 3])
        with fetch_col:
            fetch_btn = st.button("[#] Fetch Full State", use_container_width=True, key="drill_fetch")

        if fetch_btn:
            drill_data, drill_err = api_get(f"/research/jobs/{selected_job}")
            if drill_err:
                st.error(drill_err)
            else:
                st.session_state["drill_data"]   = drill_data
                st.session_state["drill_job_id"] = selected_job

        drill     = st.session_state.get("drill_data")
        drill_jid = st.session_state.get("drill_job_id")

        if drill and drill_jid == selected_job:
            d_status  = drill.get("status", "unknown")
            d_details = drill.get("state_details")

            st.markdown(
                f'{badge(d_status)}&nbsp;&nbsp;<span class="mono" style="color:#888899; font-size:0.72rem;">{selected_job}</span>',
                unsafe_allow_html=True
            )
            st.markdown('<div style="margin-top:14px;"></div>', unsafe_allow_html=True)

            render_state_details(d_details)

            with st.expander("[+] Raw state_details JSON"):
                st.json(d_details or {})

            with st.expander("[=] Full raw state (/research/state)"):
                raw_data, raw_err = api_get(f"/research/state/{selected_job}")
                if raw_err:
                    st.error(raw_err)
                elif raw_data:
                    if raw_data.get("next_step"):
                        st.markdown(f'**Next Step:** `{raw_data["next_step"]}`')
                    st.json(raw_data.get("raw_state", {}))