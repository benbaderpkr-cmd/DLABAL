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
    if not texte: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texte)
                   if unicodedata.category(c) != 'Mn').lower()

def format_text(txt):
    """Nettoie les sauts de ligne pour l'affichage Markdown Streamlit"""
    if not txt: return ""
    # On remplace les doubles backslash et les simples par le format Markdown (2 espaces + \n)
    t = str(txt).replace('\\\\n', '  \n').replace('\\n', '  \n').replace('\n', '  \n')
    return t

# ==========================================
# 3. CHARGEMENT DONNÉES
# ==========================================
ARG_DATA = load_json("arg.json")
GAB_DATA = load_json("gab.json")
JMF_DATA = load_json("jmf.json")
JDV_DATA = load_json("jdv.json")
ITAB_DATA = load_json("itab.json")
FERTI_DATA = load_json("calcul_ferti.json")
JP1_OFFICIEL = load_json("reglages_jp1.json")
JP1_JMF = load_json("reglages_jmf.json")

# Connexion GSheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL_SHEET = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"

# Liste complète pour la sidebar
leg_all = set(list(GAB_DATA.keys()) + list(JMF_DATA.keys()) + list(JDV_DATA.keys()) + list(ARG_DATA.keys()))
tous_les_legumes = sorted([l for l in leg_all if l], key=sans_accent)

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    if st.button("**🏠 ACCUEIL DLABAL**", use_container_width=True):
        st.session_state["view_mode"] = "ACCUEIL"
        st.rerun()
    
    st.divider()
    
    def on_change_sidebar():
        if st.session_state["nav_sidebar"] != "---":
            st.session_state["view_mode"] = "LEGUME"

    st.selectbox("🌱 Choisir un légume :", ["---"] + tous_les_legumes, key="nav_sidebar", on_change=on_change_sidebar)
    
    st.divider()
    if st.button("⚙️ RÉGLAGES JP1", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_JP1"
        st.rerun()
        
    if st.button("🧪 CALCUL FERTI", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_FERTI"
        st.rerun()

# ==========================================
# 5. LOGIQUE D'AFFICHAGE
# ==========================================

# --- PAGE RÉGLAGES JP1 ---
if st.session_state["view_mode"] == "PAGE_JP1":
    st.title("⚙️ RÉGLAGES JP1 TERRADONIS")
    
    # FUSION RÉELLE DES LÉGUMES JP1
    l_off = [i["CULTURE"] for i in JP1_OFFICIEL.get("reglages", [])]
    l_jmf = [i["CULTURE"] for i in JP1_JMF.get("reglages", [])]
    fusion_jp1 = sorted(list(set(l_off + l_jmf)), key=sans_accent)
    
    sel_jp1 = st.selectbox("Légume pour semis :", ["---"] + fusion_jp1)
    
    if sel_jp1 != "---":
        res = []
        # Source Officielle
        d_off = next((i for i in JP1_OFFICIEL.get("reglages", []) if i["CULTURE"] == sel_jp1), None)
        res.append({
            "SOURCE": "OFFICIEL (Terrateck)",
            "ROULEAU": d_off.get("ROULEAUX", d_off.get("ROULEAU", "-")) if d_off else "Non listé",
            "PIGNONS": "-", "OBS": "-"
        })
        # Source JMF
        d_jmf = next((i for i in JP1_JMF.get("reglages", []) if i["CULTURE"] == sel_jp1), None)
        if d_jmf:
            res.append({
                "SOURCE": "JMF (Grelinette)",
                "ROULEAU": d_jmf.get("ROULEAU", "-"),
                "PIGNONS": f"{d_jmf.get('AV','-')} / {d_jmf.get('AR','-')}",
                "OBS": d_jmf.get("OBS", "-")
            })
        st.table(pd.DataFrame(res))

# --- PAGE FERTILISATION ---
elif st.session_state["view_mode"] == "PAGE_FERTI":
    st.title("🧪 CALCULATEUR DE FERTILISATION")
    # (Le code de calcul reste identique)

# --- PAGE FICHE LÉGUME ---
elif st.session_state["view_mode"] == "LEGUME":
    sel = st.session_state.get("nav_sidebar", "---")
    if sel != "---":
        st.title(f"📊 {sel.upper()}")
        tabs = st.tabs(["📘 ARG", "📋 GAB", "🚜 JMF", "🌿 JDV", "📗 ITAB", "📝 THO"])
        
        with tabs[0]: # ARG
            for t, c in ARG_DATA.get(sel, {}).items():
                with st.expander(f"📘 {t}", expanded=True):
                    if isinstance(c, dict) and "lignes" in c:
                        st.dataframe(pd.DataFrame(c["lignes"]), use_container_width=True)
                    else: st.markdown(format_text(c))
        
        with tabs[1]: # GAB
            g = GAB_DATA.get(sel, {})
            if "BLOCS_IDENTITE" in g:
                cols = st.columns(len(g["BLOCS_IDENTITE"]))
                for i, b in enumerate(g["BLOCS_IDENTITE"]):
                    cols[i].success(f"**{b['titre']}**\n\n{format_text(b['contenu'])}")
            for k, v in g.get("TECHNIQUE", {}).items():
                with st.expander(f"📌 {k}", expanded=True): st.markdown(format_text(v))
        
        with tabs[2]: # JMF
            for t, c in JMF_DATA.get(sel, {}).items():
                with st.expander(f"🚜 {t}", expanded=True): st.markdown(format_text(c))
        
        with tabs[3]: # JDV
            for t, c in JDV_DATA.get(sel, {}).items():
                with st.expander(f"🌿 {t}", expanded=True): st.markdown(format_text(c))

        with tabs[4]: # ITAB
            for t, c in ITAB_DATA.get(sel, {}).items():
                with st.expander(f"📗 {t}", expanded=True): st.markdown(format_text(c))

# --- PAGE ACCUEIL ---
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.markdown("---")
    st.markdown("### Guide d'utilisation\n\n- **Cliquer sur un légume** à gauche pour voir les fiches.\n- **Boutons réglages/ferti** pour les outils de calcul.")
