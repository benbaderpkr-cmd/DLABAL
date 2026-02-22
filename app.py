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

if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "ACCUEIL"

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

# Chargement du nouveau fichier ARG
ARG_DATA = load_json("arg.json")
GAB_DATA = load_json("gab.json")
JMF_DATA = load_json("jmf.json")
JDV_DATA = load_json("jdv.json")
ITAB_DATA = load_json("itab.json")
FERTI_DATA = load_json("calcul_ferti.json")
RAW_JP1 = load_json("reglages_jp1.json")

legumes_uniques = [l for l in set(list(GAB_DATA.keys()) + list(JMF_DATA.keys()) + list(JDV_DATA.keys()) + list(ARG_DATA.keys())) 
                   if GAB_DATA.get(l) or JMF_DATA.get(l) or JDV_DATA.get(l) or ARG_DATA.get(l)]
tous_les_legumes = sorted(legumes_uniques, key=sans_accent)

def envoyer_feedback(legume, nom_onglet_app, message, nom_bloc, nom_utilisateur):
    try:
        nom_sheet = legume.upper()
        new_row = pd.DataFrame([{
            "DATE": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "NOM": nom_utilisateur, "LEGUME": nom_sheet, "ONGLET": nom_onglet_app,
            "BLOC": nom_bloc, "FEEDBACK": message
        }])
        df_updated = pd.concat([conn.read(spreadsheet=URL_SHEET2, worksheet=nom_sheet, ttl=0), new_row], ignore_index=True)
        conn.update(spreadsheet=URL_SHEET2, worksheet=nom_sheet, data=df_updated)
        if "https" in URL_SCRIPT_MAIL:
            requests.get(f"{URL_SCRIPT_MAIL}?legume={nom_sheet}&nom={nom_utilisateur}", timeout=5)
        st.toast(f"🚀 Merci {nom_utilisateur} ! Enregistré.", icon="✅")
    except: st.error("Erreur d'enregistrement.")

def popover_feedback(onglet, bloc, legume_sel):
    pop = st.popover("📝")
    with pop.form(key=f"form_{onglet}_{bloc}_{legume_sel}"):
        nom_in = st.text_input("Nom :", value=st.session_state["user_name"])
        msg_in = st.text_area("Suggestion :")
        if st.form_submit_button("Envoyer"):
            st.session_state["user_name"] = nom_in 
            envoyer_feedback(legume_sel, onglet, msg_in, bloc, nom_in)
            st.rerun()

# ==========================================
# 4. SIDEBAR ET NAVIGATION
# ==========================================
with st.sidebar:
    if st.button("**DLABAL**", use_container_width=True):
        st.session_state["view_mode"] = "ACCUEIL"
        st.rerun()
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.9em; margin-top: -15px;'>BDD ITK Maraîchage</p>", unsafe_allow_html=True)
    
    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes)
    if sel != "---":
        st.session_state["view_mode"] = "LEGUME"
    
    st.divider()
    if st.button("⚙️ RÉGLAGES JP1 TERRADONIS", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_JP1"; st.rerun()
    if st.button("🧪 CALCUL FERTI", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_FERTI"; st.rerun()
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""; cookies.save(); st.session_state["password_correct"] = False; st.rerun()

# ==========================================
# 5. AFFICHAGE CENTRAL
# ==========================================

# --- PAGE CALCUL FERTI ---
if st.session_state["view_mode"] == "PAGE_FERTI":
    # (Le code de fertilisation reste identique au précédent envoyé)
    st.title("🧪 CALCULATEUR DE FERTILISATION")
    # ... [Code fertilisation précédemment validé] ...

# --- PAGE RÉGLAGES JP1 ---
elif st.session_state["view_mode"] == "PAGE_JP1":
    st.title("⚙️ RÉGLAGES JP1 TERRADONIS")

# --- PAGE LÉGUME ---
elif st.session_state["view_mode"] == "LEGUME" and sel != "---":
    st.title(f"📊 {sel.upper()}")
    
    # Ajout de l'onglet ARG avant GAB
    tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["📘 ARG", "📋 GAB", "🚜 JMF", "🌿 JDV", "📗 ITAB", "📝 THO"])

    with tab0:
        arg_l = ARG_DATA.get(sel, {})
        if arg_l:
            for t, c in arg_l.items():
                with st.expander(f"📘 {t}", expanded=True):
                    # Détection si le contenu est une liste (tableau) ou du texte
                    if isinstance(c, list):
                        try:
                            df_arg = pd.DataFrame(c)
                            st.table(df_arg)
                        except:
                            st.write(str(c))
                    else:
                        st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                    popover_feedback("ARG", t, sel)
        else:
            st.info("Aucune donnée ARG disponible pour ce légume.")

    with tab1:
        g = GAB_DATA.get(sel, {})
        if "BLOCS_IDENTITE" in g:
            cols = st.columns(len(g["BLOCS_IDENTITE"]))
            for i, b in enumerate(g["BLOCS_IDENTITE"]):
                with cols[i]:
                    st.success(f"**{b['titre']}**\n\n{str(b['contenu']).replace('\\\\n', '\\n').replace('\\n', '\n')}")
        for k, v in g.get("TECHNIQUE", {}).items():
            with st.expander(f"📌 {k}", expanded=True):
                st.markdown(str(v).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("GAB", k, sel)

    with tab2:
        for t, c in JMF_DATA.get(sel, {}).items():
            with st.expander(f"🚜 {t}", expanded=True):
                st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("JMF", t, sel)

    with tab3:
        for t, c in JDV_DATA.get(sel, {}).items():
            with st.expander(f"🌿 {t}", expanded=True):
                st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("JDV", t, sel)

    with tab4:
        for t, c in ITAB_DATA.get(sel, {}).items():
            with st.expander(f"📗 {t}", expanded=True):
                st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("ITAB", t, sel)

    with tab5:
        st.subheader("📝 Saisie Terrain (THO)")
        # ... [Reste du code THO] ...

# --- ACCUEIL ---
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.info("Sélectionnez un légume ou utilisez le calculateur de fertilisation.")
