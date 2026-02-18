import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("🧪 TEST D'ACCÈS DIRECT")

# ON UTILISE L'URL COMPLETE CETTE FOIS
URL_COMPLETE = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    st.subheader("1. Tentative de lecture via URL")
    # On passe l'URL complète au lieu de l'ID
    data = conn.read(spreadsheet=URL_COMPLETE, ttl=0)
    st.success("✅ LECTURE RÉUSSIE !")
    st.dataframe(data)

    st.subheader("2. Tentative d'écriture")
    if st.button("🚀 TESTER L'ÉCRITURE SUR CETTE URL"):
        test_df = pd.DataFrame([{"TEST": "Ca marche enfin"}])
        conn.update(spreadsheet=URL_COMPLETE, data=test_df)
        st.balloons()
        st.success("Vérifie ton fichier !")

except Exception as e:
    st.error(f"ERREUR : {e}")
    st.info("Si l'erreur est encore 'SpreadsheetNotFound', c'est que l'email du Service Account n'a pas accès à ce lien précis.")
