"""CLOS Studio UI – Panel Badacza v0.4 (Read-Only)."""

import streamlit as st
import sys
import os
import json
import pandas as pd
sys.path.insert(0, os.getcwd())

from clos_studio.metadata_index import MetadataIndex
from clos_studio.artifacts.manager import ArtifactManager
from clos_studio.manifest.matrix_schema import MatrixManifest


# ============================================================
# KONFIGURACJA STRONY
# ============================================================
st.set_page_config(
    page_title="CLOS Studio",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 CLOS Studio – Panel Badacza")
st.caption("Read-Only – zero ingerencji w Core")

# ============================================================
# INICJALIZACJA POŁĄCZEŃ (READ-ONLY)
# ============================================================
@st.cache_resource
def get_metadata_index():
    idx = MetadataIndex()
    idx.connect()
    return idx

@st.cache_resource
def get_artifact_manager():
    return ArtifactManager()

idx = get_metadata_index()
am = get_artifact_manager()

# ============================================================
# ZAKŁADKI
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Eksperymenty",
    "🔬 Runy",
    "📦 Publikacje",
    "📋 Manifest"
])

# ============================================================
# ZAKŁADKA 1: EKSPERYMENTY
# ============================================================
with tab1:
    st.subheader("Wszystkie eksperymenty")

    experiments = idx.list_experiments()

    if not experiments:
        st.info("Brak eksperymentów w indeksie. Uruchom pierwszy eksperyment przez CLI.")
    else:
        # Tabela eksperymentów
        exp_data = []
        for exp in experiments:
            exp_id = exp["experiment_id"]
            statuses = idx.get_run_count_by_status(exp_id)
            completed = statuses.get("COMPLETE", 0)
            failed = statuses.get("FAILED", 0)
            total = sum(statuses.values())

            # Sprawdź integralność
            integrity = am.check_integrity(exp_id)
            manifest_ok = integrity.get("manifest") == "COMPLETE"

            exp_data.append({
                "Experiment ID": exp_id,
                "Workflow": exp.get("workflow_version", "N/A"),
                "Created": exp.get("created_at", "N/A")[:19] if exp.get("created_at") else "N/A",
                "Runs (OK/Fail)": f"{completed}/{total}" if total > 0 else "0/0",
                "Failed": failed,
                "Manifest": "✅" if manifest_ok else "❌",
            })

        df = pd.DataFrame(exp_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Wybór eksperymentu do szczegółów
        if experiments:
            exp_ids = [e["experiment_id"] for e in experiments]
            selected_exp = st.selectbox("Wybierz eksperyment", exp_ids)

            if selected_exp:
                col1, col2, col3, col4 = st.columns(4)
                statuses = idx.get_run_count_by_status(selected_exp)
                integrity = am.check_integrity(selected_exp)

                with col1:
                    st.metric("Runy COMPLETE", statuses.get("COMPLETE", 0))
                with col2:
                    st.metric("Runy FAILED", statuses.get("FAILED", 0))
                with col3:
                    st.metric("Manifest", "✅" if integrity.get("manifest") == "COMPLETE" else "❌")
                with col4:
                    total = sum(statuses.values())
                    st.metric("Razem runów", total)

                # Przycisk weryfikacji
                if st.button("🔍 Zweryfikuj eksperyment", type="primary"):
                    with st.spinner("Weryfikacja..."):
                        import subprocess
                        result = subprocess.run(
                            [sys.executable, "-m", "clos_cli", "verify-matrix", selected_exp],
                            capture_output=True, text=True, cwd=os.getcwd(),
                            env={**os.environ, "PYTHONPATH": os.getcwd()}
                        )
                        st.code(result.stdout, language="text")

# ============================================================
# ZAKŁADKA 2: RUNY
# ============================================================
with tab2:
    st.subheader("Szczegóły runów")

    experiments = idx.list_experiments()
    if experiments:
        exp_ids = [e["experiment_id"] for e in experiments]
        selected_exp = st.selectbox("Eksperyment", exp_ids, key="run_exp_select")

        if selected_exp:
            runs = idx.get_experiment_runs(selected_exp)

            if runs:
                run_data = []
                for run in runs:
                    run_data.append({
                        "Run ID": run["run_id"],
                        "Genome": run["genome"],
                        "Scenario": run["scenario"],
                        "Seed": run["seed"],
                        "Ticks": run["ticks"],
                        "Status": run["status"],
                        "Created": run.get("created_at", "N/A")[:19] if run.get("created_at") else "N/A",
                    })

                df = pd.DataFrame(run_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Filtrowanie
                status_filter = st.multiselect(
                    "Filtruj status",
                    ["COMPLETE", "FAILED", "TIMEOUT", "ERROR"],
                    default=["COMPLETE", "FAILED"]
                )
                genome_filter = st.multiselect(
                    "Filtruj genom",
                    list(set(r["genome"] for r in runs))
                )

                filtered = [
                    r for r in runs
                    if r["status"] in status_filter
                    and (not genome_filter or r["genome"] in genome_filter)
                ]

                st.metric("Widocznych runów", len(filtered))

                # Podgląd artefaktu
                if filtered:
                    run_ids = [r["run_id"] for r in filtered]
                    selected_run = st.selectbox("Podgląd artefaktu", run_ids)

                    if selected_run:
                        exp_dir = am.get_experiment_dir(selected_exp)
                        run_file = exp_dir / "runs" / f"{selected_run}.json"

                        if run_file.exists():
                            with open(run_file, "r", encoding="utf-8") as f:
                                artifact = json.load(f)
                            st.json(artifact)
                        else:
                            st.warning(f"Artefakt nie znaleziony: {run_file}")
            else:
                st.info("Brak runów dla tego eksperymentu.")
    else:
        st.info("Brak eksperymentów.")

# ============================================================
# ZAKŁADKA 3: PUBLIKACJE
# ============================================================
with tab3:
    st.subheader("Publikacje (Publication Bundles)")

    pub_dir = "publications"
    if os.path.exists(pub_dir):
        bundles = [
            d for d in os.listdir(pub_dir)
            if os.path.isdir(os.path.join(pub_dir, d)) and d.startswith("EXP-")
        ]

        if bundles:
            st.metric("Liczba publikacji", len(bundles))

            selected_bundle = st.selectbox("Wybierz publikację", sorted(bundles, reverse=True))

            if selected_bundle:
                bundle_path = os.path.join(pub_dir, selected_bundle)
                files = os.listdir(bundle_path)

                # Metadata
                metadata_path = os.path.join(bundle_path, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Runów", metadata.get("total_runs", "N/A"))
                    with col2:
                        st.metric("CLOS", f"v{metadata.get('clos_version', 'N/A')}")
                    with col3:
                        st.metric("Git", metadata.get("git_commit", "N/A")[:8] if metadata.get("git_commit") else "N/A")

                # Zawartość bundle
                st.write("**Zawartość paczki:**")
                for f in sorted(files):
                    if f.endswith(".json"):
                        st.write(f"📄 {f}")
                    elif os.path.isdir(os.path.join(bundle_path, f)):
                        st.write(f"📁 {f}/")
                    else:
                        st.write(f"📎 {f}")

                # Podgląd plików
                json_files = [f for f in sorted(files) if f.endswith(".json")]
                if json_files:
                    selected_file = st.selectbox("Podgląd pliku", json_files)
                    if selected_file:
                        file_path = os.path.join(bundle_path, selected_file)
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = json.load(f)
                        st.json(content)
        else:
            st.info("Brak publikacji. Uruchom matrix z publish_on_verify: true.")
    else:
        st.info("Katalog publications/ nie istnieje.")

# ============================================================
# ZAKŁADKA 4: MANIFEST
# ============================================================
with tab4:
    st.subheader("Podgląd manifestu")

    uploaded_file = st.file_uploader("Wgraj plik manifestu (.yaml)", type=["yaml", "yml"])

    if uploaded_file:
        import yaml
        manifest_dict = yaml.safe_load(uploaded_file.read())

        try:
            manifest = MatrixManifest.from_dict(manifest_dict)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ID", manifest.experiment_id)
            with col2:
                st.metric("Runów", manifest.get_total_runs())
            with col3:
                st.metric("Ticks", manifest.ticks)

            st.write("**Genomy:**", ", ".join(manifest.genomes))
            st.write("**Scenariusze:**", ", ".join(manifest.scenarios))
            st.write("**Seedy:**", manifest.seeds)

            st.divider()
            st.write("**Pełny manifest:**")
            st.json(manifest_dict)

        except Exception as e:
            st.error(f"Błąd parsowania manifestu: {e}")

    else:
        # Podgląd istniejącego manifestu
        experiments = idx.list_experiments()
        if experiments:
            exp_ids = [e["experiment_id"] for e in experiments]
            selected_exp = st.selectbox("Eksperyment", exp_ids, key="manifest_exp_select")

            if selected_exp:
                exp_dir = am.get_experiment_dir(selected_exp)
                manifest_file = exp_dir / "manifest.json"

                if manifest_file.exists():
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest_dict = json.load(f)
                    st.json(manifest_dict)
                else:
                    st.warning("Manifest nie znaleziony.")
        else:
            st.info("Wgraj plik .yaml lub uruchom eksperyment.")

# ============================================================
# STOPKA
# ============================================================
st.divider()
st.caption("CLOS Studio v0.4 – Read-Only Panel Badacza | Zero ingerencji w Core")
