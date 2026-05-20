from __future__ import annotations

import pandas as pd
import streamlit as st

from jobs.pipeline import MCVDataPipeline


st.set_page_config(page_title="MCV Data Engine", layout="wide")
st.title("MCV Data Engine — Painel Operacional")
st.caption("Monitoramento interno de ingestão, qualidade, duplicados, snapshots e liquidez.")

uploaded = st.file_uploader("Importar CSV/JSON de anúncios", type=["csv", "json"])
persist = st.checkbox("Persistir no banco", value=False)

if uploaded and st.button("Processar arquivo"):
    suffix = ".csv" if uploaded.name.endswith(".csv") else ".json"
    tmp_path = f"/tmp/mcv_data_engine_upload{suffix}"
    with open(tmp_path, "wb") as fh:
        fh.write(uploaded.getbuffer())
    result = MCVDataPipeline().run_import(tmp_path, persist=persist)
    st.success("Processamento concluído")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros recebidos", result["received"])
    c2.metric("Registros limpos", result["clean_records"])
    c3.metric("Duplicados", result["duplicates"])
    c4.metric("Qualidade média", result["avg_quality"])
    st.json(result["exports"])
else:
    st.info("Envie um arquivo para processar ou use a API FastAPI.")
