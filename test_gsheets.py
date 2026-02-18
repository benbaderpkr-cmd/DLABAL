import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("🧪 Test Connexion Ultra-Simple")

# Ton ID de Sheet
SHEET_ID = "1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s"

# Connexion
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. Création d'une donnée de test unique
df_test = pd.DataFrame([{"TEST": "Ligne de test réussie !"}])

st.write("Tableau que l'on va essayer d'envoyer :")
st.table(df_test)

if st.button("🚀 LANCER LE TEST D'ÉCRITURE"):
    try:
        # On essaie d'écrire dans un NOUVEL onglet nommé "TEST_APP" 
        # pour ne pas polluer ton onglet "THO"
        conn.update(spreadsheet=SHEET_ID, worksheet="TEST_APP", data=df_test)
        
        st.success("✅ L'API Google a répondu 'Succès' !")
        st.balloons()
        st.info("Vérifie maintenant ton fichier Google Sheets : un nouvel onglet 'TEST_APP' a dû apparaître.")
        
    except Exception as e:
        st.error(f"❌ Erreur détectée : {e}")
