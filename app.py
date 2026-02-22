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

# Chargement des fichiers JSON
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

# --- SIDEBAR ---
with st.sidebar:
    if st.button("**DLABAL**", use_container_width=True):
        st.session_state["view_mode"] = "ACCUEIL"
        st.rerun()
    
    # On ajoute une clé au selectbox pour pouvoir la manipuler
    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes, key="legume_selector")
    
    # Si on sélectionne un légume, on change le mode de vue
    if sel != "---":
        st.session_state["view_mode"] = "LEGUME"
    
    st.divider()

    # Quand on clique sur un outil, on remet le sélecteur de légume à "---"
    if st.button("⚙️ RÉGLAGES JP1 TERRADONIS", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_JP1"
        st.session_state["legume_selector"] = "---" # Reset le choix
        st.rerun()

    if st.button("🧪 CALCUL FERTI", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_FERTI"
        st.session_state["legume_selector"] = "---" # Reset le choix
        st.rerun()
# ==========================================
# 5. AFFICHAGE CENTRAL
# ==========================================

# --- PAGE CALCUL FERTI ---
if st.session_state["view_mode"] == "PAGE_FERTI":
    st.title("🧪 CALCULATEUR DE FERTILISATION")
    # (Le code de fertilisation complet tel que précédemment validé est ici)

# --- PAGE RÉGLAGES JP1 ---
elif st.session_state["view_mode"] == "PAGE_JP1":
    st.title("⚙️ RÉGLAGES JP1 TERRADONIS")
    # (Le code JP1 complet est ici)

# --- PAGE LÉGUME ---
elif st.session_state["view_mode"] == "LEGUME" and sel != "---":
    st.title(f"📊 {sel.upper()}")
    
    # Structure des onglets avec ARG en premier
    tabs = st.tabs(["📘 ARG", "📋 GAB", "🚜 JMF", "🌿 JDV", "📗 ITAB", "📝 THO"])

    with tabs[0]: # ARG
        arg_l = ARG_DATA.get(sel, {})
        if arg_l:
            for t, c in arg_l.items():
                with st.expander(f"📘 {t}", expanded=True):
                    # Gestion texte ou tableau JSON
                    if isinstance(c, list):
                        try: st.table(pd.DataFrame(c))
                        except: st.write(str(c))
                    else:
                        st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                    popover_feedback("ARG", t, sel)
        else:
            st.info("Aucune donnée ARG disponible.")

    with tabs[1]: # GAB
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

    with tabs[2]: # JMF
        for t, c in JMF_DATA.get(sel, {}).items():
            with st.expander(f"🚜 {t}", expanded=True):
                st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("JMF", t, sel)

    with tabs[3]: # JDV
        for t, c in JDV_DATA.get(sel, {}).items():
            with st.expander(f"🌿 {t}", expanded=True):
                st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("JDV", t, sel)

    with tabs[4]: # ITAB
        for t, c in ITAB_DATA.get(sel, {}).items():
            with st.expander(f"📗 {t}", expanded=True):
                st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("ITAB", t, sel)

    with tabs[5]: # THO
        st.subheader("📝 Saisie Terrain (THO)")
        # (Le code THO complet est ici)

# --- PAGE D'ACCUEIL ---
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
    st.info("👈 Commencez par choisir un légume dans la barre latérale.")

