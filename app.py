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

    # --- SOURCE THO (C'est ici que l'erreur 'df' est corrigée) ---
    with tab4:
        st.subheader(f"📝 Notes de culture : {sel}")
        
        # FIX : On définit df AVANT tout essai de lecture pour être sûr qu'il existe
        df = pd.DataFrame(columns=["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"])
        notes = {}

        try:
            # On tente de lire le Google Sheet
            fetched_df = conn.read(spreadsheet=SHEET_ID, worksheet="THO", ttl=0)
            if isinstance(fetched_df, pd.DataFrame) and not fetched_df.empty:
                df = fetched_df
                # On cherche les notes du légume
                if 'LEGUME' in df.columns:
                    existing_data = df[df['LEGUME'] == sel]
                    if not existing_data.empty:
                        notes = existing_data.iloc[-1].to_dict()
            st.success("✅ Connexion Google Sheets établie")
        except Exception as e:
            st.info("Initialisation d'un nouveau tableau (lecture impossible ou vide).")

        # Ton formulaire en 2 colonnes
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
                    # Préparation de la donnée
                    nouvelle_donnee = {
                        "LEGUME": sel, "PLANTATION": v_plan, "ENTRETIEN": v_entr,
                        "SANTE": v_sant, "RENDEMENT": v_rend, "VARIETE": v_vari, "INFO_SUPP": v_info
                    }
                    
                    # Mise à jour de 'df' (qui est maintenant forcément défini)
                    if 'LEGUME' in df.columns and sel in df['LEGUME'].values:
                        df = df[df['LEGUME'] != sel]
                    
                    df_final = pd.concat([df, pd.DataFrame([nouvelle_donnee])], ignore_index=True)
                    
                    # Envoi
                    conn.update(spreadsheet=SHEET_ID, worksheet="THO", data=df_final)
                    st.cache_data.clear() 
                    st.success("✨ Enregistré !")
                    st.balloons()
                    
                except Exception as e:
                    if "200" in str(e):
                        st.success("✨ Enregistré !")
                        st.balloons()
                    else:
                        st.error(f"Erreur : {e}")
else:
    st.info("Sélectionnez un légume.")
