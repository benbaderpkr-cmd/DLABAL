import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION
st.set_page_config(page_title="DLABAL - SYSTÈME EXPERT", layout="wide", page_icon="🌱")

# 2. SYSTÈME DE MOT DE PASSE
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    st.title("🔐 Accès Restreint")
    pwd = st.text_input("Entrez le mot de passe pour accéder à DLABAL :", type="password")
    if st.button("Valider"):
        if pwd == st.secrets["password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
    return False

if not check_password():
    st.stop()

# 3. CONNEXION GSHEETS
URL_SHEET = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. CHARGEMENT DES DONNÉES LOCALES
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = json.load(f)
                return content if isinstance(content, dict) else {}
        except Exception as e:
            st.error(f"Erreur de lecture du fichier {filename} : {e}")
            return {}
    return {}

DATA = load_json("data.json")
JDV_DATA = load_json("jdv.json")
SOURCES_JMF = load_json("sources_jmf.json")
REGLAGES_JP1_OFFICIEL = load_json("reglages_jp1.json")

# Préparation de la liste des légumes
cles_itk = list(SOURCES_JMF.get("reglages_itk", {}).keys())
tous_les_legumes = sorted(list(set(list(DATA.keys()) + list(JDV_DATA.keys()) + cles_itk)))

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style="line-height: 1.3;">
            <span style="font-size: 24px; font-weight: bold;">DLABAL</span><br>
            <span style="font-size: 15px; font-weight: bold;">Base de données des ITKs</span><br>
            <span style="font-size: 12px; color: gray;">DB LA Braille Aux Loups</span>
        </div>
        <br>
    """, unsafe_allow_html=True)
    
    # SÉLECTEUR
    sel = st.selectbox(
        "Choisir ou taper le nom d'un légume :", 
        ["---"] + tous_les_legumes,
        help="Tapez les premières lettres pour filtrer rapidement."
    )
    
    # LOGIQUE DE RÉINITIALISATION : Si le légume change, on revient au mode DOSSIER
    if sel != "---":
        if "last_sel" not in st.session_state or st.session_state["last_sel"] != sel:
            st.session_state["view_mode"] = "DOSSIER"
            st.session_state["last_sel"] = sel

    st.divider()

    # BOUTON RÉGLAGES JP1
    if st.button("📊 RÉGLAGES JP1 GLOBAUX", use_container_width=True):
        st.session_state["view_mode"] = "JP1_GLOBAL"
        st.rerun()

# --- LOGIQUE D'AFFICHAGE DU CONTENU ---

# CAS 1 : MODE RÉGLAGES JP1
if st.session_state.get("view_mode") == "JP1_GLOBAL":
    st.title("🚜 RÉGLAGES OFFICIELS JP1 (CONSTRUCTEUR)")
    
    st.warning("""
    **⚠️ AVERTISSEMENT :** Ces réglages proviennent du croisement des guides techniques Terrateck et Terradonis. 
    Ils ne constituent pas une référence absolue. Ajustez selon vos propres objectifs de distance.
    """)
    
    # SECTION 1 : PRÉCONISATIONS PAR CULTURE
    liste = REGLAGES_JP1_OFFICIEL.get("reglages", [])
    if liste:
        st.subheader("📋 Préconisations par culture")
        
        with st.expander("💡 Suggérer un nouveau réglage ou une correction"):
            with st.form("form_suggestion"):
                col_s1, col_s2, col_s3 = st.columns(3)
                s_leg = col_s1.text_input("Légume")
                s_rou = col_s2.text_input("Rouleau (ex: XY-24)")
                s_dist = col_s3.text_input("Distance visée (cm)")
                col_s4, col_s5, col_s6 = st.columns(3)
                s_pav = col_s4.number_input("Pignon AV", 9, 14, 11)
                s_par = col_s5.number_input("Pignon AR", 9, 14, 11)
                s_note = col_s6.text_input("Note / Observation")
                
                if st.form_submit_button("Envoyer la suggestion"):
                    try:
                        df_sug = conn.read(spreadsheet=URL_SHEET, worksheet="SUGGESTIONS")
                        new_sug = pd.DataFrame([{
                            "DATE": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "LEGUME": s_leg, "ROULEAU": s_rou, "PIGNON_AV": s_pav, 
                            "PIGNON_AR": s_par, "DISTANCE": s_dist, "NOTE": s_note
                        }])
                        df_final_sug = pd.concat([df_sug, new_sug], ignore_index=True)
                        conn.update(spreadsheet=URL_SHEET, worksheet="SUGGESTIONS", data=df_final_sug)
                        st.success("Suggestion enregistrée !")
                    except:
                        st.error("Onglet 'SUGGESTIONS' manquant dans GSheets.")

        df_culture = pd.DataFrame(liste)
        recherche = st.text_input("🔍 Filtrer la liste...", "")
        if recherche:
            df_culture = df_culture[df_culture['légume'].str.contains(recherche, case=False)]
        
        st.dataframe(df_culture.rename(columns={
            "légume": "Légume", "pignon_av": "Pignon AV", "pignon_ar": "Pignon AR", "distance_cm": "Distance (cm)"
        }), use_container_width=True, hide_index=True)

    st.divider()

    # SECTION 2 : DISTANCES (PAGE 4)
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

    # SECTION 3 : TROUS (PAGE 4)
    st.subheader("📏 Tableau des dimensions des trous des rouleaux (en mm)")
    c1, c2 = st.columns(2)
    with c1:
        trous_a = {
            "Réf": ["A", "AA", "C", "F", "FJ", "G", "J", "L", "LJ", "M", "MJ", "MM", "N"],
            "Ø trou": ["13,50", "12,00", "11,00", "5,00", "5,00", "9,00", "SPECIAL", "7,00", "7,00", "5,00", "6,00", "6,00", "SPECIAL"],
            "Prof.": ["6,00", "6,00", "5,50", "2,50", "3,00", "4,50", "1,5 mm", "2,50", "3,70", "2,00", "3,50", "2,50", "16x6 mm"]
        }
        st.table(pd.DataFrame(trous_a))
    with c2:
        trous_b = {
            "Réf": ["R", "S-4", "U-4", "X", "XY", "XYY", "Y", "YJ", "YK", "YX", "YXX", "YYJ", "YYX"],
            "Ø trou": ["9,00", "SPECIAL", "SPECIAL", "4,00", "2,50", "2,00", "3,50", "3,00", "3,50", "2,50", "2,50", "3,00", "2,00"],
            "Prof.": ["3,50", "19x8 mm", "19x10 mm", "2,00", "1,20", "1,20", "1,50", "2,00", "2,30", "1,50", "1,80", "1,70", "1,80"]
        }
        st.table(pd.DataFrame(trous_b))
    st.caption("Source : Manuel utilisateur JP1 - Terradonis - Page 4")

# CAS 2 : MODE DOSSIER (Légume sélectionné)
else:
    if sel == "---":
        st.title("🌱 Bienvenue sur DLABAL")
        st.info("Sélectionnez un légume ci-contre ou consultez les réglages JP1 globaux.")
    else:
        st.title(f"📊 {sel.upper()}")
        tab1, tab2, tab3, tab4 = st.tabs(["📋 GAB / FRAB", "🚜 JMF", "🌿 JDV", "📝 THO"])

        # --- TAB 1 : GAB ---
        with tab1:
            g = DATA.get(sel, {}).get("GAB_FRAB", {})
            if g:
                if "BLOCS_IDENTITE" in g:
                    blocs = g["BLOCS_IDENTITE"]
                    cols = st.columns(len(blocs))
                    for i, b in enumerate(blocs):
                        cols[i].success(f"**{b['titre']}**\n\n{b['contenu']}")
                for k, v in g.get("TECHNIQUE", {}).items():
                    with st.expander(f"📌 {k}", expanded=True):
                        st.markdown(v)
            else: st.warning("Données GAB absentes.")

        # --- TAB 2 : JMF ---
        with tab2:
            base = SOURCES_JMF.get("reglages_itk", SOURCES_JMF)
            reglages = base.get(sel.strip())
            if reglages and isinstance(reglages, dict):
                st.markdown(f"### ⚙️ Configuration Semoir JP1 : {sel}")
                c_j, c_t = st.columns(2)
                with c_j:
                    r_j = reglages.get("jmf", {})
                    st.info(f"**📍 JMF**\n- Rouleau : `{r_j.get('rouleau', '?')}`\n- Pignons : `{r_j.get('pignon_av', '?')}/{r_j.get('pignon_ar', '?')}`")
                with c_t:
                    r_t = reglages.get("terrateck", {})
                    st.warning(f"**🚜 Terrateck**\n- Rouleau : `{r_t.get('rouleau', '?')}`\n- Pignons : `{r_t.get('pignon_av', '?')}/{r_t.get('pignon_ar', '?')}`")
            f = DATA.get(sel, {}).get("JMF_FORTIER", {})
            if f:
                for t, c in f.items():
                    with st.expander(f"📌 {t}", expanded=True):
                        st.markdown(c)

        # --- TAB 3 : JDV ---
        with tab3:
            j = JDV_DATA.get(sel, {})
            if j:
                if "RENDEMENT JDV" in j: st.success(f"**🚜 RENDEMENT JDV :** {j['RENDEMENT JDV']}")
                for t, c in j.items():
                    if t != "RENDEMENT JDV":
                        with st.expander(f"🌿 {t}", expanded=True): st.markdown(str(c))

        # --- TAB 4 : THO ---
        with tab4:
            st.subheader(f"📝 Saisie Terrain - {sel}")
            try:
                df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO", ttl=0)
                notes = df_gs[df_gs['LEGUME'] == sel].iloc[-1].to_dict() if not df_gs[df_gs['LEGUME'] == sel].empty else {}
            except: 
                df_gs = pd.DataFrame(columns=["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"])
                notes = {}

            with st.form(key=f"form_{sel}"):
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
