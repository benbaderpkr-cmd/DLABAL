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

GAB_DATA = load_json("gab.json")
JMF_DATA = load_json("jmf.json")
JDV_DATA = load_json("jdv.json")
ITAB_DATA = load_json("itab.json")
FERTI_DATA = load_json("calcul_ferti.json")
RAW_JP1 = load_json("reglages_jp1.json")
REGLAGES_LISTE = RAW_JP1.get("reglages", [])

legumes_uniques = [l for l in set(list(GAB_DATA.keys()) + list(JMF_DATA.keys()) + list(JDV_DATA.keys())) 
                   if GAB_DATA.get(l) or JMF_DATA.get(l) or JDV_DATA.get(l)]
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
    st.write("") 
    
    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes)
    if sel != "---":
        st.session_state["view_mode"] = "LEGUME"
    
    st.divider()

    if st.button("⚙️ RÉGLAGES JP1 TERRADONIS", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_JP1"
        st.rerun()

    if st.button("🧪 CALCUL FERTI", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_FERTI"
        st.rerun()

    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""; cookies.save(); st.session_state["password_correct"] = False; st.rerun()

# ==========================================
# 5. AFFICHAGE CENTRAL
# ==========================================

# --- CAS : PAGE CALCUL FERTI ---
if st.session_state["view_mode"] == "PAGE_FERTI":
    st.title("🧪 CALCULATEUR DE FERTILISATION")
    
    longueur = st.number_input("Longueur de la planche (m)", value=20.0)
    largeur = st.number_input("Largeur de la planche (m)", value=0.75)
    
    surface = longueur * largeur
    st.write(f"Surface : {surface} m²")
    
    legume_ferti = st.selectbox("Légume :", options=sorted(list(FERTI_DATA.keys())) if FERTI_DATA else ["Aucune donnée"])
    
    if FERTI_DATA and legume_ferti in FERTI_DATA:
        res = FERTI_DATA[legume_ferti].get("JDV")
        if res:
            n = (res['N'] / 10000) * surface
            p = (res['P'] / 10000) * surface
            k = (res['K'] / 10000) * surface
            
            st.markdown("---")
            st.write(f"Besoins pour {surface} m² :")
            st.write(f"N : {n:.3f}")
            st.write(f"P : {p:.3f}")
            st.write(f"K : {k:.3f}")
        else:
            st.info("Référentiel JDV absent pour ce légume dans le fichier.")
    else:
        st.info("Le fichier calcul_ferti.json est vide ou introuvable.")

# --- CAS : RÉGLAGES JP1 ---
elif st.session_state["view_mode"] == "PAGE_JP1":
    st.title("⚙️ RÉGLAGES JP1 TERRADONIS")
    st.caption(f"Source : {RAW_JP1.get('source', '')}")
    st.markdown("---")
    
    st.subheader("📋 Réglages Techniques (Source : JMF)")
    DATA_JMF = load_json("reglages_jmf.json")
    if DATA_JMF:
        df_jmf = pd.DataFrame(DATA_JMF["reglages"])
        st.dataframe(df_jmf.rename(columns={"AV": "Pignon AV", "AR": "Pignon AR", "OBS": "Observations"}), use_container_width=True, hide_index=True)

    st.write("")
    st.divider()

    st.subheader("🌱 Guide de semis (Source : Terradonis / Terrain)")
    if "reglages" in RAW_JP1:
        df_terra = pd.DataFrame(RAW_JP1["reglages"])[["CULTURE", "ROULEAUX"]]
        st.dataframe(df_terra.sort_values("CULTURE"), use_container_width=True, hide_index=True)

# --- CAS : AFFICHAGE LÉGUME ---
elif st.session_state["view_mode"] == "LEGUME" and sel != "---":
    
    # --- EXTRACTION BESOIN NUTRITIONNEL JMF ---
    jmf_legume = JMF_DATA.get(sel, {})
    besoin_ferti = ""
    for k, v in jmf_legume.items():
        if "fertilisation" in k.lower() or "nutritionnel" in k.lower():
            besoin_ferti = v
            break

    # Titre dynamique avec le besoin nutritionnel
    if besoin_ferti:
        st.title(f"📊 {sel.upper()} — {besoin_ferti}")
    else:
        st.title(f"📊 {sel.upper()}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 GAB", "🚜 JMF", "🌿 JDV", "📗 ITAB", "📝 THO"])

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
                st.markdown(v); c1, c2 = st.columns([0.96, 0.04])
                with c2: popover_feedback("GAB", k, sel)

    with tab2:
        for t, c in jmf_legume.items():
            with st.expander(f"📌 {t}", expanded=True):
                st.markdown(c); c1, c2 = st.columns([0.96, 0.04])
                with c2: popover_feedback("JMF", t, sel)

    with tab3:
        for t, c in JDV_DATA.get(sel, {}).items():
            with st.expander(f"🌿 {t}", expanded=True):
                st.markdown(str(c)); c1, c2 = st.columns([0.96, 0.04])
                with c2: popover_feedback("JDV", t, sel)

    with tab4:
        itab = ITAB_DATA.get(sel, {})
        if itab:
            for t, c in itab.items():
                with st.expander(f"📗 {t}", expanded=True):
                    st.markdown(str(c)); c1, c2 = st.columns([0.96, 0.04])
                    with c2: popover_feedback("ITAB", t, sel)
        else:
            st.info("Aucune donnée ITAB disponible pour ce légume.")

    with tab5:
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

# --- CAS : ACCUEIL ---
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.markdown("---")
    st.markdown("### DLABAL - BDD ITK Maraîchage")
    st.info("👈 Sélectionnez un légume ou utilisez le calculateur de fertilisation dans la barre latérale.")

st.sidebar.markdown("---")
with st.sidebar:
    st.markdown("### 🌦️ Météo locale")
    components.html('<iframe width="150" height="300" frameborder="0" scrolling="no" src="https://meteofrance.com/widget/prevision/852810##3D6AA2" style="border: none;"></iframe>', height=310)
