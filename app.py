import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_cookies_manager import EncryptedCookieManager

# 1. CONFIGURATION ET COOKIES
st.set_page_config(page_title="DLABAL - SYSTÈME EXPERT", layout="wide", page_icon="🌱")

cookies = EncryptedCookieManager(password="cle_secrete_dlabal_2026")
if not cookies.ready():
    st.stop()

# 2. SYSTÈME DE MOT DE PASSE (Validation par touche Entrée via formulaire)
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

# 3. CONNEXION GSHEETS
URL_SHEET = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. CHARGEMENT DES DONNÉES JSON
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

DATA = load_json("data.json")
JDV_DATA = load_json("jdv.json")
SOURCES_JMF = load_json("sources_jmf.json")
REGLAGES_JP1_OFFICIEL = load_json("reglages_jp1.json")

cles_itk = list(SOURCES_JMF.get("reglages_itk", {}).keys())
tous_les_legumes = sorted(list(set(list(DATA.keys()) + list(JDV_DATA.keys()) + cles_itk)))

# --- SIDEBAR ---
with st.sidebar:
    # 1. TITRE DLABAL GRAS + LIEN ACCUEIL
    if st.button("DLABAL", key="btn_home", use_container_width=True, type="secondary"):
        st.session_state["view_mode"] = "DOSSIER"
        st.session_state["last_sel"] = "---"
        st.session_state["reset_key"] = st.session_state.get("reset_key", 0) + 1
        st.rerun()
    
    # 2. SOUS-TITRE PLUS PETIT
    st.markdown("<p style='font-size: 0.85em; color: gray; margin-top: -15px; margin-bottom: 20px;'>Base de données maraîchère</p>", unsafe_allow_html=True)
    
    # 3. DROPDOWN
    res_key = st.session_state.get("reset_key", 0)
    sel = st.selectbox(
        "Choisir un légume :", 
        ["---"] + tous_les_legumes,
        key=f"selection_legume_{res_key}"
    )
    
    if sel != "---":
        if "last_sel" not in st.session_state or st.session_state["last_sel"] != sel:
            st.session_state["view_mode"] = "DOSSIER"
            st.session_state["last_sel"] = sel

    st.divider()
    
    # 4. BOUTONS EN PETIT (Format compact Streamlit)
    if st.button("📊 RÉGLAGES JP1 GLOBAUX", use_container_width=True):
        st.session_state["view_mode"] = "JP1_GLOBAL"
        st.rerun()
    
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""
        cookies.save()
        st.session_state["password_correct"] = False
        st.rerun()

# --- LOGIQUE D'AFFICHAGE ---

if st.session_state.get("view_mode") == "JP1_GLOBAL":
    st.title("🚜 RÉGLAGES OFFICIELS JP1")
    
    if st.button("⬅️ Retour"):
        st.session_state["view_mode"] = "DOSSIER"
        st.rerun()

    with st.expander("💡 Propose ton réglage du JP1.", expanded=False):
        with st.form("form_sug_jp1", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            s_leg = c1.text_input("Légume concerné")
            s_rouleau = c2.text_input("rouleau")
            s_pav = c3.text_input("pignon AV")
            c4, c5, c6 = st.columns(3)
            s_par = c4.text_input("pignon AR")
            s_brosse = c5.text_input("Brosse")
            s_info = c6.text_input("info supp.")
            if st.form_submit_button("Enregistrer"):
                if s_leg and s_rouleau:
                    try:
                        df_sug = conn.read(spreadsheet=URL_SHEET, worksheet="SUGGESTIONS", ttl=0)
                    except:
                        df_sug = pd.DataFrame(columns=["DATE", "LEGUME", "ROULEAU", "PIGNON_AV", "PIGNON_AR", "BROSSE", "INFO_SUPP"])
                    new_sug = pd.DataFrame([{"DATE": datetime.now().strftime("%d/%m/%Y"), "LEGUME": s_leg, "ROULEAU": s_rouleau, "PIGNON_AV": s_pav, "PIGNON_AR": s_par, "BROSSE": s_brosse, "INFO_SUPP": s_info}])
                    df_updated = pd.concat([df_sug, new_sug], ignore_index=True)
                    conn.update(spreadsheet=URL_SHEET, worksheet="SUGGESTIONS", data=df_updated)
                    st.success("Envoyé !")
                else:
                    st.error("Champs requis : Légume et Rouleau.")

    st.divider()
    liste = REGLAGES_JP1_OFFICIEL.get("reglages", [])
    if liste:
        df_c = pd.DataFrame(liste)
        rech = st.text_input("🔍 Filtrer...", key="filter_jp1")
        if rech: 
            df_c = df_c[df_c['légume'].str.contains(rech, case=False)]
        st.dataframe(df_c.rename(columns={"légume":"Légume", "pignon_av":"AV", "pignon_ar":"AR", "distance_cm":"cm"}), use_container_width=True, hide_index=True)

else:
    if sel == "---":
        st.title("🌱 DLABAL")
        st.markdown("### Base de notes partagée")
        st.info("Sélectionnez un légume dans le menu à gauche pour commencer.")
    else:
        st.title(f"📊 {sel.upper()}")
        tab1, tab2, tab3, tab4 = st.tabs(["📋 GAB / FRAB", "🚜 JMF", "🌿 JDV", "📝 THO"])

        with tab1:
            g = DATA.get(sel, {}).get("GAB_FRAB", {})
            if g:
                if "BLOCS_IDENTITE" in g:
                    cols = st.columns(len(g["BLOCS_IDENTITE"]))
                    for i, b in enumerate(g["BLOCS_IDENTITE"]):
                        cols[i].success(f"**{b['titre']}**\n\n{b['contenu']}")
                for k, v in g.get("TECHNIQUE", {}).items():
                    with st.expander(f"📌 {k}", expanded=True): st.markdown(v)
            else:
                st.info(f"Aucune donnée de GAB / FRAB pour {sel}")

        with tab2:
            found_jmf = False
            base = SOURCES_JMF.get("reglages_itk", {})
            reg = base.get(sel.strip())
            if reg:
                found_jmf = True
                c1, c2 = st.columns(2)
                c1.info(f"**📍 JMF**\n- Rouleau : `{reg.get('jmf', {}).get('rouleau', '?')}`")
                c2.warning(f"**🚜 Terrateck**\n- Rouleau : `{reg.get('terrateck', {}).get('rouleau', '?')}`")
            f = DATA.get(sel, {}).get("JMF_FORTIER", {})
            if f:
                found_jmf = True
                for t, c in f.items():
                    with st.expander(f"📌 {t}", expanded=True): st.markdown(c)
            if not found_jmf:
                st.info(f"Aucune donnée de JMF pour {sel}")
                        
        with tab3:
            j = JDV_DATA.get(sel, {})
            if j:
                if "RENDEMENT JDV" in j: st.success(f"**🚜 RENDEMENT JDV :** {j['RENDEMENT JDV']}")
                for t, c in j.items():
                    if t != "RENDEMENT JDV":
                        with st.expander(f"🌿 {t}", expanded=True): st.markdown(str(c))
            else:
                st.info(f"Aucune donnée de JDV pour {sel}")

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
                    st.success("Enregistré !")
