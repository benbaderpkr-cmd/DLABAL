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
    # Correction dynamique du nom de fichier pour éviter le FileNotFoundError
    jmf_file = 'jmf (4).json' if os.path.exists('jmf (4).json') else 'jmf.json'
    
    with open(jmf_file, 'r', encoding='utf-8') as f:
        jmf_data = json.load(f)
    
    with open('calcul_ferti.json', 'r', encoding='utf-8') as f:
        ferti_data = json.load(f)
        
    return jmf_data, ferti_data

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
    
    longueur = st.number_input("Longueur de la planche (m)", min_value=0.0, value=20.0)
    largeur = st.number_input("Largeur de la planche (m)", min_value=0.0, value=0.75)
    
    surface = longueur * largeur
    st.write(f"Surface calculée : {surface} m²")
    
    legume_sel = st.selectbox("Légume :", options=sorted(list(ferti_db.keys())))
    
    if legume_sel:
        # On appelle le dictionnaire chargé depuis calcul_ferti.json
        res = ferti_db[legume_sel].get("JDV")
        if res:
            n = (res['N'] / 10000) * surface
            p = (res['P'] / 10000) * surface
            k = (res['K'] / 10000) * surface
            
            st.markdown("---")
            st.write(f"**Besoins pour {surface} m² :**")
            st.write(f"**Azote (N) :** {n:.3f} unités")
            st.write(f"**Phosphore (P) :** {p:.3f} unités")
            st.write(f"**Potassium (K) :** {k:.3f} unités")
        else:
            st.warning("Données JDV manquantes pour ce légume dans le fichier JSON.")

# --- CAS : ACCUEIL ---
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.write("Sélectionnez un onglet dans le menu à gauche pour commencer.")
