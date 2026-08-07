"""
Streamlit dashboard — talks to the FastAPI backend (backend/api.py) rather
than running detection itself, so this stays a thin UI layer.

Run with:
    streamlit run dashboard/app.py

Requires the backend to already be running (python -m uvicorn backend.api:app).
"""

import time

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API = "http://localhost:8000"

st.set_page_config(page_title="AI Traffic Signal Controller", page_icon="🚦", layout="wide")

SIGNAL_COLORS = {"RED": "#E5484D", "YELLOW": "#F5A524", "GREEN": "#2FB344"}
DENSITY_COLORS = {"LOW": "#2FB344", "MEDIUM": "#F5A524", "HIGH": "#E5484D", "EMERGENCY": "#8B5CF6"}


def api_get(path, timeout=2):
    try:
        r = requests.get(f"{API}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


def signal_light(active):
    circles = ""
    for light in ["RED", "YELLOW", "GREEN"]:
        color = SIGNAL_COLORS[light] if light == active else "#2A2A2A"
        glow = f"box-shadow: 0 0 16px {color};" if light == active else ""
        circles += (
            f'<div style="width:34px;height:34px;border-radius:50%;'
            f'background:{color};margin:5px auto;{glow}"></div>'
        )
    st.markdown(
        f'<div style="background:#111;border-radius:12px;padding:8px 14px;'
        f'width:60px;margin:auto;">{circles}</div>',
        unsafe_allow_html=True,
    )


st.title("AI-Based Traffic Signal Controller")
st.caption(f"Live dashboard — backend API at {API}")

with st.sidebar:
    st.header("Pipeline control")
    source = st.text_input("Video source", value="0",
                            help="0 = webcam, or a video file path / rtsp:// URL")
    lane_id = st.text_input("Lane ID", value="north")
    c1, c2 = st.columns(2)
    start_clicked = c1.button("▶ Start Pipeline", type="primary")
    stop_clicked = c2.button("⏹ Stop")
    refresh_rate = st.slider("Refresh every (s)", 0.5, 5.0, 1.0, step=0.5)

    st.markdown("---")
    health = api_get("/health")
    if health:
        st.markdown("Backend: 🟢 online")
    else:
        st.markdown("Backend: 🔴 unreachable")
        st.caption("Start it with: `python -m uvicorn backend.api:app --reload`")

if start_clicked:
    try:
        resp = requests.post(f"{API}/pipeline/start",
                              json={"source": source, "lane_id": lane_id}, timeout=5)
        st.success("Pipeline started") if resp.ok else st.error(resp.json().get("detail", "Failed to start"))
    except requests.RequestException as e:
        st.error(f"Could not reach backend: {e}")

if stop_clicked:
    try:
        resp = requests.post(f"{API}/pipeline/stop", timeout=5)
        st.success("Pipeline stopped") if resp.ok else st.error(resp.json().get("detail", "Failed to stop"))
    except requests.RequestException as e:
        st.error(f"Could not reach backend: {e}")

status = api_get("/status")

if status and status.get("running"):
    top = st.columns([1, 1.4, 1, 1, 1])

    with top[0]:
        st.markdown("**Signal**")
        signal_light(status["signal_phase"])

    with top[1]:
        st.markdown("**Live view**")
        frame_bytes = None
        try:
            r = requests.get(f"{API}/frame", timeout=2)
            if r.ok:
                frame_bytes = r.content
        except requests.RequestException:
            pass
        st.image(frame_bytes, use_container_width=True) if frame_bytes else st.info("Waiting for frames...")

    with top[2]:
        st.markdown("**Density**")
        density = status["density"]
        color = DENSITY_COLORS.get(density, "#888")
        st.markdown(
            f'<div style="background:{color};color:white;padding:4px 14px;'
            f'border-radius:20px;font-weight:600;display:inline-block;">{density}</div>',
            unsafe_allow_html=True,
        )

    top[3].metric("Green time", f"{status['green_time_s']}s")
    top[4].metric("Phase remaining", f"{status['signal_remaining']}s")

    if status.get("emergency"):
        st.error("🚨 EMERGENCY vehicle flagged — signal jumping to immediate green")

    st.markdown("---")
    m = st.columns(4)
    counts = status.get("counts", {})
    m[0].metric("Total vehicles (last sample)", status["total_vehicles"])
    m[1].metric("Cars", counts.get("car", 0))
    m[2].metric("Bikes", counts.get("bike", 0))
    m[3].metric("Buses/Trucks", counts.get("bus", 0) + counts.get("truck", 0))

    metrics = api_get("/metrics")
    history = metrics.get("history", []) if metrics else []
    if history:
        df = pd.DataFrame(history)
        df["time"] = pd.to_datetime(df["t"], unit="s")
        counts_df = pd.json_normalize(df["counts"])
        counts_df["time"] = df["time"]

        st.markdown("---")
        c1, c2 = st.columns(2)
        present_cols = [c for c in ["car", "bike", "bus", "truck"] if c in counts_df.columns]
        if present_cols:
            fig1 = px.bar(counts_df, x="time", y=present_cols,
                          title="Vehicle counts over time", barmode="stack")
            c1.plotly_chart(fig1, use_container_width=True)
        fig2 = px.line(df, x="time", y="green_time_s", markers=True,
                        title="Green time decisions", color_discrete_sequence=["#2FB344"])
        c2.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.subheader("Recent history")
        st.dataframe(
            df[["time", "total_vehicles", "density", "emergency", "green_time_s"]],
            use_container_width=True, height=240,
        )
else:
    st.info("Pipeline is not running. Set a video source in the sidebar and click **Start Pipeline**.")

if status and status.get("running"):
    time.sleep(refresh_rate)
    st.rerun()
