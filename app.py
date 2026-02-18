import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("🧪 TEST DE CONNEXION DLABAL")

# Ton ID de Sheet
SHEET_ID = "1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s"

# Connexion
conn = st.connection("gsheets", type=GSheetsConnection)

st.write("Si tu vois ce message, le script est bien lancé sur GitHub.")

if st.button("🚀 CLIQUE ICI POUR TESTER L'ÉCRITURE"):
    try:
        # On crée une seule donnée très simple
        df_test = pd.DataFrame([{"TEST": "Connexion OK à 100%"}])
        
        # On essaie d'écrire dans un onglet appelé 'TEST_DLABAL'
        conn.update(spreadsheet=SHEET_ID, worksheet="TEST_DLABAL", data=df_test)
        
        st.success("✅ BRAVO ! L'ordre d'écriture a été envoyé.")
        st.balloons()
        st.info("Maintenant, regarde ton fichier Google Sheets. Un onglet 'TEST_DLABAL' doit être apparu.")
        
    except Exception as e:
        st.error(f"❌ L'ERREUR EST ICI : {e}")
