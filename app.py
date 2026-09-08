"""Streamlit UI for the Autonomous LinkedIn Content Manager."""

from __future__ import annotations

import streamlit as st

from linkedin_content_manager import STAGES, require_env, run_pipeline

st.set_page_config(page_title="LinkedIn Content Manager", page_icon="💼", layout="wide")

PIPELINE_CSS = """
<style>
  .pipeline { display:flex; align-items:flex-start; justify-content:space-between; gap:8px; margin: 8px 0 24px; }
  .stage-wrap { flex:1; text-align:center; position:relative; }
  .stage-wrap:not(:last-child)::after {
    content:""; position:absolute; top:22px; left:55%; right:-45%; height:3px;
    background:#d0d7de; z-index:0;
  }
  .stage-wrap.done:not(:last-child)::after { background:#0a66c2; }
  .stage-wrap.running:not(:last-child)::after {
    background: linear-gradient(90deg, #0a66c2 0%, #70b5f9 50%, #0a66c2 100%);
    background-size: 200% 100%;
    animation: flow 1.2s linear infinite;
  }
  .dot {
    width:44px; height:44px; border-radius:50%; margin:0 auto 8px; position:relative; z-index:1;
    display:flex; align-items:center; justify-content:center;
    font-weight:700; color:#fff; background:#8c8c8c; box-shadow: 0 0 0 4px #e8e8e8;
  }
  .stage-wrap.pending .dot { background:#b0b0b0; }
  .stage-wrap.running .dot {
    background:#0a66c2;
    animation: pulse 1.3s ease-in-out infinite;
  }
  .stage-wrap.done .dot { background:#057642; }
  .stage-wrap.error .dot { background:#cc1016; }
  .label { font-size:13px; font-weight:600; color:#191919; }
  .role { font-size:11px; color:#666; }
  .orbit {
    display:none; width:58px; height:58px; border-radius:50%;
    border:2px dashed #70b5f9; position:absolute; top:-7px; left:50%;
    margin-left:-29px; z-index:0;
  }
  .stage-wrap.running .orbit { display:block; animation: spin 2.4s linear infinite; }
  @keyframes pulse {
    0%,100% { transform:scale(1); box-shadow:0 0 0 4px #d0e8ff, 0 0 0 8px rgba(10,102,194,0.15); }
    50% { transform:scale(1.08); box-shadow:0 0 0 8px #d0e8ff, 0 0 16px 12px rgba(10,102,194,0.25); }
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes flow { 0% { background-position: 0% 0; } 100% { background-position: 200% 0; } }
  .dots { display:inline-flex; gap:6px; margin-left:8px; vertical-align:middle; }
  .dots span {
    width:8px; height:8px; border-radius:50%; background:#0a66c2;
    animation: bounce 0.9s infinite ease-in-out;
  }
  .dots span:nth-child(2) { animation-delay: 0.15s; }
  .dots span:nth-child(3) { animation-delay: 0.3s; }
  @keyframes bounce {
    0%,80%,100% { transform: translateY(0); opacity:.4; }
    40% { transform: translateY(-7px); opacity:1; }
  }
</style>
"""

ICONS = {
    "research": "1",
    "writing": "2",
    "critique": "3",
    "optimization": "4",
    "scheduling": "5",
}


def pipeline_html(status: dict[str, str], current_label: str | None = None) -> str:
    parts = [PIPELINE_CSS, '<div class="pipeline">']
    for key, label, role in STAGES:
        state = status.get(key, "pending")
        parts.append(
            f'<div class="stage-wrap {state}">'
            f'<div class="orbit"></div>'
            f'<div class="dot">{ICONS[key]}</div>'
            f'<div class="label">{label}</div>'
            f'<div class="role">{role}</div>'
            f"</div>"
        )
    parts.append("</div>")
    if current_label:
        parts.append(
            f'<p><strong>{current_label}</strong> in progress'
            f'<span class="dots"><span></span><span></span><span></span></span></p>'
        )
    return "".join(parts)


st.title("Autonomous LinkedIn Content Manager")
st.caption("Five CrewAI agents: research → write → critique → optimize → schedule. No Serper key required.")

with st.sidebar:
    st.header("Run settings")
    verbose = st.toggle("Verbose agent logs", value=True)
    st.markdown("Needs `OPENAI_API_KEY` in `.env`. Model defaults to `gpt-4o`.")

topic = st.text_input("Topic to search", placeholder="e.g. AI agents in enterprise software")
audience = st.text_input("Audience for the topic", placeholder="e.g. VP Engineering, CTOs, product leaders")
go = st.button("Generate LinkedIn post", type="primary", use_container_width=True)

pipe = st.empty()
status_box = st.empty()
stage_slots = {key: st.empty() for key, _, _ in STAGES}

if go:
    if not topic.strip() or not audience.strip():
        st.error("Enter both a topic and an audience.")
        st.stop()
    try:
        require_env()
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

    status = {key: "pending" for key, _, _ in STAGES}
    pipe.markdown(pipeline_html(status), unsafe_allow_html=True)

    def on_stage(event: str, key: str, payload):
        label = next(s[1] for s in STAGES if s[0] == key)
        if event == "start":
            status[key] = "running"
            pipe.markdown(pipeline_html(status, current_label=label), unsafe_allow_html=True)
            status_box.info(f"{label} agent is working…")
        elif event == "done":
            status[key] = "done"
            pipe.markdown(pipeline_html(status), unsafe_allow_html=True)
            with stage_slots[key].expander(f"{label} complete", expanded=(key == "scheduling")):
                st.markdown(payload["text"])
                if verbose and payload.get("logs"):
                    st.code(payload["logs"], language="text")

    try:
        results = run_pipeline(topic.strip(), audience.strip(), verbose=verbose, on_stage=on_stage)
        status_box.success("All five stages finished. Copy the scheduling brief into LinkedIn.")
        st.download_button(
            "Download publishing brief",
            results["scheduling"]["text"],
            file_name="linkedin_publishing_brief.txt",
        )
    except Exception as exc:
        running = next((k for k, v in status.items() if v == "running"), None)
        if running:
            status[running] = "error"
            pipe.markdown(pipeline_html(status), unsafe_allow_html=True)
        status_box.error(f"Crew run failed: {exc}")
else:
    pipe.markdown(pipeline_html({k: "pending" for k, _, _ in STAGES}), unsafe_allow_html=True)
