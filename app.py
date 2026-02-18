import streamlit as st
import json
import os
import pandas as pd
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
    
    # SÉLECTEUR AVEC LE NOUVEAU LIBELLÉ (Moteur de recherche suggéré)
    sel = st.selectbox(
        "Choisir ou taper le nom d'un légume :", 
        ["---"] + tous_les_legumes,
        help="Tapez les premières lettres pour filtrer rapidement les cultures."
    )
    
    st.divider()

    # BOUTON FIXE REGLAGE JP1
    if st.button("📊 RÉGLAGES JP1", use_container_width=True):
        st.session_state["view_mode"] = "JP1_GLOBAL"
    
    # Reset du mode si un légume est sélectionné
    if sel != "---" and st.session_state.get("last_sel") != sel:
        st.session_state["view_mode"] = "DOSSIER"
        st.session_state["last_sel"] = sel

# --- LOGIQUE D'AFFICHAGE DU CONTENU ---

# MODE 1 : TABLEAU GLOBAL JP1 (Données Constructeur + Abaques techniques)
if st.session_state.get("view_mode") == "JP1_GLOBAL":
    st.title("🚜 RÉGLAGES OFFICIELS JP1 (CONSTRUCTEUR)")
    
    # Annotation de prévention
    st.warning("""
    **⚠️ AVERTISSEMENT :** Ces réglages proviennent du croisement des guides techniques Terrateck et Terradonis. 
    Ils ne constituent pas une référence absolue. La précision dépend du contexte (préparation du sol, humidité) 
    et du calibre exact de vos semences. Ajustez selon vos propres objectifs de distance.
    """)
    
    if st.button("⬅️ Retour au dossier"):
        st.session_state["view_mode"] = "DOSSIER"
        st.rerun()

    # Section 1 : Préconisations par culture
    liste = REGLAGES_JP1_OFFICIEL.get("reglages", [])
    if liste:
        st.subheader("📋 Préconisations par culture")
        df = pd.DataFrame(liste)
        recherche = st.text_input("🔍 Filtrer la liste globale...", "")
        if recherche:
            df = df[df['légume'].str.contains(recherche, case=False)]
        
        st.dataframe(df.rename(columns={
            "légume": "Légume", "pignon_av": "Pignon AV", "pignon_ar": "Pignon AR", "distance_cm": "Distance (cm)"
        }), use_container_width=True, hide_index=True)
    
    st.divider()

    # Section 2 : Abaques Techniques de référence
    st.subheader("🛠️ Références Mécaniques (Abaques Terradonis)")
    
    col_trous, col_dist = st.columns(2)
    
    with col_trous:
        st.markdown("**📏 Dimensions des trous des rouleaux**")
        data_trous = {
            "Code Rouleau": ["YYJ", "YYX", "XY", "X", "Y", "F", "LJ", "N", "MJ", "M", "L", "AA"],
            "Diamètre (mm)": ["2.0", "2.5", "3.0", "3.5", "4.0", "5.0", "7.5", "8.0", "8.5", "9.0", "10.0", "12.0"]
        }
        st.table(pd.DataFrame(data_trous))
        
    with col_dist:
        st.markdown("**⚙️ Tableau des distances mécaniques**")
        data_dist = {
            "Pignons (AV/AR)": ["14 / 11", "13 / 11", "11 / 11", "11 / 13", "11 / 14", "10 / 14", "9 / 14"],
            "6 trous (mm)": ["95", "105", "110", "130", "140", "155", "170"],
            "12 trous (mm)": ["45", "50", "55", "65", "70", "75", "85"],
            "24 trous (mm)": ["23", "25", "28", "33", "35", "38", "43"]
        }
        st.table(pd.DataFrame(data_dist))

    st.caption("Source : Manuel utilisateur JP1 - Terradonis (www.terradonis.com)")

# MODE 2 : DOSSIER MARAÎCHAGE (Affichage par onglets)
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
            reglages_propres = {str(k).strip(): v for k, v in base.items()}
            reglages = reglages_propres.get(sel.strip())

            if reglages and isinstance(reglages, dict):
                st.markdown(f"### ⚙️ Configuration Semoir JP1 : {sel}")
                col_pdf, col_terra = st.columns(2)
                with col_pdf:
                    st.info("**📍 Réglages JMF (Fiches PDF)**")
                    r_j = reglages.get("jmf", {})
                    st.markdown(f"- **Rouleau :** `{r_j.get('rouleau', 'N/A')}`\n- **Pignons (AV/AR) :** `{r_j.get('pignon_av', '?')} / {r_j.get('pignon_ar', '?')}`\n- **Brosse :** `{r_j.get('brosse', 'Standard')}`")
                with col_terra:
                    st.warning("**🚜 Réglages Site Terrateck / Jang**")
                    r_t = reglages.get("terrateck", {})
                    st.markdown(f"- **Rouleau :** `{r_t.get('rouleau', 'N/A')}`\n- **Pignons (AV/AR) :** `{r_t.get('pignon_av', '?')} / {r_t.get('pignon_ar', '?')}`\n- **Note :** *{r_t.get('obs', '-')}*")
                st.divider()

            f = DATA.get(sel, {}).get("JMF_FORTIER", {})
            if f:
                for t, c in f.items():
                    with st.expander(f"📌 {t}", expanded=True):
                        st.markdown(c)
                        
        # --- TAB 3 : JDV ---
        with tab3:
            j = JDV_DATA.get(sel, {})
            if j:
                if "RENDEMENT JDV" in j:
                    st.success(f"**🚜 RENDEMENT JDV :** {j['RENDEMENT JDV']}")
                for t, c in j.items():
                    if t != "RENDEMENT JDV":
                        with st.expander(f"🌿 {t}", expanded=True):
                            st.markdown(str(c).replace('\n', '\n\n'))

        # --- TAB 4 : THO ---
        with tab4:
            st.subheader(f"📝 Saisie Terrain - {sel}")
            cols_gs = ["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"]
            df_gs = pd.DataFrame(columns=cols_gs)
            notes = {}
            try:
                df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO", ttl=0)
                if df_gs is not None and not df_gs.empty:
                    existing = df_gs[df_gs['LEGUME'] == sel]
                    if not existing.empty: notes = existing.iloc[-1].to_dict()
            except: pass

            with st.form(key=f"f_{sel}"):
                c1, c2 = st.columns(2)
                with c1:
                    v_p = st.text_area("🌱 PLANTATION", value=str(notes.get("PLANTATION", "")), key=f"p_{sel}")
                    v_e = st.text_area("🛠️ ENTRETIEN", value=str(notes.get("ENTRETIEN", "")), key=f"e_{sel}")
                    v_s = st.text_area("🏥 SANTE", value=str(notes.get("SANTE", "")), key=f"s_{sel}")
                with c2:
                    v_r = st.text_area("📊 RENDEMENT", value=str(notes.get("RENDEMENT", "")), key=f"r_{sel}")
                    v_v = st.text_area("🧬 VARIETE", value=str(notes.get("VARIETE", "")), key=f"v_{sel}")
                    v_i = st.text_area("➕ INFO SUPP", value=str(notes.get("INFO_SUPP", "")), key=f"i_{sel}")
                if st.form_submit_button("💾 ENREGISTRER"):
                    new_row = {"LEGUME": sel, "PLANTATION": v_p, "ENTRETIEN": v_e, "SANTE": v_s, "RENDEMENT": v_r, "VARIETE": v_v, "INFO_SUPP": v_i}
                    if not df_gs.empty: df_gs = df_gs[df_gs['LEGUME'] != sel]
                    df_final = pd.concat([df_gs, pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(spreadsheet=URL_SHEET, worksheet="THO", data=df_final)
                    st.cache_data.clear()
                    st.success("Enregistré !")
                    st.balloons()
