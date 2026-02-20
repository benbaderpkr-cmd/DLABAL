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
# 2. FONCTIONS DE CHARGEMENT ET OUTILS
# ==========================================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# --- NOUVELLE FONCTION : PAGE CALCUL FERTILISATION ---
def page_calcul_ferti():
    st.title("📊 CALCULATEUR DE FERTILISATION")
    st.markdown("---")
    
    ferti_data = load_json('calcul_ferti.json')
    if not ferti_data:
        st.error("Fichier 'calcul_ferti.json' non trouvé ou vide.")
        return

    # 1. Sélection
    legume_sel = st.selectbox("Sélectionnez un légume :", list(ferti_data.keys()))
    
    # 2. Dimensions
    c_dim1, c_dim2 = st.columns(2)
    longueur = c_dim1.number_input("Longueur de la planche (m)", min_value=0.0, value=10.0)
    largeur = c_dim2.number_input("Largeur de la planche (m)", min_value=0.0, value=0.75)
    surface = longueur * largeur
    st.info(f"Surface à fertiliser : **{surface:.2f} m²**")

    # 3. Produit Fertilisant
    st.subheader("🧪 Votre Produit Fertilisant")
    c_f1, c_f2, c_f3 = st.columns(3)
    f_n = c_f1.number_input("N (%)", value=6.0)
    f_p = c_f2.number_input("P (%)", value=3.0)
    f_k = c_f3.number_input("K (%)", value=10.0)

    # 4. Extraction et Calcul
    txt_ferti = ferti_data[legume_sel].get("FERTILISATION", "")
    
    def get_val(symbole, texte):
        pattern = rf"(\d+)\s*kg\s*{symbole}"
        match = re.search(pattern, texte)
        return int(match.group(1)) if match else None

    val_n = get_val("N", txt_ferti)
    
    st.markdown("---")
    if val_n:
        st.write(f"**Besoin identifié (JMF) :** {val_n} kg N / hectare")
        # Calcul : (Besoin/10000) * surface / (Dosage_Engrais/100)
        apport = (val_n / 10000) * surface / (f_n / 100)
        st.success(f"### 👉 Apportez {apport:.2f} kg de votre engrais")
    else:
        st.warning("⚠️ Pas de valeur chiffrée (kg N) trouvée dans JMF pour ce légume.")
        st.write("**Texte source JMF :**")
        st.info(txt_ferti)

# ==========================================
# 3. INTERFACE PRINCIPALE (SIDEBAR)
# ==========================================
jmf_data = load_json('jmf.json')
itab_data = load_json('itab.json')

with st.sidebar:
    st.image("https://img.icons8.com/color/96/sprout.png", width=80)
    st.title("DLABAL")
    
    # Recherche de légume
    tous_les_legumes = sorted(list(set(list(jmf_data.keys()) + list(itab_data.keys()))))
    sel = st.selectbox("🔍 Rechercher un légume :", [""] + tous_les_legumes)
    
    if sel:
        st.session_state["page_actuelle"] = "fiche"
    
    st.markdown("---")
    st.subheader("⚙️ REGLAGES JP1 TERRADONIS")
    # Tes boutons réglages existants...
    if st.button("CALIBRE SEMENCE", use_container_width=True): pass
    if st.button("PIGNONS/DISQUES", use_container_width=True): pass
    
    st.markdown("---")
    # LE NOUVEAU BOUTON
    if st.button("📊 CALCUL FERTI/LEGUME", use_container_width=True):
        st.session_state["page_actuelle"] = "calcul_ferti"
        st.rerun()

# ==========================================
# 4. LOGIQUE D'AFFICHAGE
# ==========================================

# Affichage de la page de calcul
if st.session_state.get("page_actuelle") == "calcul_ferti":
    page_calcul_ferti()

# Affichage des fiches légumes
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
        st.write("Section Saisie Terrain / THO en cours...")

# Page d'accueil par défaut
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.markdown("---")
    st.write("Sélectionnez un légume dans la barre latérale pour commencer.")
