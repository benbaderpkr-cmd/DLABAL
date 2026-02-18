import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("🧪 DIAGNOSTIC DE CONNEXION")

SHEET_ID = "1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s"

# Tentative de connexion
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 1. TEST DE LECTURE BRUTE
    st.subheader("1. Test de lecture")
    # On essaie de lire sans aucun paramètre pour voir si la connexion de base répond
    data = conn.read(spreadsheet=SHEET_ID, ttl=0)
    st.write("Données reçues :")
    st.dataframe(data)
    
except Exception as e:
    st.error(f"Erreur lors du test : {e}")
    st.write("Type de l'erreur :", type(e))

# 2. TEST D'ÉCRITURE FORCÉE
st.subheader("2. Test d'écriture")
if st.button("🚀 FORCER L'ÉCRITURE"):
    try:
        test_df = pd.DataFrame([{"TEST": "Ligne de test"}])
        # On utilise une syntaxe différente pour voir si ça débloque la situation
        conn.update(spreadsheet=SHEET_ID, data=test_df)
        st.success("✅ Commande envoyée !")
    except Exception as e:
        st.error(f"Erreur d'écriture : {e}")

st.divider()
st.info("Note : Si l'erreur est encore <Response [200]>, cela signifie que la bibliothèque reçoit un succès mais ne sait pas l'afficher.")
