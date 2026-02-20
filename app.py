import streamlit as st
import json
import os
import pandas as pd
import requests
import unicodedata
import streamlit.components.v1 as components
import re
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
# 2. FONCTIONS DE CHARGEMENT
# ==========================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# --- NOUVELLE FONCTION PAGE CALCUL ---
def page_calcul_ferti():
    st.title("📊 CALCUL FERTI/LEGUME")
    ferti_data = load_json('calcul_ferti.json')
    if not ferti_data:
        st.error("Fichier 'calcul_ferti.json' introuvable.")
        return

    legume_sel = st.selectbox("Légume :", list(ferti_data.keys()))
    
    col1, col2 = st.columns(2)
    long = col1.number_input("Longueur (m)", value=10.0)
    larg = col2.number_input("Largeur (m)", value=0.75)
    surf = long * larg
    
    st.subheader("Votre Engrais")
    e1, e2, e3 = st.columns(3)
    en = e1.number_input("N (%)", value=6.0)
    
    txt = ferti_data[legume_sel].get("FERTILISATION", "")
    match = re.search(r"(\d+)\s*kg\s*N", txt)
    besoin_n = int(match.group(1)) if match else None

    if besoin_n:
        st.info(f"Besoin JMF : {besoin_n} kg N/ha")
        apport = (besoin_n / 10000) * surf / (en / 100)
        st.success(f"Apport final : **{apport:.2f} kg**")
    else:
        st.warning("Pas de valeur chiffrée (kg N) trouvée.")
        st.write(txt)

# ==========================================
# 3. INTERFACE (SIDEBAR)
# ==========================================
jmf_data = load_json('jmf.json')
itab_data = load_json('itab.json')

with st.sidebar:
    st.title("DLABAL")
    tous_les_legumes = sorted(list(set(list(jmf_data.keys()) + list(itab_data.keys()))))
    sel = st.selectbox("🔍 Rechercher un légume :", [""] + tous_les_legumes)
    
    if sel:
        st.session_state["page_actuelle"] = "fiche"

    st.markdown("---")
    st.subheader("⚙️ REGLAGES JP1 TERRADONIS")
    if st.button("CALIBRE SEMENCE", use_container_width=True): pass
    if st.button("PIGNONS/DISQUES", use_container_width=True): pass
    
    # LE BOUTON DEMANDÉ
    if st.button("📊 CALCUL FERTI/LEGUME", use_container_width=True):
        st.session_state["page_actuelle"] = "calcul_ferti"
        st.rerun()

# ==========================================
# 4. LOGIQUE D'AFFICHAGE
# ==========================================

# Affichage de la page de calcul
if st.session_state.get("page_actuelle") == "calcul_ferti":
    page_calcul_ferti()

# Affichage des fiches (Ton code d'origine)
elif sel:
    st.title(f"🌿 {sel.upper()}")
    tab1, tab2, tab3 = st.tabs(["📘 JMF", "📗 ITAB", "📝 THO"])
    
    with tab1:
        if sel in jmf_data:
            for c, v in jmf_data[sel].items():
                with st.expander(f"🔹 {c}"): st.write(v)
    
    with tab2:
        if sel in itab_data:
            for c, v in itab_data[sel].items():
                with st.expander(f"🔹 {c}"): st.markdown(v)
    
    with tab3:
        st.write("Saisie THO...")

else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.write("Sélectionnez un légume ou utilisez le calculateur.")
