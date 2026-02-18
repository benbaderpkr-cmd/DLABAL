import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("🧪 TEST DE CONNEXION DLABAL")

SHEET_ID = "1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s"
# On change juste ici pour forcer une connexion "fraîche"
conn = st.connection("gsheets", type=GSheetsConnection)

if st.button("🚀 CLIQUE ICI POUR TESTER L'ÉCRITURE"):
    try:
        df_test = pd.DataFrame([{"TEST": "Connexion OK"}])
        
        # CHANGEMENT ICI : On utilise une méthode plus "brute"
        # On essaie d'écrire sans préciser d'onglet pour voir s'il crée 'Sheet1'
        conn.update(spreadsheet=SHEET_ID, data=df_test)
        
        st.success("✅ Code 200 reçu !")
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ ERREUR : {e}")

# AJOUT DE CE BLOC POUR VOIR SI LA LECTURE MARCHE
st.subheader("Lecture du fichier actuel :")
try:
    df_lecture = conn.read(spreadsheet=SHEET_ID)
    st.write("Voici ce que l'appli voit dans ton fichier :")
    st.dataframe(df_lecture)
except Exception as e:
    st.error(f"Impossible de lire : {e}")
