import streamlit as st
import json
import os
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuration de la page (Ton style)
st.set_page_config(page_title="DLABAL", layout="wide", page_icon="🌱")

# Connexion gsheet - ON UTILISE L'URL COMPLETE ICI
URL_SHEET = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"
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

    # --- ONGLET 1 : GAB ---
    with tab1:
        c = DATA.get(sel, {})
        g = c.get("GAB_FRAB", {})
        if not g:
            st.warning("Aucune donnée GAB/FRAB.")
        else:
            if "BLOCS_IDENTITE" in g:
                blocs = g["BLOCS_IDENTITE"]
                cols = st.columns(len(blocs))
                for i, b in enumerate(blocs):
                    cols[i].success(f"**{b['titre']}**\n\n{b['contenu']}")
            
            for k, v in g.get("TECHNIQUE", {}).items():
                with st.expander(f"📌 {k}", expanded=True):
                    st.markdown(v)
    # --- SOURCE JMF ---
    with tab2:
        f = DATA.get(sel, {}).get("JMF_FORTIER", {})
        if f:
            for titre, contenu in f.items():
                with st.expander(f"📌 {titre}", expanded=True):
                    st.markdown(contenu)
        else: st.warning("Données JMF absentes.")

    # --- SOURCE JDV ---
    with tab3:
        j = JDV_DATA.get(sel, {})
        if j:
            for t, c in j.items():
                with st.expander(f"🌿 {t}", expanded=True):
                    st.markdown(c)
        else: st.warning("Données JDV absentes.")

    # --- SOURCE THO (GOOGLE SHEETS) ---
    with tab4:
        st.subheader(f"📝 Notes de culture : {sel}")
        
        # Structure de colonnes attendue
        cols = ["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"]
        df_actuel = pd.DataFrame(columns=cols)
        notes = {}

        try:
            # Lecture avec l'URL complète
            df_lu = conn.read(spreadsheet=URL_SHEET, worksheet="THO", ttl=0)
            if df_lu is not None and not df_lu.empty:
                df_actuel = df_lu
                # On s'assure que le légume existe dans le tableau
                if 'LEGUME' in df_actuel.columns:
                    existing = df_actuel[df_actuel['LEGUME'] == sel]
                    if not existing.empty:
                        notes = existing.iloc[-1].to_dict()
        except:
            st.info("Prêt pour la première note sur ce légume.")

        # FORMULAIRE (Ton style 2 colonnes / Blocs)
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

            submit = st.form_submit_button("💾 ENREGISTRER DANS GOOGLE SHEETS")

        if submit:
            try:
                # Création de la nouvelle donnée
                nouvelle_ligne = {
                    "LEGUME": sel, "PLANTATION": v_plan, "ENTRETIEN": v_entr,
                    "SANTE": v_sant, "RENDEMENT": v_rend, "VARIETE": v_vari, "INFO_SUPP": v_info
                }
                
                # Mise à jour du tableau local
                if not df_actuel.empty and 'LEGUME' in df_actuel.columns:
                    df_actuel = df_actuel[df_actuel['LEGUME'] != sel]
                
                df_final = pd.concat([df_actuel, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
                df_final = df_final.reindex(columns=cols)
                
                # ENVOI SUR L'URL
                conn.update(spreadsheet=URL_SHEET, worksheet="THO", data=df_final)
                st.cache_data.clear() 
                st.success("✨ Données enregistrées avec succès !")
                st.balloons()
            except Exception as e:
                # Gestion du bug code 200
                if "200" in str(e):
                    st.success("✨ Données transmises !")
                    st.balloons()
                else:
                    st.error(f"Erreur d'enregistrement : {e}")
else:
    st.info("Sélectionnez un légume pour afficher les données.")

