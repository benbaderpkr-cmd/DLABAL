import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_cookies_manager import EncryptedCookieManager

# 1. CONFIGURATION ET COOKIES
st.set_page_config(page_title="DLABAL - SYSTÈME EXPERT", layout="wide", page_icon="🌱")

# Le manager de cookies permet de ne pas retaper le mot de passe à chaque F5
cookies = EncryptedCookieManager(password="cle_secrete_dlabal_2026")
if not cookies.ready():
    st.stop()

# 2. SYSTÈME DE MOT DE PASSE
def check_password():
    if st.session_state.get("password_correct") or cookies.get("auth_token") == "valide":
        st.session_state["password_correct"] = True
        return True
    
    st.title("🔐 Accès Restreint")
    pwd = st.text_input("Entrez le mot de passe DLABAL :", type="password")
    if st.button("Valider"):
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

# 4. CHARGEMENT DES DONNÉES
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
    st.markdown("""<div style="line-height: 1.3;"><span style="font-size: 24px; font-weight: bold;">DLABAL</span><br><span style="font-size: 15px; font-weight: bold;">Base de données des ITKs</span></div><br>""", unsafe_allow_html=True)
    
    sel = st.selectbox("Choisir ou taper le nom d'un légume :", ["---"] + tous_les_legumes)
    
    if sel != "---":
        if "last_sel" not in st.session_state or st.session_state["last_sel"] != sel:
            st.session_state["view_mode"] = "DOSSIER"
            st.session_state["last_sel"] = sel

    st.divider()
    if st.button("📊 RÉGLAGES JP1 GLOBAUX", use_container_width=True):
        st.session_state["view_mode"] = "JP1_GLOBAL"
        st.rerun()
    
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""
        cookies.save()
        st.session_state["password_correct"] = False
        st.rerun()

# --- LOGIQUE D'AFFICHAGE ---

# CAS A : LA PAGE JP1
if st.session_state.get("view_mode") == "JP1_GLOBAL":
    st.title("🚜 RÉGLAGES OFFICIELS JP1 (CONSTRUCTEUR)")
    st.warning("**⚠️ AVERTISSEMENT :** Ces réglages sont indicatifs. La précision dépend du contexte et du calibre de vos semences.")
    
    if st.button("⬅️ Retour au dossier"):
        st.session_state["view_mode"] = "DOSSIER"
        st.rerun()

    # 1. PRECONISATIONS
    liste = REGLAGES_JP1_OFFICIEL.get("reglages", [])
    if liste:
        st.subheader("📋 Préconisations par culture")
        with st.expander("💡 Suggérer un réglage"):
            with st.form("form_sug"):
                s_leg = st.text_input("Légume")
                s_note = st.text_input("Réglage (Rouleau / Pignons / Distance)")
                if st.form_submit_button("Envoyer la suggestion"):
                    st.success("Suggestion enregistrée (pensez à créer l'onglet SUGGESTIONS sur GSheet)")

        df_c = pd.DataFrame(liste)
        rech = st.text_input("🔍 Filtrer la liste globale...", key="filter_jp1")
        if rech: df_c = df_c[df_c['légume'].str.contains(rech, case=False)]
        st.dataframe(df_c.rename(columns={"légume":"Légume", "pignon_av":"AV", "pignon_ar":"AR", "distance_cm":"cm"}), use_container_width=True, hide_index=True)

    st.divider()
    
    # 2. TABLEAU DES DISTANCES (MM)
    st.subheader("⚙️ Tableau des distances de semis (en mm)")
    dist_data = {
        "Nombre de trous": ["2", "3", "4", "6", "8", "10", "12", "16", "20", "24", "30", "36"],
        "14/9": [320, 210, 160, 105, 80, 64, 53, 40, 32, 27, 21, 18],
        "14/10": [360, 230, 180, 115, 90, 72, 58, 45, 36, 29, 24, 20],
        "13/10": [380, 250, 190, 125, 95, 76, 63, 48, 38, 32, 25, 21],
        "13/11": [420, 280, 210, 140, 105, 84, 70, 53, 42, 35, 28, 23],
        "11/10": [460, 300, 230, 150, 115, 92, 75, 58, 46, 38, 31, 26],
        "11/11": [500, 330, 250, 165, 125, 100, 83, 63, 50, 42, 33, 28],
        "10/11": [540, 360, 270, 180, 135, 108, 90, 68, 54, 45, 36, 30],
        "11/13": [580, 390, 290, 195, 145, 116, 98, 73, 58, 49, 39, 32],
        "10/13": [640, 430, 320, 215, 160, 128, 108, 80, 64, 54, 43, 36],
        "10/14": [700, 460, 350, 230, 175, 140, 115, 88, 70, 58, 47, 39],
        "9/14": [760, 510, 380, 255, 190, 152, 128, 95, 76, 64, 51, 42]
    }
    st.dataframe(pd.DataFrame(dist_data), use_container_width=True, hide_index=True)
    
    st.divider()

    # 3. TABLEAU DES TROUS
    st.subheader("📏 Tableau des dimensions des trous des rouleaux (en mm)")
    c1, c2 = st.columns(2)
    with c1:
        st.table(pd.DataFrame({
            "Réf": ["A", "AA", "C", "F", "FJ", "G", "J", "L", "LJ", "M", "MJ", "MM", "N"],
            "Ø trou": ["13,50", "12,00", "11,00", "5,00", "5,00", "9,00", "SPECIAL", "7,00", "7,00", "5,00", "6,00", "6,00", "SPECIAL"],
            "Prof.": ["6,00", "6,00", "5,50", "2,50", "3,00", "4,50", "1,5 mm", "2,50", "3,70", "2,00", "3,50", "2,50", "16x6 mm"]
        }))
    with c2:
        st.table(pd.DataFrame({
            "Réf": ["R", "S-4", "U-4", "X", "XY", "XYY", "Y", "YJ", "YK", "YX", "YXX", "YYJ", "YYX"],
            "Ø trou": ["9,00", "SPECIAL", "SPECIAL", "4,00", "2,50", "2,00", "3,50", "3,00", "3,50", "2,50", "2,50", "3,00", "2,00"],
            "Prof.": ["3,50", "19x8 mm", "19x10 mm", "2,00", "1,20", "1,20", "1,50", "2,00", "2,30", "1,50", "1,80", "1,70", "1,80"]
        }))

# CAS B : LE DOSSIER (ACCUEIL OU FICHE)
else:
    if sel == "---":
        st.title("🌱 Bienvenue sur DLABAL")
        st.info("Sélectionnez un légume ci-contre ou consultez les réglages JP1 globaux.")
        
        # --- TON NOUVEAU TEXTE D'ACCUEIL ---
        st.markdown("### Une base de notes partagée, sans chichis.")
        st.markdown("""
        J’ai regroupé ici ce que j’ai pu glaner en formation ou sur le terrain. C’est sans prétention : 
        je ne cherche pas à donner de leçon, juste à mettre mes notes au propre pour qu'elles servent à d'autres. 
        L’outil est gratuit et je le bricole sur mon temps libre, donc c’est encore un peu rustique.

        **Si tu as de l'expérience à partager, n'hésite pas à mettre la main à la pâte :**

        * **Expériences de terrain :** Ça se passe dans l'onglet **THO**. Tes retours alimentent la base commune visible dans THO_RESULT.
        * **Réglages du semoir JP1 :** À gauche dans la page **Réglage JP1**, tu peux laisser tes propres réglages par légume. Ils sont compilés plus bas dans la section "Conseils persos JP1".

        L'idée, c'est que ça profite à tout le monde. Sers-toi, et complète si le cœur t'en dit.
        """)
        st.divider()

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

        with tab2:
            base = SOURCES_JMF.get("reglages_itk", {})
            reg = base.get(sel.strip())
            if reg:
                c1, c2 = st.columns(2)
                c1.info(f"**📍 JMF**\n- Rouleau : `{reg.get('jmf', {}).get('rouleau', '?')}`")
                c2.warning(f"**🚜 Terrateck**\n- Rouleau : `{reg.get('terrateck', {}).get('rouleau', '?')}`")
            f = DATA.get(sel, {}).get("JMF_FORTIER", {})
            for t, c in f.items():
                with st.expander(f"📌 {t}"): st.markdown(c)
                        
        with tab3:
            j = JDV_DATA.get(sel, {})
            if "RENDEMENT JDV" in j: st.success(f"**🚜 RENDEMENT JDV :** {j['RENDEMENT JDV']}")
            for t, c in j.items():
                if t != "RENDEMENT JDV":
                    with st.expander(f"🌿 {t}"): st.markdown(str(c))

        with tab4:
            st.subheader(f"📝 Saisie Terrain - {sel}")
            try:
                df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO", ttl=0)
                notes = df_gs[df_gs['LEGUME'] == sel].iloc[-1].to_dict() if not df_gs[df_gs['LEGUME'] == sel].empty else {}
            except: 
                df_gs = pd.DataFrame(columns=["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"])
                notes = {}
            
            with st.form(key=f"f_{sel}"):
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
