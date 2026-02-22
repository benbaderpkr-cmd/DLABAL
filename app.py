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

# Initialisation des états
if "user_name" not in st.session_state: st.session_state["user_name"] = ""
if "view_mode" not in st.session_state: st.session_state["view_mode"] = "ACCUEIL"

# ==========================================
# 2. FONCTIONS UTILES
# ==========================================
def load_json(f):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as file: return json.load(file)
        except: return {}
    return {}

def sans_accent(texte):
    return ''.join(c for c in unicodedata.normalize('NFD', texte)
                   if unicodedata.category(c) != 'Mn').lower()

# ==========================================
# 3. CONNEXIONS ET CHARGEMENT DONNÉES
# ==========================================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"
URL_SHEET2 = "https://docs.google.com/spreadsheets/d/1wUngO5HjSCRYbWzd0hMxKBj4aUD4ThW1ishVvaOwOcc/edit#gid=0"
URL_SCRIPT_MAIL = "https://script.google.com/macros/s/AKfycbwMW0m4CJPvv5rJ0tFjmoU58F6LTnpNmB1BYsp3bKiKy9vBi3PFUQqmWP9n-axt-iqXZA/exec" 

conn = st.connection("gsheets", type=GSheetsConnection)

ARG_DATA = load_json("arg.json")
GAB_DATA = load_json("gab.json")
JMF_DATA = load_json("jmf.json")
JDV_DATA = load_json("jdv.json")
ITAB_DATA = load_json("itab.json")
FERTI_DATA = load_json("calcul_ferti.json")
JP1_OFFICIEL = load_json("reglages_jp1 (4).json")
JP1_JMF = load_json("reglages_jmf.json")

legumes_uniques = [l for l in set(list(GAB_DATA.keys()) + list(JMF_DATA.keys()) + list(JDV_DATA.keys()) + list(ARG_DATA.keys())) 
                   if GAB_DATA.get(l) or JMF_DATA.get(l) or JDV_DATA.get(l) or ARG_DATA.get(l)]
tous_les_legumes = sorted(legumes_uniques, key=sans_accent)

# ==========================================
# 4. SIDEBAR ET NAVIGATION
# ==========================================
with st.sidebar:
    if st.button("**DLABAL**", use_container_width=True):
        st.session_state["view_mode"] = "ACCUEIL"
        st.rerun()
    
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.9em; margin-top: -15px;'>BDD ITK Maraîchage</p>", unsafe_allow_html=True)
    
    # NAVIGATION PRINCIPALE PAR LÉGUME
    # On utilise un callback pour changer le mode uniquement quand on touche à CE selectbox
    def on_change_sidebar():
        if st.session_state["nav_sidebar"] != "---":
            st.session_state["view_mode"] = "LEGUME"

    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes, key="nav_sidebar", on_change=on_change_sidebar)
    
    st.divider()

    if st.button("⚙️ RÉGLAGES JP1", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_JP1"
        st.rerun()
        
    if st.button("🧪 CALCUL FERTI", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_FERTI"
        st.rerun()

    st.link_button("📂 Fiches légumes JA", "https://drive.google.com/drive/u/0/folders/1nj4ZGdFExm-_xs8xRYBBxmSkqmVEvdmM", use_container_width=True)
        
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""; cookies.save(); st.session_state["password_correct"] = False; st.rerun()

# ==========================================
# 5. AFFICHAGE CENTRAL
# ==========================================

# --- PAGE FERTILISATION ---
if st.session_state["view_mode"] == "PAGE_FERTI":
    st.title("🧪 CALCULATEUR DE FERTILISATION")
    # Utilisation d'une clé unique pour ne pas interférer avec la sidebar
    leg_f = st.selectbox("Légume pour base de calcul :", ["---"] + sorted(FERTI_DATA.keys(), key=sans_accent), key="sel_ferti")
    
    # ... Logique de calcul identique à avant ...
    with st.expander("Saisie manuelle (u/ha)"):
        cn, cp, ck = st.columns(3)
        manuel_n = cn.number_input("N", min_value=0, value=0)
        manuel_p = cp.number_input("P", min_value=0, value=0)
        manuel_k = ck.number_input("K", min_value=0, value=0)
    col1, col2 = st.columns(2)
    longueur = col1.number_input("Longueur (m)", min_value=1, value=10)
    largeur = col2.number_input("Largeur (m)", min_value=0.1, value=1.0)
    surface = longueur * largeur
    st.markdown("#### Caractéristiques de l'engrais")
    t1, t2, t3 = st.columns(3)
    ten_N, ten_P, ten_K = t1.number_input("% N", value=6.0), t2.number_input("% P", value=4.0), t3.number_input("% K", value=10.0)
    ten_pat = st.number_input("Patentkali % K", value=30.0)
    
    rows = []; facteur = surface / 10000
    def calc(n_ha, p_ha, k_ha, label):
        b_n, b_k = n_ha * facteur, k_ha * facteur
        dose_kg = round(b_n / (ten_N / 100), 1) if ten_N > 0 else 0
        k_app = round(dose_kg * (ten_K / 100), 2)
        manque_k = max(0, round(b_k - k_app, 2))
        dose_pat = round(manque_k / (ten_pat / 100), 2) if ten_pat > 0 else 0
        return {"Source": label, "Besoin (U/ha)": f"N:{n_ha}|K:{k_ha}", "Dose Principal (kg)": dose_kg, "💎 Patentkali (kg)": dose_pat}
    
    if (manuel_n > 0 or manuel_k > 0):
        rows.append(calc(manuel_n, manuel_p, manuel_k, "Manuel"))
    elif leg_f != "---":
        d = FERTI_DATA.get(leg_f, {})
        for s, v in d.items():
            if v: rows.append(calc(v["N"], v["P"], v["K"], s))
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# --- PAGE REGLAGES JP1 ---
elif st.session_state["view_mode"] == "PAGE_JP1":
    st.title("⚙️ RÉGLAGES JP1 TERRADONIS")
    list_off = [item["CULTURE"] for item in JP1_OFFICIEL.get("reglages", [])]
    list_jmf = [item["CULTURE"] for item in JP1_JMF.get("reglages", [])]
    full_list = sorted(list(set(list_off + list_jmf)), key=sans_accent)
    
    # Clé unique pour isoler ce selectbox
    l_jp1 = st.selectbox("Choisir un légume :", ["---"] + full_list, key="sel_jp1")
    
    if l_jp1 != "---":
        tableau_data = []
        off_data = next((i for i in JP1_OFFICIEL.get("reglages", []) if i["CULTURE"] == l_jp1), None)
        tableau_data.append({
            "Source": "OFFICIEL", "Rouleau(x)": off_data.get("ROULEAUX", "-") if off_data else "Aucune donnée",
            "Pignons (AV/AR)": "-", "Observations": "-"
        })
        jmf_item = next((i for i in JP1_JMF.get("reglages", []) if i["CULTURE"] == l_jp1), None)
        if jmf_item:
            tableau_data.append({
                "Source": "JMF", "Rouleau(x)": jmf_item.get("ROULEAU", "-"),
                "Pignons (AV/AR)": f"{jmf_item.get('AV','-')} / {jmf_item.get('AR','-')}", "Observations": jmf_item.get("OBS", "-")
            })
        st.table(pd.DataFrame(tableau_data))

# --- PAGE LEGUME (ONGLETS) ---
elif st.session_state["view_mode"] == "LEGUME":
    # On récupère le légume sélectionné dans la sidebar
    sel_legume = st.session_state.get("nav_sidebar", "---")
    if sel_legume != "---":
        st.title(f"📊 {sel_legume.upper()}")
        tabs = st.tabs(["📘 ARG", "📋 GAB", "🚜 JMF", "🌿 JDV", "📗 ITAB", "📝 THO"])
        
        # ... (Le code de tes onglets ici reste le même, utilisant 'sel_legume') ...
        with tabs[0]:
            arg_l = ARG_DATA.get(sel_legume, {})
            if arg_l: 
                st.write(f"Données ARG pour {sel_legume}") 
                # (Ton code complet pour ARG)
            else: st.info(f"Aucune donnée ARG {sel_legume} disponible.")
        # ... (Répéter pour les autres onglets) ...

else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.markdown("---")
    st.info("Sélectionnez un légume dans la barre latérale ou utilisez les outils JP1 / Ferti.")
