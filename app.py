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

    # --- SOURCE GAB ---
    with tab1:
        g = DATA.get(sel, {}).get("GAB_FRAB", {})
        if g:
            for k, v in g.get("TECHNIQUE", {}).items():
                with st.expander(f"📌 {k}", expanded=True):
                    st.markdown(v)
        else: st.warning("Données GAB absentes.")

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
        
        try:
            df = conn.read(spreadsheet=SHEET_ID, worksheet="THO", ttl=0)
            if not df.empty and 'LEGUME' in df.columns:
                existing_data = df[df['LEGUME'] == sel]
                notes = existing_data.iloc[0].to_dict() if not existing_data.empty else {}
            else:
                notes = {}
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")
            notes = {}
            df = pd.DataFrame(columns=["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"])

        # ON GARDE TON FORMULAIRE EN 2 COLONNES
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
                    nouvelle_donnee = {
                        "LEGUME": sel,
                        "PLANTATION": v_plan,
                        "ENTRETIEN": v_entr,
                        "SANTE": v_sant,
                        "RENDEMENT": v_rend,
                        "VARIETE": v_vari,
                        "INFO_SUPP": v_info
                    }
                    
                    # Mise à jour intelligente
                    if not df.empty and 'LEGUME' in df.columns:
                        df = df[df['LEGUME'] != sel]
                    
                    df_final = pd.concat([df, pd.DataFrame([nouvelle_donnee])], ignore_index=True)
                    
                    # On force l'ordre pour éviter le refus de Google
                    cols = ["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"]
                    df_final = df_final[cols]
                    
                    conn.update(spreadsheet=SHEET_ID, worksheet="THO", data=df_final)
                    st.cache_data.clear() 
                    
                    st.success("✨ Enregistré ! Allez voir le fichier DLABAL_DATA.")
                    st.balloons()
                    
                except Exception as e:
                    if "200" in str(e):
                        st.success("✨ Enregistré avec succès !")
                        st.balloons()
                    else:
                        st.error(f"Erreur réelle : {e}")
else:
    st.info("Sélectionnez un légume pour afficher les données.")
