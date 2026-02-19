import streamlit as st
import json
import os
import pandas as pd
import requests # <-- AJOUTÉ : Pour communiquer avec Google
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

if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

# ==========================================
# 2. CONNEXIONS ET URL NOTIFICATION
# ==========================================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"
URL_SHEET2 = "https://docs.google.com/spreadsheets/d/1wUngO5HjSCRYbWzd0hMxKBj4aUD4ThW1ishVvaOwOcc/edit#gid=0"

# --- ACTION REQUISE : COLLE TON URL ICI (DOIT FINIR PAR /exec) ---
URL_SCRIPT_MAIL = "https://script.google.com/macros/s/AKfycbwMW0m4CJPvv5rJ0tFjmoU58F6LTnpNmB1BYsp3bKiKy9vBi3PFUQqmWP9n-axt-iqXZA/exec" 

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
        
        # 1. ÉCRITURE DANS LE GSHEET
        try:
            df_existing = conn.read(spreadsheet=URL_SHEET2, worksheet=nom_sheet, ttl=0)
            df_updated = pd.concat([df_existing, new_row], ignore_index=True)
        except:
            df_updated = new_row
        
        conn.update(spreadsheet=URL_SHEET2, worksheet=nom_sheet, data=df_updated)
        
        # 2. ENVOI DE LA NOTIFICATION (avec diagnostic)
        if "https" in URL_SCRIPT_MAIL:
            try:
                # On ajoute un timeout pour ne pas bloquer l'app si Google est lent
                response = requests.get(f"{URL_SCRIPT_MAIL}?legume={nom_sheet}&nom={nom_utilisateur}", timeout=5)
                if response.status_code != 200:
                    st.error(f"Erreur Script Google : {response.status_code}")
            except Exception as e:
                st.warning(f"Le GSheet a été mis à jour, mais le mail n'a pu être envoyé.")
        
        # 3. INFOBULLE DE RÉUSSITE (REMISE ICI)
        st.toast(f"🚀 Merci {nom_utilisateur} ! Feedback enregistré.", icon="✅")

    except Exception as e:
        st.error(f"Erreur d'enregistrement sur l'onglet {legume.upper()}.")

def load_json(f):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as file: return json.load(file)
        except: return {}
    return {}

GAB_DATA = load_json("gab.json")
JMF_DATA = load_json("jmf.json")
JDV_DATA = load_json("jdv.json")

# Filtrage intelligent des légumes (Pilier 5)
tous_les_legumes = sorted([l for l in set(list(GAB_DATA.keys()) + list(JMF_DATA.keys()) + list(JDV_DATA.keys())) 
                           if GAB_DATA.get(l) or JMF_DATA.get(l) or JDV_DATA.get(l)])

# ==========================================
# 3. FONCTION FORMULAIRE (POPOVER)
# ==========================================
def popover_feedback(onglet, bloc, legume_sel):
    pop = st.popover("📝", help=f"Suggérer une correction pour {bloc}")
    with pop.form(key=f"form_{onglet}_{bloc}_{legume_sel}"):
        nom_in = st.text_input("Ton Nom :", value=st.session_state["user_name"])
        msg_in = st.text_area("Ta suggestion :")
        if st.form_submit_button("Envoyer"):
            if not nom_in or not msg_in:
                st.warning("Nom et message requis.")
            else:
                st.session_state["user_name"] = nom_in 
                envoyer_feedback(legume_sel, onglet, msg_in, bloc, nom_in)
                st.rerun()

# ==========================================
# 4. SIDEBAR ET NAVIGATION
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
# 5. AFFICHAGE
# ==========================================
if sel != "---":
    st.title(f"📊 {sel.upper()}")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 GAB", "🚜 JMF", "🌿 JDV", "📝 THO"])

    with tab1:
        g = GAB_DATA.get(sel, {})
        if "BLOCS_IDENTITE" in g:
            cols = st.columns(len(g["BLOCS_IDENTITE"]))
            for i, b in enumerate(g["BLOCS_IDENTITE"]):
                with cols[i]:
                    st.success(f"**{b['titre']}**\n\n{b['contenu']}")
                    popover_feedback("GAB", b['titre'], sel)
        for k, v in g.get("TECHNIQUE", {}).items():
            with st.expander(f"📌 {k}", expanded=True):
                st.markdown(v)
                c1, c2 = st.columns([0.96, 0.04])
                with c2: popover_feedback("GAB", k, sel)

    with tab2:
        for t, c in JMF_DATA.get(sel, {}).items():
            with st.expander(f"📌 {t}", expanded=True):
                st.markdown(c)
                c1, c2 = st.columns([0.96, 0.04])
                with c2: popover_feedback("JMF", t, sel)

    with tab3:
        for t, c in JDV_DATA.get(sel, {}).items():
            with st.expander(f"🌿 {t}", expanded=True):
                st.markdown(str(c))
                c1, c2 = st.columns([0.96, 0.04])
                with c2: popover_feedback("JDV", t, sel)

    with tab4:
        st.subheader("📝 Saisie Terrain")
        try:
            df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO", ttl=0)
            notes = df_gs[df_gs['LEGUME'] == sel].iloc[-1].to_dict() if not df_gs[df_gs['LEGUME'] == sel].empty else {}
        except:
            df_gs = pd.DataFrame(columns=["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"])
            notes = {}

        with st.form(key=f"f_tho_{sel}"):
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
else:
    st.title("🌱 Bienvenue sur DLABAL")

st.sidebar.markdown("---")
with st.sidebar:
    st.markdown("### 🌦️ Météo locale")
    components.html('<iframe width="150" height="300" frameborder="0" scrolling="no" src="https://meteofrance.com/widget/prevision/852810##3D6AA2" style="border: none;"></iframe>', height=310)



