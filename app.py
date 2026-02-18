import streamlit as st
import json
import os
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuration de la page
st.set_page_config(page_title="DLABAL", layout="wide", page_icon="🌱")

# Connexion gsheet
SHEET_ID = "1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. FONCTIONS DE GESTION DES DONNÉES ---
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

# --- 2. CHARGEMENT INITIAL ---
DATA = load_json("data.json")
tous_les_legumes = sorted(list(DATA.keys()))

# --- 3. BARRE LATÉRALE ---
st.sidebar.title("🌱 DLABAL")
sel = st.sidebar.selectbox("Choisir un légume :", ["---"] + tous_les_legumes, key="main_selector")

# --- 4. CONTENU PRINCIPAL ---
if sel != "---":
    st.title(f"📊 {sel.upper()}")
    
    JDV_DATA = load_json("jdv.json")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 SOURCE GAB", 
        "🚜 SOURCE JMF", 
        "🌿 SOURCE JDV", 
        "📝 SOURCE THO"
    ])

    # --- SOURCE GAB / JMF / JDV (Style conservé) ---
    with tab1:
        g = DATA.get(sel, {}).get("GAB_FRAB", {})
        if g:
            for k, v in g.get("TECHNIQUE", {}).items():
                with st.expander(f"📌 {k}", expanded=True):
                    st.markdown(v)
    with tab2:
        f = DATA.get(sel, {}).get("JMF_FORTIER", {})
        if f:
            for titre, contenu in f.items():
                with st.expander(f"📌 {titre}", expanded=True):
                    st.markdown(contenu)
    with tab3:
        j = JDV_DATA.get(sel, {})
        if j:
            for t, c in j.items():
                with st.expander(f"🌿 {t}", expanded=True):
                    st.markdown(c)

    # --- SOURCE THO ---
    # --- ONGLET 4 : SOURCE THO ---
    with tab4:
        st.subheader(f"📝 Notes de culture : {sel}")
        
        # Initialisation de df et notes pour éviter les erreurs 'not defined'
        cols = ["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"]
        df_actuel = pd.DataFrame(columns=cols)
        notes = {}

        try:
            df_lu = conn.read(spreadsheet=SHEET_ID, worksheet="THO", ttl=0)
            if df_lu is not None and not df_lu.empty:
                df_actuel = df_lu
                df_actuel.columns = [c.strip().upper() for c in df_actuel.columns]
                if 'LEGUME' in df_actuel.columns:
                    existing = df_actuel[df_actuel['LEGUME'] == sel]
                    if not existing.empty:
                        notes = existing.iloc[-1].to_dict()
            st.success("✅ Connecté")
        except:
            st.warning("⚠️ Prêt pour premier enregistrement")

        # DEBUT DU FORMULAIRE
        with st.form(key=f"form_tho_{sel}"):
            c1, c2 = st.columns(2)
            with c1:
                v_plan = st.text_area("🌱 PLANTATION", value=str(notes.get("PLANTATION", "")), key=f"p_{sel}")
                v_entr = st.text_area("🛠️ ENTRETIEN", value=str(notes.get("ENTRETIEN", "")), key=f"e_{sel}")
                v_sant = st.text_area("🏥 SANTE", value=str(notes.get("SANTE", "")), key=f"s_{sel}")
            with c2:
                v_rend = st.text_area("📊 RENDEMENT", value=str(notes.get("RENDEMENT", "")), key=f"r_{sel}")
                v_vari = st.text_area("🧬 VARIETE", value=str(notes.get("VARIETE", "")), key=f"v_{sel}")
                v_info = st.text_area("➕ INFO SUPP", value=str(notes.get("INFO_SUPP", "")), key=f"i_{sel}")

            # LE BOUTON DOIT ETRE ICI (Aligné avec 'c1, c2' et 'with c1')
            submit = st.form_submit_button("💾 ENREGISTRER DANS GOOGLE SHEETS")

        # LA LOGIQUE APRES LE BOUTON (Hors du bloc 'with st.form' ou dedans, mais 'submit' doit être défini)
        if submit:
            try:
                nouvelle_ligne = {
                    "LEGUME": sel, "PLANTATION": v_plan, "ENTRETIEN": v_entr,
                    "SANTE": v_sant, "RENDEMENT": v_rend, "VARIETE": v_vari, "INFO_SUPP": v_info
                }
                
                if not df_actuel.empty and 'LEGUME' in df_actuel.columns:
                    df_actuel = df_actuel[df_actuel['LEGUME'] != sel]
                
                df_final = pd.concat([df_actuel, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
                df_final = df_final.reindex(columns=cols)
                
                conn.update(spreadsheet=SHEET_ID, worksheet="THO", data=df_final)
                st.cache_data.clear() 
                st.success("✨ Données enregistrées !")
                st.balloons()
            except Exception as e:
                if "200" in str(e):
                    st.success("✨ Enregistré !")
                    st.balloons()
                else:
                    st.error(f"Erreur : {e}")
else:
    st.info("Sélectionnez un légume.")

