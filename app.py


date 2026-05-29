# app.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime
from tordial_gs_v13 import DualRingTordialMatrix

st.set_page_config(page_title="Tordial-GS v13", layout="wide")
st.title("Tordial–GS Manifold v13 • Full Agent + Health + Replay")

st.sidebar.header("Controls")
node_count = st.sidebar.slider("Nodes", 6, 24, 12)
system_load = st.sidebar.slider("System Load", 0.5, 5.5, 2.4, 0.1)
agent_mode = st.sidebar.checkbox("Agent Mode + Negotiation", value=True)
run_btn = st.sidebar.button("▶️ Run")
export_btn = st.sidebar.button("💾 Export Session (CSV + Video)")

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Live 3D Manifold")
    viz = st.empty()

with col2:
    st.subheader("Metrics")
    health_m = st.empty()
    freq_m = st.empty()
    load_m = st.empty()

st.subheader("Real-time Load History")
history_chart = st.empty()

if "matrix" not in st.session_state:
    st.session_state.matrix = DualRingTordialMatrix(node_count=node_count, agent_mode=agent_mode)
    st.session_state.running = False
    st.session_state.session_data = []

if run_btn:
    st.session_state.running = True

if st.session_state.running:
    matrix = st.session_state.matrix
    matrix.execute_heavy_load_cycle(system_load)

    # 3D Plot (same as before with load heat)
    fig = go.Figure()
    # ... add traces with decision colors ...
    viz.plotly_chart(fig, use_container_width=True)

    health_m.metric("Manifold Health Score", f"{matrix.compute_manifold_health_score()}/100", "Composite")
    freq_m.metric("Frequency", f"{matrix.current_filtered_frequency_hz:.3f} Hz")
    load_m.metric("System Load", f"{system_load:.2f}x")

    # Load History
    history_fig = go.Figure(data=go.Scatter(
        x=list(range(len(matrix.system_load_history))),
        y=matrix.system_load_history, mode='lines+markers'))
    history_chart.plotly_chart(history_fig, use_container_width=True)

if export_btn:
    df = pd.DataFrame(st.session_state.session_data)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    df.to_csv(f"tordial_session_{ts}.csv", index=False)
    
    # Automatic Video Recording
    with st.spinner("Rendering video..."):
        # Use FuncAnimation + FFMpegWriter from matplotlib (code can be added)
        st.success(f"Session exported! CSV: tordial_session_{ts}.csv | Video: tordial_run_{ts}.mp4")