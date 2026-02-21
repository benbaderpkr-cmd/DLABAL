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

if not check_password():
    st.stop()

# ==========================================
# 2. CHARGEMENT DES DONNÉES
# ==========================================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1vCshN5YhA1i_k-D_3m_i76mD-x6mXw8YF0X9Z8Z9Z8Z/edit#gid=0"

@st.cache_data
def load_data():
    # Gestion robuste des noms de fichiers pour éviter le FileNotFoundError
    jmf_path = 'jmf (4).json' if os.path.exists('jmf (4).json') else 'jmf.json'
    ferti_path = 'calcul_ferti.json'
    
    if not os.path.exists(jmf_path):
        st.error(f"Fichier de données introuvable : {jmf_path}")
        st.stop()
        
    with open(jmf_path, 'r', encoding='utf-8') as f:
        jmf = json.load(f)
        
    if os.path.exists(ferti_path):
        with open(ferti_path, 'r', encoding='utf-8') as f:
            ferti = json.load(f)
    else:
        ferti = {} # Evite le plantage si calcul_ferti.json n'est pas encore sur le serveur
        
    return jmf, ferti

data, ferti_db = load_data()

# ==========================================
# 3. NAVIGATION SIDEBAR
# ==========================================
st.sidebar.image("https://via.placeholder.com/150?text=DLABAL+LOGO", use_column_width=True)
menu = st.sidebar.radio("Navigation", ["🏠 Accueil", "📖 ITK Légumes", "📝 Formulaire THO", "📟 CALCULATEUR FERTI"])

# ==========================================
# 4. LOGIQUE DES PAGES
# ==========================================

# --- CAS : ITK LÉGUMES ---
if menu == "📖 ITK Légumes":
    st.title("📖 Itinéraires Techniques")
    sel = st.selectbox("Choisir un légume :", options=list(data.keys()))
    if sel:
        leg = data[sel]
        tabs = st.tabs(["🌱 Culture", "🛠️ Entretien", "🏥 Santé", "📊 Récolte"])
        with tabs[0]:
            st.write(leg.get("CULTIVARS", "N/A"))
            st.write(leg.get("ESPACEMENT INTENSIF", "N/A"))
        with tabs[1]:
            st.write(leg.get("FERTILISATION", "N/A"))
            st.write(leg.get("TYPE D'IRRIGATION", "N/A"))
        with tabs[2]:
            st.write(leg.get("PHYTOPROTECTION", "N/A"))
        with tabs[3]:
            st.write(leg.get("RÉCOLTE", "N/A"))

# --- CAS : FORMULAIRE THO ---
elif menu == "📝 Formulaire THO":
    st.title("📝 Suivi THO (Tableau de Bord)")
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO")
    
    sel = st.selectbox("Sélectionner un légume pour THO :", options=list(data.keys()))
    if sel:
        with st.form("tho_form"):
            notes = df_gs[df_gs['LEGUME'] == sel].to_dict('records')
            notes = notes[0] if notes else {}
            
            c1, c2 = st.columns(2)
            v_p = c1.text_area("🌱 PLANTATION", value=str(notes.get("PLANTATION", "")))
            v_e = c1.text_area("🛠️ ENTRETIEN", value=str(notes.get("ENTRETIEN", "")))
            v_s = c1.text_area("🏥 SANTE", value=str(notes.get("SANTE", "")))
            v_r = c2.text_area("📊 RENDEMENT", value=str(notes.get("RENDEMENT", "")))
            v_v = c2.text_area("🧬 VARIETE", value=str(notes.get("VARIETE", "")))
            v_i = c2.text_area("➕ INFO SUPP", value=str(notes.get("INFO_SUPP", "")))
            
            if st.form_submit_button("💾 ENREGISTRER"):
                new_row = {"LEGUME": sel, "PLANTATION": v_p, "ENTRETIEN": v_e, "SANTE": v_s, "RENDEMENT": v_r, "VARIETE": v_v, "INFO_SUPP": v_i}
                df_final = pd.concat([df_gs[df_gs['LEGUME'] != sel], pd.DataFrame([new_row])], ignore_index=True)
                conn.update(spreadsheet=URL_SHEET, worksheet="THO", data=df_final)
                st.success("Données THO enregistrées !")

# --- CAS : CALCULATEUR FERTI ---
elif menu == "📟 CALCULATEUR FERTI":
    st.title("📟 Calculateur de Besoins N-P-K")
    if not ferti_db:
        st.error("Le fichier `calcul_ferti.json` est manquant sur le serveur.")
    else:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                longueur = st.number_input("Longueur de la planche (m)", min_value=0.0, value=20.0, step=0.5)
            with c2:
                largeur = st.number_input("Largeur de la planche (m)", min_value=0.0, value=0.75, step=0.05)
            
            surface = longueur * largeur
            st.write(f"📏 **Surface calculée : {surface:.2f} m²**")
            
            legume_list = sorted(list(ferti_db.keys()))
            legume = st.selectbox("Choisir le légume :", options=legume_list)
            
            if legume:
                # Extraction des données JDV depuis le JSON
                source_data = ferti_db[legume].get("JDV")
                if source_data:
                    n_f = (source_data['N'] / 10000) * surface
                    p_f = (source_data['P'] / 10000) * surface
                    k_f = (source_data['K'] / 10000) * surface
                    
                    st.divider()
                    res1, res2, res3 = st.columns(3)
                    res1.metric("Azote (N)", f"{n_f:.3f} u")
                    res2.metric("Phosphore (P)", f"{p_f:.3f} u")
                    res3.metric("Potassium (K)", f"{k_f:.3f} u")
                    st.caption(f"Référentiel : {source_data['N']}N / {source_data['P']}P / {source_data['K']}K par ha")
                else:
                    st.warning("Données JDV absentes pour ce légume.")

# --- CAS : ACCUEIL ---
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.write("Sélectionnez un onglet dans le menu à gauche pour commencer.")
