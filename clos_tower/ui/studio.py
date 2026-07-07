"""CLOS Studio UI v0.7.2 – z Control Tower."""

import streamlit as st
import streamlit.components.v1 as components
import sys, os, json, pandas as pd
sys.path.insert(0, os.getcwd())

from clos_studio.metadata_index import MetadataIndex
from clos_studio.artifacts.manager import ArtifactManager

st.set_page_config(page_title="CLOS Studio", page_icon="🧠", layout="wide")
st.title("🧠 CLOS Studio – Panel Badacza")
st.caption("Read-Only – zero ingerencji w Core")

@st.cache_resource
def get_mi(): idx = MetadataIndex(); idx.connect(); return idx
@st.cache_resource
def get_am(): return ArtifactManager()

idx = get_mi(); am = get_am()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Eksperymenty", "🔬 Runy", "📦 Publikacje", "📋 Manifest", "🏗️ Control Tower"])

with tab1:
    st.subheader("Wszystkie eksperymenty")
    experiments = idx.list_experiments()
    if not experiments:
        st.info("Brak eksperymentow. Uruchom: python -m clos_cli run-matrix experiment.yaml")
    else:
        exp_data = []
        for exp in experiments:
            eid = exp["experiment_id"]
            statuses = idx.get_run_count_by_status(eid)
            exp_data.append({
                "Experiment ID": eid, "Workflow": exp.get("workflow_version","N/A"),
                "Created": str(exp.get("created_at",""))[:19],
                "COMPLETE": statuses.get("COMPLETE",0), "FAILED": statuses.get("FAILED",0),
                "Total": sum(statuses.values())
            })
        st.dataframe(pd.DataFrame(exp_data), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Szczegoly runow")
    experiments = idx.list_experiments()
    if experiments:
        eids = [e["experiment_id"] for e in experiments]
        sel = st.selectbox("Eksperyment", eids, key="run_sel")
        if sel:
            runs = idx.get_experiment_runs(sel)
            if runs:
                st.dataframe(pd.DataFrame([{
                    "Run ID": r["run_id"], "Genome": r["genome"], "Scenario": r["scenario"],
                    "Seed": r["seed"], "Ticks": r["ticks"], "Status": r["status"]
                } for r in runs]), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Publikacje")
    pub_dir = "publications"
    if os.path.exists(pub_dir):
        bundles = [d for d in os.listdir(pub_dir) if os.path.isdir(os.path.join(pub_dir,d)) and d.startswith("EXP-")]
        if bundles:
            sel = st.selectbox("Publikacja", sorted(bundles, reverse=True))
            if sel:
                mp = os.path.join(pub_dir, sel, "metadata.json")
                if os.path.exists(mp):
                    with open(mp,"r") as f: st.json(json.load(f))
        else: st.info("Brak publikacji")
    else: st.info("Katalog publications/ nie istnieje")

with tab4:
    st.subheader("Podglad manifestu")
    experiments = idx.list_experiments()
    if experiments:
        sel = st.selectbox("Eksperyment", [e["experiment_id"] for e in experiments], key="man_sel")
        if sel:
            mf = am.get_experiment_dir(sel) / "manifest.json"
            if mf.exists():
                with open(mf,"r") as f: st.json(json.load(f))
            else: st.warning("Manifest nie znaleziony")

with tab5:
    st.subheader("🏗️ Control Tower")
    st.caption("Live view – dane z EXP-89D9BA69")
    with open("clos_tower/static/control_tower.html","r",encoding="utf-8") as f:
        components.html(f.read(), height=800, scrolling=True)

st.divider()
st.caption("CLOS Studio v0.7.2 – Read-Only")
