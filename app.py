import streamlit as st
import json
import os
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_cookies_manager import EncryptedCookieManager

# ==========================================
# 1. CONFIGURATION, COOKIES ET SECURITE
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
        pwd = st.text_input("Entrez le mot de passe DLABAL :", type="password")
        submit = st.form_submit_button("Valider")
        if submit:
            if pwd == st.secrets["password"]:
                st.session_state["password_correct"] = True
                cookies["auth_token"] = "valide"
                cookies.save()
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
    return False

if not check_password():
    st.stop()

# Initialisation du cache pour le NOM
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
        
        try:
            df_existing = conn.read(spreadsheet=URL_SHEET2, worksheet=nom_sheet, ttl=0)
            df_updated = pd.concat([df_existing, new_row], ignore_index=True)
        except:
            df_updated = new_row
        
        conn.update(spreadsheet=URL_SHEET2, worksheet=nom_sheet, data=df_updated)
        st.toast(f"✅ Merci {nom_utilisateur} ! Feedback enregistré.", icon="🚀")
    except Exception as e:
        st.error(f"L'onglet '{nom_sheet}' doit être créé dans le GSheet Feedback.")
        
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

GAB_DATA = load_json("gab.json")
JMF_DATA = load_json("jmf.json")
JDV_DATA = load_json("jdv.json")
SOURCES_JMF = load_json("sources_jmf.json")
REGLAGES_JP1_OFFICIEL = load_json("reglages_jp1.json")

tous_les_legumes_potentiels = sorted(list(set(
    list(GAB_DATA.keys()) + 
    list(JMF_DATA.keys()) + 
    list(JDV_DATA.keys()) + 
    list(SOURCES_JMF.get("reglages_itk", {}).keys())
)))

tous_les_legumes = []
for leg in tous_les_legumes_potentiels:
    # On vérifie s'il y a de la donnée réelle quelque part
    has_gab = leg in GAB_DATA and GAB_DATA[leg] != {}
    has_jmf = leg in JMF_DATA and JMF_DATA[leg] != {}
    has_jdv = leg in JDV_DATA and JDV_DATA[leg] != {}
    has_itk = leg in SOURCES_JMF.get("reglages_itk", {})
    
    # Si le légume existe dans au moins un tab, on l'ajoute à la liste finale
    if has_gab or has_jmf or has_jdv or has_itk:
        tous_les_legumes.append(leg)

# ==========================================
# 3. SIDEBAR
# ==========================================
with st.sidebar:
    if st.button("**DLABAL**", key="btn_home", use_container_width=True):
        st.session_state["view_mode"] = "DOSSIER"
        st.session_state["last_sel"] = "---"
        st.session_state["reset_key"] = st.session_state.get("reset_key", 0) + 1
        st.rerun()
    
    st.markdown("<p style='font-size: 0.85em; color: gray; margin-top: -15px;'>Base de données maraîchère</p>", unsafe_allow_html=True)
    
    res_key = st.session_state.get("reset_key", 0)
    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes, key=f"sel_{res_key}")
    
    if sel != "---":
        if "last_sel" not in st.session_state or st.session_state["last_sel"] != sel:
            st.session_state["view_mode"] = "DOSSIER"
            st.session_state["last_sel"] = sel

    st.divider()
    if st.button("📊 RÉGLAGES JP1 GLOBAUX", use_container_width=True):
        st.session_state["view_mode"] = "JP1_GLOBAL"
        st.rerun()

    st.link_button("📩 Me contacter", "https://docs.google.com/forms/d/e/1FAIpQLSf0xs8AXpRAkZ4yChDo1HtarrAsxxnudS5TXMVtaZRwrbClmQ/viewform?usp=dialog", use_container_width=True)
    
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""
        cookies.save()
        st.session_state["password_correct"] = False
        st.rerun()

# ==========================================
# 4. LOGIQUE D'AFFICHAGE
# ==========================================

if st.session_state.get("view_mode") == "JP1_GLOBAL":
    st.title("🚜 RÉGLAGES OFFICIELS JP1")
    if st.button("⬅️ Retour au dossier"):
        st.session_state["view_mode"] = "DOSSIER"
        st.rerun()
    # (Le code JP1 global reste le même ici)

else:
    if sel == "---":
        st.title("🌱 Bienvenue sur DLABAL")
        st.info("👈 Sélectionnez un légume dans le menu à gauche.")
    else:
        st.title(f"📊 {sel.upper()}")
        tab1, tab2, tab3, tab4 = st.tabs(["📋 GAB / FRAB", "🚜 JMF", "🌿 JDV", "📝 THO"])

        # --- TAB 1 : GAB ---
        with tab1:
            g = GAB_DATA.get(sel, {})
            if g:
                if "BLOCS_IDENTITE" in g:
                    cols = st.columns(len(g["BLOCS_IDENTITE"]))
                    for i, b in enumerate(g["BLOCS_IDENTITE"]):
                        with cols[i]:
                            st.success(f"**{b['titre']}**\n\n{b['contenu']}")
                            pop = st.popover("📝", help=f"Suggérer une correction sur {b['titre']}")
                            with pop.form(key=f"fb_gab_id_{sel}_{i}"):
                                nom_input = st.text_input("Ton Nom :", value=st.session_state["user_name"], key=f"nom_gab_id_{i}")
                                msg = st.text_area("Ta suggestion :")
                                if st.form_submit_button("Envoyer"):
                                    st.session_state["user_name"] = nom_input # Mise en cache
                                    if not nom_input: st.error("Ton nom est requis.")
                                    else: envoyer_feedback(sel, "GAB", msg, b['titre'], nom_input)

                for k, v in g.get("TECHNIQUE", {}).items():
                    with st.expander(f"📌 {k}", expanded=True): 
                        st.markdown(v)
                        c1, c2 = st.columns([0.95, 0.05])
                        with c2:
                            pop = st.popover("📝", help=f"Suggérer une correction pour {k}")
                            with pop.form(key=f"fb_gab_tech_{sel}_{k}"):
                                nom_input = st.text_input("Ton Nom :", value=st.session_state["user_name"], key=f"nom_gab_tech_{k}")
                                msg = st.text_area("Ta suggestion :")
                                if st.form_submit_button("Envoyer"):
                                    st.session_state["user_name"] = nom_input
                                    if not nom_input: st.error("Ton nom est requis.")
                                    else: envoyer_feedback(sel, "GAB", msg, k, nom_input)

        # --- TAB 2 : JMF ---
        with tab2:
            f = JMF_DATA.get(sel, {})
            if f:
                for t, c in f.items():
                    with st.expander(f"📌 {t}", expanded=True):
                        st.markdown(c)
                        c1, c2 = st.columns([0.95, 0.05])
                        with c2:
                            pop = st.popover("📝", help=f"Suggérer une correction pour {t}")
                            with pop.form(key=f"fb_jmf_{sel}_{t}"):
                                nom_input = st.text_input("Ton Nom :", value=st.session_state["user_name"], key=f"nom_jmf_{t}")
                                msg = st.text_area("Ta suggestion :")
                                if st.form_submit_button("Envoyer"):
                                    st.session_state["user_name"] = nom_input
                                    if not nom_input: st.error("Ton nom est requis.")
                                    else: envoyer_feedback(sel, "JMF", msg, t, nom_input)

        # --- TAB 3 : JDV ---
        with tab3:
            j = JDV_DATA.get(sel, {})
            if j:
                for t, c in j.items():
                    with st.expander(f"🌿 {t}", expanded=True):
                        st.markdown(str(c))
                        c1, c2 = st.columns([0.95, 0.05])
                        with c2:
                            pop = st.popover("📝", help=f"Suggérer une correction pour {t}")
                            with pop.form(key=f"fb_jdv_{sel}_{t}"):
                                nom_input = st.text_input("Ton Nom :", value=st.session_state["user_name"], key=f"nom_jdv_{t}")
                                msg = st.text_area("Ta suggestion :")
                                if st.form_submit_button("Envoyer"):
                                    st.session_state["user_name"] = nom_input
                                    if not nom_input: st.error("Ton nom est requis.")
                                    else: envoyer_feedback(sel, "JDV", msg, t, nom_input)

        # --- TAB 4 : THO ---
        with tab4:
            st.subheader(f"📝 Saisie Terrain - {sel}")
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

# --- METEO SIDEBAR ---
st.sidebar.markdown("---")
with st.sidebar:
    st.markdown("### 🌦️ Météo locale")
    mf_iframe = """<iframe id="widget_autocomplete_preview" width="150" height="300" frameborder="0" scrolling="no" src="https://meteofrance.com/widget/prevision/852810##3D6AA2" style="display: block; margin: 0 auto; border: none;"></iframe>"""
    components.html(mf_iframe, height=310)

