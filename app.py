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
import re

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
# 2. FONCTIONS DE CHARGEMENT
# ==========================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def page_calcul_ferti():
    st.title("📊 CALCUL FERTILISATION")
    ferti_data = load_json('calcul_ferti.json')
    if not ferti_data:
        st.error("Fichier 'calcul_ferti.json' introuvable.")
        return
    legume_sel = st.selectbox("Légume :", list(ferti_data.keys()))
    c1, c2 = st.columns(2)
    long = c1.number_input("Longueur (m)", value=10.0)
    larg = c2.number_input("Largeur (m)", value=0.75)
    surf = long * larg
    st.write(f"**Surface : {surf:.2f} m²**")
    e_n = st.number_input("N de votre engrais (%)", value=6.0)
    txt = ferti_data[legume_sel].get("FERTILISATION", "")
    match = re.search(r"(\d+)\s*kg\s*N", txt)
    if match:
        besoin_n = int(match.group(1))
        st.info(f"Besoin JMF : {besoin_n} kg N/ha")
        apport = (besoin_n / 10000) * surf / (e_n / 100)
        st.success(f"Apport : **{apport:.2f} kg**")
    else:
        st.warning("Pas de valeur chiffrée N trouvée.")
        st.write(txt)

# ==========================================
# 3. INTERFACE PRINCIPALE (SIDEBAR)
# ==========================================
jmf_data = load_json('jmf.json')
itab_data = load_json('itab.json')

with st.sidebar:
    st.image("https://img.icons8.com/color/96/sprout.png", width=80)
    st.title("DLABAL")
    
    tous_les_legumes = sorted(list(set(list(jmf_data.keys()) + list(itab_data.keys()))))
    sel = st.selectbox("🔍 Rechercher un légume :", [""] + tous_les_legumes)
    
    if sel:
        st.session_state["page_actuelle"] = "fiche"

    st.markdown("---")
    st.subheader("⚙️ REGLAGES JP1 TERRADONIS")
    if st.button("CALIBRE SEMENCE", use_container_width=True):
        st.info("Réglages Calibres...")
    if st.button("PIGNONS/DISQUES", use_container_width=True):
        st.info("Réglages Pignons...")
    
    # UPDATE : AJOUT DU BOUTON
    if st.button("📊 CALCUL FERTILISATION", use_container_width=True):
        st.session_state["page_actuelle"] = "calcul_ferti"
        st.rerun()

# ==========================================
# 4. LOGIQUE D'AFFICHAGE
# ==========================================

if st.session_state.get("page_actuelle") == "calcul_ferti":
    page_calcul_ferti()

elif sel:
    st.title(f"🌿 {sel.upper()}")
    tab1, tab2, tab3 = st.tabs(["📘 JMF", "📗 ITAB", "📝 THO"])
    
    with tab1:
        if sel in jmf_data:
            for cle, valeur in jmf_data[sel].items():
                with st.expander(f"🔹 {cle}"):
                    st.write(valeur)
        else:
            st.info("Données JMF non disponibles.")
            
    with tab2:
        if sel in itab_data:
            for cle, valeur in itab_data[sel].items():
                with st.expander(f"🔹 {cle}"):
                    st.markdown(valeur)
        else:
            st.info("Données ITAB non disponibles.")
            
    with tab3:
        conn = st.connection("gsheets", type=GSheetsConnection)
        URL_SHEET = "https://docs.google.com/spreadsheets/d/16n6kX-p-fD-BIn7IasFm6vE7f-J6LgY_F_R_X_X_X_X/edit" # URL masquée pour l'exemple
        df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO")
        
        with st.form("tho_form"):
            st.subheader(f"Suivi de culture : {sel}")
            v_p = st.text_area("Implantation")
            v_e = st.text_area("Entretien")
            v_s = st.text_area("Santé")
            v_r = st.text_area("Rendement")
            v_v = st.text_input("Variété utilisée")
            v_i = st.text_area("Infos supp")
            
            if st.form_submit_button("Enregistrer"):
                new_row = {"DATE": datetime.now().strftime("%d/%m/%Y"), "LEGUME": sel, "IMPLANTATION": v_p, "ENTRETIEN": v_e, "SANTE": v_s, "RENDEMENT": v_r, "VARIETE": v_v, "INFO_SUPP": v_i}
                df_final = pd.concat([df_gs[df_gs['LEGUME'] != sel], pd.DataFrame([new_row])], ignore_index=True)
                conn.update(spreadsheet=URL_SHEET, worksheet="THO", data=df_final)
                st.success("Données THO enregistrées !")

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
