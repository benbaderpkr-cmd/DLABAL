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
                # On vérifie si c'est bien un dictionnaire
                return content if isinstance(content, dict) else {}
        except Exception as e:
            st.error(f"Erreur de lecture du fichier {filename} : {e}")
            return {}
    return {}

DATA = load_json("data.json")
JDV_DATA = load_json("jdv.json")
SOURCES_JMF = load_json("sources_jmf.json")

# Création de la liste des légumes (priorité aux réglages JP1 pour être sûr qu'ils apparaissent)
cles_jp1 = list(SOURCES_JMF.get("reglages_itk", {}).keys())
tous_les_legumes = sorted(list(set(list(DATA.keys()) + list(JDV_DATA.keys()) + cles_jp1)))

# --- SIDEBAR ---
st.sidebar.markdown("""
    <div style="line-height: 1.3;">
        <span style="font-size: 24px; font-weight: bold;">DLABAL</span><br>
        <span style="font-size: 15px; font-weight: bold;">Base de données des ITKs (GAB, JMF, JDV)</span><br>
        <span style="font-size: 12px; color: gray;">DB LA Braille Aux Loups</span>
    </div>
    <br>
""", unsafe_allow_html=True)

sel = st.sidebar.selectbox("Choisir un légume :", ["---"] + tous_les_legumes)

# --- CONTENU PRINCIPAL ---
if sel != "---":
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
        # On essaie de récupérer reglages_itk, sinon on prend le dictionnaire entier
        base = SOURCES_JMF.get("reglages_itk", SOURCES_JMF)
        
        # Nettoyage des clés pour éviter les erreurs d'espaces ou de majuscules
        reglages_propres = {str(k).strip(): v for k, v in base.items()}
        
        # Recherche du légume
        reglages = reglages_propres.get(sel.strip())

        if reglages and isinstance(reglages, dict):
            st.markdown(f"### ⚙️ Configuration Semoir JP1 : {sel}")
            col_pdf, col_terra = st.columns(2)
            
            with col_pdf:
                st.info("**📍 Réglages JMF (Fiches PDF)**")
                r_j = reglages.get("jmf", {})
                st.markdown(f"""
                - **Rouleau :** `{r_j.get('rouleau', 'N/A')}`
                - **Pignons (AV/AR) :** `{r_j.get('pignon_av', '?')} / {r_j.get('pignon_ar', '?')}`
                - **Brosse :** `{r_j.get('brosse', 'Standard')}`
                - **Nombre de rangs :** `{r_j.get('rangs', '?')}`
                """)
            
            with col_terra:
                st.warning("**🚜 Réglages Site Terrateck / Jang**")
                r_t = reglages.get("terrateck", {})
                st.markdown(f"""
                - **Rouleau :** `{r_t.get('rouleau', 'N/A')}`
                - **Pignons (AV/AR) :** `{r_t.get('pignon_av', '?')} / {r_t.get('pignon_ar', '?')}`
                - **Brosse :** `{r_t.get('brosse', 'Standard')}`
                - **Note :** *{r_t.get('obs', '-')}*
                """)
            st.divider()
        else:
            # Si toujours vide, on affiche un message d'aide
            if not SOURCES_JMF:
                st.error("⚠️ Le fichier 'sources_jmf.json' semble vide ou n'a pas pu être chargé.")
            else:
                st.warning(f"ℹ️ Aucun réglage JP1 trouvé pour '{sel}'.")
                with st.expander("Diagnostic technique (clés lues)"):
                    st.write(list(reglages_propres.keys()))

        # Suite : Contenu textuel JMF
        f = DATA.get(sel, {}).get("JMF_FORTIER", {})
        if f:
            for t, c in f.items():
                with st.expander(f"📌 {t}", expanded=False):
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

    # --- TAB 4 : THO (GSheets) ---
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



