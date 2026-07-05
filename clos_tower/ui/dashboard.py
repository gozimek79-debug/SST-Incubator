"""CLOS Control Tower – Streamlit Dashboard v0.2."""

import streamlit as st
import sys
import os
sys.path.insert(0, os.getcwd())

from clos_tower.integration.cli_bridge import run_demo_full


def render():
    st.set_page_config(page_title="CLOS Control Tower", layout="wide")
    st.title("CLOS Control Tower v0.2")
    st.caption("Live Observability Layer – Read Only")

    col1, col2, col3 = st.columns(3)
    with col1:
        seed = st.number_input("Seed", value=42, min_value=0, max_value=9999)
    with col2:
        ticks = st.number_input("Ticks", value=100, min_value=10, max_value=2000)
    with col3:
        st.write("")
        st.write("")
        run_clicked = st.button("Run Demo", type="primary")

    if run_clicked:
        with st.spinner(f"Running demo (seed={seed}, ticks={ticks})..."):
            output = run_demo_full(seed=seed, ticks=ticks)
            st.success("Experiment complete!")
            st.code(output, language="text")

    st.divider()
    st.subheader("Live Stream")
    st.info("WebSocket stream available at ws://localhost:8000/stream/demo_shock")

    st.divider()
    st.subheader("Architecture")
    st.markdown("""
USER -> Control Tower (Streamlit)
|
v
FastAPI / WebSocket (read-only)
|
v
CLI subprocess (JSONL stream)
|
v
Kernel / Brain / World

text
""")


if __name__ == "__main__":
render()
