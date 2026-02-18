import streamlit as st
import json
import os
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuration de la page
st.set_page_config(page_title="DLABAL", layout="wide", page_icon="🌱")

# Connexion gsheet (ID centralisé ici)
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

    # --- ONGLET 1 : GAB/FRAB ---
    with tab1:
        g = DATA.get(sel, {}).get("GAB_FRAB", {})
        if g:
            for k, v in g.get("TECHNIQUE", {}).items():
                with st.expander(f"📌 {k}", expanded=True):
                    st.markdown(v)
        else: st.warning("Données GAB absentes.")

    # --- ONGLET 2 : JMF ---
    with tab2:
        f = DATA.get(sel, {}).get("JMF_FORTIER", {})
        if f:
            for titre, contenu in f.items():
                with st.expander(f"📌 {titre}", expanded=True):
                    st.markdown(contenu)
        else: st.warning("Données JMF absentes.")

    # --- ONGLET 3 : JDV ---
    with tab3:
        j = JDV_DATA.get(sel, {})
        if j:
            for t, c in j.items():
                with st.expander(f"🌿 {t}", expanded=True):
                    st.markdown(c)
        else: st.warning("Données JDV absentes.")

    # --- ONGLET 4 : SAISIE TERRAIN (GOOGLE SHEETS) ---
    with tab4:
        st.subheader(f"📝 Notes de culture : {sel}")
        
        try:
            # Lecture des données fraîches
            df = conn.read(spreadsheet=SHEET_ID, worksheet="THO", ttl=0)
            
            if not isinstance(df, pd.DataFrame):
                conn.reset()
                df = conn.read(spreadsheet=SHEET_ID, worksheet="THO", ttl=0)

            # Recherche des notes pour le légume choisi
            existing_data = df[df['LEGUME'] == sel] if not df.empty else pd.DataFrame()
            notes = existing_data.iloc[0].to_dict() if not existing_data.empty else {}
            st.success("✅ Données chargées !")

        except Exception as e:
            st.error(f"Erreur de lecture : {e}")
            notes = {}
            df = pd.DataFrame(columns=["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"])

        # Formulaire avec ton style exact de blocs et colonnes
        with st.form(key=f"form_gsheet_{sel}"):
            c1, c2 = st.columns(2)
            with c1:
                v_plan = st.text_area("🌱 PLANTATION", value=notes.get("PLANTATION", ""), key=f"p_{sel}")
                v_entr = st.text_area("🛠️ ENTRETIEN", value=notes.get("ENTRETIEN", ""), key=f"e_{sel}")
                v_sant = st.text_area("🏥 SANTE", value=notes.get("SANTE", ""), key=f"s_{sel}")
            with c2:
                v_rend = st.text_area("📊 RENDEMENT", value=notes.get("RENDEMENT", ""), key=f"r_{sel}")
                v_vari = st.text_area("🧬 VARIETE", value=notes.get("VARIETE", ""), key=f"v_{sel}")
                v_info = st.text_area("➕ INFO SUPP", value=notes.get("INFO_SUPP", ""), key=f"i_{sel}")

            submit = st.form_submit_button("💾 ENREGISTRER DANS GOOGLE SHEETS")

            if submit:
                try:
                    # Préparation de la ligne
                    nouvelle_donnee = {
                        "LEGUME": sel,
                        "PLANTATION": v_plan,
                        "ENTRETIEN": v_entr,
                        "SANTE": v_sant,
                        "RENDEMENT": v_rend,
                        "VARIETE": v_vari,
                        "INFO_SUPP": v_info
                    }
                    
                    # Mise à jour du DataFrame local
                    if not df.empty and sel in df['LEGUME'].values:
                        for col, val in nouvelle_donnee.items():
                            df.loc[df['LEGUME'] == sel, col] = val
                        df_maj = df
                    else:
                        df_maj = pd.concat([df, pd.DataFrame([nouvelle_donnee])], ignore_index=True)
                    
                    # Envoi vers Google Sheets
                    conn.update(spreadsheet=SHEET_ID, worksheet="THO", data=df_maj)
                    st.cache_data.clear() 
                    
                    st.success("✨ Enregistré avec succès dans Google Sheets !")
                    st.balloons()
                    
                except Exception as e:
                    # Gestion du faux message d'erreur 200
                    if "200" in str(e):
                        st.success("✨ Enregistré avec succès !")
                        st.balloons()
                    else:
                        st.error(f"Erreur réelle : {e}")
else:
    st.info("Sélectionnez un légume pour afficher les données.")
