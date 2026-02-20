import streamlit as st
import json
import os
import pandas as pd
import requests
import unicodedata
import streamlit.components.v1 as components
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_cookies_manager import EncryptedCookieManager

# ==========================================
# 1. CONFIGURATION ET SECURITE
# ==========================================
st.set_page_config(page_title="DLABAL - BDD ITK Maraîchage", layout="wide", page_icon="🌱")

cookies = EncryptedCookieManager(password="cle_secrete_dlabal_2026")
if not cookies.ready():
    st.stop()

def check_password():
    if st.session_state.get("password_correct") or cookies.get("auth_token") == "valide":
        st.session_state["password_correct"] = True
        return True
    st.title("🔐 Accès Restreint")
    with st.form("auth_form", clear_on_submit=False):
        pwd = st.text_input("Mot de passe DLABAL :", type="password")
        if st.form_submit_button("Valider"):
            if pwd == st.secrets["password"]:
                st.session_state["password_correct"] = True
                cookies["auth_token"] = "valide"
                cookies.save()
                st.rerun()
            else:
                st.error("Incorrect")
    return False

# --- AJOUT FONCTION LECTURE JSON ---
def load_itab_data():
    if os.path.exists("itab.json"):
        with open("itab.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return None

if not check_password():
    st.stop()

# ==========================================
# 2. CONNEXION GSHEETS (Lignes Originales)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
URL_SHEET = st.secrets["gsheets"]["spreadsheet"]

# ==========================================
# 3. BARRE LATERALE ET SELECTION
# ==========================================
with st.sidebar:
    st.title("Menu DLABAL")
    
    df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO")
    liste_legumes = sorted(df_gs['LEGUME'].dropna().unique().tolist())
    
    sel = st.selectbox("Choisir un légume :", [""] + liste_legumes)

# ==========================================
# 4. AFFICHAGE DES ONGLETS
# ==========================================
if sel:
    st.title(f"🥕 Fiche Technique : {sel}")
    
    # AJOUT "ITAB" DANS LA LISTE
    tabs = st.tabs(["GAB", "JMF", "JDV", "ITAB", "THO"])

    # --- CAS 1 : GAB ---
    with tabs[0]:
        st.info("Données en cours de synchronisation avec le GAB...")

    # --- CAS 2 : JMF ---
    with tabs[1]:
        st.info("Référentiel Jean-Martin Fortier...")

    # --- CAS 3 : JDV ---
    with tabs[2]:
        st.info("Données Jardin du Vernois...")

    # --- NOUVEL ONGLET : ITAB ---
    with tabs[3]:
        st.subheader(f"📚 Expertise ITAB : {sel}")
        itab_data = load_itab_data()
        if itab_data and sel.upper() in itab_data:
            data = itab_data[sel.upper()]
            st.json(data)
        else:
            st.warning("Aucune donnée ITAB disponible dans itab.json")

    # --- CAS 4 : THO (Ton code original) ---
    with tabs[4]:
        st.header("📝 Saisie Terrain (THO)")
        row = df_gs[df_gs['LEGUME'] == sel].iloc[0]
        
        with st.form("tho_form"):
            v_p = st.text_area("Plantation :", value=row.get('PLANTATION', ""))
            v_e = st.text_area("Entretien :", value=row.get('ENTRETIEN', ""))
            v_s = st.text_area("Santé :", value=row.get('SANTE', ""))
            v_r = st.text_area("Rendement :", value=row.get('RENDEMENT', ""))
            v_v = st.text_area("Variétés :", value=row.get('VARIETE', ""))
            v_i = st.text_area("Infos Supp :", value=row.get('INFO_SUPP', ""))
            
            if st.form_submit_button("💾 Enregistrer les modifications"):
                new_row = {"LEGUME": sel, "PLANTATION": v_p, "ENTRETIEN": v_e, "SANTE": v_s, "RENDEMENT": v_r, "VARIETE": v_v, "INFO_SUPP": v_i}
                df_final = pd.concat([df_gs[df_gs['LEGUME'] != sel], pd.DataFrame([new_row])], ignore_index=True)
                conn.update(spreadsheet=URL_SHEET, worksheet="THO", data=df_final)
                st.success("Données THO enregistrées !")

# --- CAS 3 : PAGE D'ACCUEIL ---
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.markdown("---")
    st.markdown("""
    ### DLABAL - BDD ITK Maraîchage
    
    Cet outil centralise les connaissances techniques du **GAB**, de **JMF**, de **JDV** et de l'**ITAB**.
    
    **Comment utiliser l'application :**
    1. **Sélectionnez ou taper le nom d'un légume** dans le menu déroulant à gauche.
    2. **Consultez les fiches** via les onglets thématiques.
    3. **Contribuez** en cliquant sur l'icône 📝 pour suggérer une correction.
    4. **Saisie Terrain** : Utilisez l'onglet **THO** pour enregistrer vos observations en direct.
    
    ---
    *Toutes les modifications de données textuelles sont soumises à validation.*
    """)
    st.info("👈 Commencez par choisir un légume dans le menu à gauche pour afficher ses données.")
