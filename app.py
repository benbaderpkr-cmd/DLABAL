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
        if "leg_sel" in st.session_state: del st.session_state["leg_sel"]
        st.rerun()
    
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.9em; margin-top: -15px;'>BDD ITK Maraîchage</p>", unsafe_allow_html=True)
    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes, key="leg_sel")
    if sel != "---": st.session_state["view_mode"] = "LEGUME"
    st.divider()
    
    if st.button("⚙️ RÉGLAGES JP1", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_JP1"
        if "leg_sel" in st.session_state: del st.session_state["leg_sel"]
        st.rerun()
        
    if st.button("🧪 CALCUL FERTI", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_FERTI"
        if "leg_sel" in st.session_state: del st.session_state["leg_sel"]
        st.rerun()
        
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""; cookies.save(); st.session_state["password_correct"] = False; st.rerun()

# ==========================================
# 5. AFFICHAGE CENTRAL
# ==========================================

if st.session_state["view_mode"] == "PAGE_FERTI":
    st.title("🧪 CALCULATEUR DE FERTILISATION")
    # ... (code ferti inchangé)

elif st.session_state["view_mode"] == "PAGE_JP1":
    st.title("⚙️ RÉGLAGES JP1")
    # ... (code JP1 inchangé)

elif st.session_state["view_mode"] == "LEGUME" and sel != "---":
    st.title(f"📊 {sel.upper()}")
    tabs = st.tabs(["📘 ARG", "📋 GAB", "🚜 JMF", "🌿 JDV", "📗 ITAB", "📝 THO"])

    with tabs[0]: # Onglet ARG
        arg_l = ARG_DATA.get(sel, {})
        if arg_l:
            for titre, contenu in arg_l.items():
                with st.expander(f"📘 {titre}", expanded=True):
                    
                    # --- GESTION TABLEAUX (RESPONSIVE & SECURISEE) ---
                    if isinstance(contenu, dict) and "lignes" in contenu:
                        df_temp = pd.DataFrame(contenu["lignes"])
                        
                        # Raccourcissement colonnes
                        mapping_col = {"Janv.":"J","Fév.":"F","Mars":"M","Avril":"A","Mai":"M","Juin":"J","Juill.":"J","Août":"A","Sept.":"S","Oct.":"O","Nov.":"N","Déc.":"D","col_0":"Activité"}
                        df_temp = df_temp.rename(columns=mapping_col)
                        
                        # Raccourcissement contenu
                        def clean_val(v):
                            if not isinstance(v, str): return v
                            m = {"Plein champ":"PC", "Culture sous abri":"Abri", "Temps de travaux (indicatif)":"Tps W", "Temps de travaux":"Tps W"}
                            for l, c in m.items(): v = v.replace(l, c)
                            return v
                        
                        df_temp = df_temp.apply(lambda x: x.map(clean_val))
                        st.dataframe(df_temp, use_container_width=True, hide_index=True)

                    elif isinstance(contenu, list):
                        try: st.dataframe(pd.DataFrame(contenu), use_container_width=True, hide_index=True)
                        except: st.write(str(contenu))
                    
                    # --- GESTION TEXTE (NETTOYAGE PDF) ---
                    else:
                        t = str(contenu).strip()
                        while t.startswith((".", ":", " ")): t = t[1:].strip()
                        
                        # Harmonisation sauts de ligne
                        t = t.replace('\\\\n', '\n').replace('\\n', '\n')
                        
                        # Suppression des sauts de ligne orphelins (ex: Artichaut)
                        # On ne garde le saut de ligne que s'il y a un tiret ou un double saut
                        import re
                        t = re.sub(r'(?<!\n)\n(?![-\s\n])', ' ', t)
                        
                        # Forcer le saut de ligne avant les tirets pour les listes
                        t = t.replace('\n-', '  \n-').replace(' -', '  \n-')
                        
                        st.markdown(t)
                    
                    popover_feedback("ARG", titre, sel)

    # ... (Restant des onglets GAB, JMF, JDV, ITAB, THO comme dans app 21)
    # Note : Assurez-vous de bien fermer les parenthèses et les blocs.

else:
    st.title("🌱 Bienvenue sur DLABAL")
    # ... (accueil inchangé)
