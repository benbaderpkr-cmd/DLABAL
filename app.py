import streamlit as st
import json
import os
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_cookies_manager import EncryptedCookieManager

# ==========================================
# 1. CONFIGURATION ET SECURITE
# ==========================================
st.set_page_config(page_title="DLABAL - SYSTÈME EXPERT", layout="wide", page_icon="🌱")

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

# Initialisation silencieuse du cache
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

# ==========================================
# 2. CONNEXIONS ET CHARGEMENT
# ==========================================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"
URL_SHEET2 = "https://docs.google.com/spreadsheets/d/1wUngO5HjSCRYbWzd0hMxKBj4aUD4ThW1ishVvaOwOcc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def envoyer_feedback(legume, nom_onglet_app, message, nom_bloc, nom_utilisateur):
    try:
        nom_sheet = legume.upper()
        new_row = pd.DataFrame([{
            "DATE": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "NOM": nom_utilisateur,
            "LEGUME": nom_sheet,
            "ONGLET": nom_onglet_app,
            "BLOC": nom_bloc,
            "FEEDBACK": message
        }])
        df_existing = conn.read(spreadsheet=URL_SHEET2, worksheet=nom_sheet, ttl=0)
        df_updated = pd.concat([df_existing, new_row], ignore_index=True)
        conn.update(spreadsheet=URL_SHEET2, worksheet=nom_sheet, data=df_updated)
        st.toast(f"✅ Merci {nom_utilisateur} ! Feedback enregistré.", icon="🚀")
    except Exception:
        st.error("Erreur d'enregistrement.")

def load_json(f):
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as file: return json.load(file)
    return {}

GAB_DATA = load_json("gab.json")
JMF_DATA = load_json("jmf.json")
JDV_DATA = load_json("jdv.json")
SOURCES_JMF = load_json("sources_jmf.json")

# Filtrage intelligent
tous_les_legumes = sorted([l for l in set(list(GAB_DATA.keys()) + list(JMF_DATA.keys()) + list(JDV_DATA.keys())) if GAB_DATA.get(l) or JMF_DATA.get(l) or JDV_DATA.get(l)])

# ==========================================
# 3. SIDEBAR
# ==========================================
with st.sidebar:
    if st.button("**DLABAL**", use_container_width=True):
        st.session_state["view_mode"] = "DOSSIER"
        st.rerun()
    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes)
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""; cookies.save()
        st.session_state["password_correct"] = False; st.rerun()

# ==========================================
# 4. AFFICHAGE ET FORMULAIRES INTEGRES
# ==========================================
if sel != "---":
    st.title(f"📊 {sel.upper()}")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 GAB", "🚜 JMF", "🌿 JDV", "📝 THO"])

    # Fonction pour générer le petit formulaire de feedback dans le popover
    def popover_feedback(onglet, bloc):
        pop = st.popover("📝", help=f"Suggérer une correction pour {bloc}")
        with pop.form(key=f"form_{onglet}_{bloc}_{sel}"):
            # Champ Nom qui récupère la valeur en cache
            nom = st.text_input("Ton Nom :", value=st.session_state["user_name"])
            msg = st.text_area("Ta suggestion :")
            if st.form_submit_button("Envoyer"):
                if not nom or not msg:
                    st.warning("Nom et message requis.")
                else:
                    st.session_state["user_name"] = nom # On met à jour le cache
                    envoyer_feedback(sel, onglet, msg, bloc, nom)
                    st.rerun() # Relance pour que le nom s'affiche partout au prochain coup

    with tab1:
        g = GAB_DATA.get(sel, {})
        if "BLOCS_IDENTITE" in g:
            cols = st.columns(len(g["BLOCS_IDENTITE"]))
            for i, b in enumerate(g["BLOCS_IDENTITE"]):
                with cols[i]:
                    st.success(f"**{b['titre']}**\n\n{b['contenu']}")
                    popover_feedback("GAB", b['titre'])
        for k, v in g.get("TECHNIQUE", {}).items():
            with st.expander(f"📌 {k}", expanded=True):
                st.markdown(v)
                c1, c2 = st.columns([0.96, 0.04]); with c2: popover_feedback("GAB", k)

    with tab2:
        for t, c in JMF_DATA.get(sel, {}).items():
            with st.expander(f"📌 {t}", expanded=True):
                st.markdown(c)
                c1, c2 = st.columns([0.96, 0.04]); with c2: popover_feedback("JMF", t)

    with tab3:
        for t, c in JDV_DATA.get(sel, {}).items():
            with st.expander(f"🌿 {t}", expanded=True):
                st.markdown(str(c))
                c1, c2 = st.columns([0.96, 0.04]); with c2: popover_feedback("JDV", t)

    with tab4:
        st.subheader("📝 Saisie Terrain")
        # Ton code THO reste identique ici...
