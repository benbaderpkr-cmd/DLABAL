import streamlit as st
import json
import os
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="DLABAL", layout="wide", page_icon="🌱")

# --- CONNEXION GSHEET ---
SHEET_ID = "1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. FONCTIONS JSON ---
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

# --- 2. CHARGEMENT ---
DATA = load_json("data.json")
tous_les_legumes = sorted(list(DATA.keys()))

# --- 3. SIDEBAR ---
st.sidebar.title("🌱 DLABAL")
sel = st.sidebar.selectbox("Choisir un légume :", ["---"] + tous_les_legumes)

# --- 4. CONTENU ---
if sel != "---":
    st.title(f"📊 {sel.upper()}")
    JDV_DATA = load_json("jdv.json")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 GAB", "🚜 JMF", "🌿 JDV", "📝 THO"])

    with tab1:
        g = DATA.get(sel, {}).get("GAB_FRAB", {})
        if g:
            for k, v in g.get("TECHNIQUE", {}).items():
                with st.expander(f"📌 {k}"): st.markdown(v)

    with tab2:
        f = DATA.get(sel, {}).get("JMF_FORTIER", {})
        if f:
            for t, c in f.items():
                with st.expander(f"📌 {t}"): st.markdown(c)

    with tab3:
        j = JDV_DATA.get(sel, {})
        if j:
            for t, c in j.items():
                with st.expander(f"🌿 {t}"): st.markdown(c)

    # --- ONGLET 4 : GOOGLE SHEETS ---
    with tab4:
        st.subheader(f"📝 Notes : {sel}")
        try:
            df = conn.read(spreadsheet=SHEET_ID, worksheet="THO", ttl=0)
            existing_data = df[df['LEGUME'] == sel] if not df.empty else pd.DataFrame()
            notes = existing_data.iloc[0].to_dict() if not existing_data.empty else {}
        except:
            notes = {}
            df = pd.DataFrame(columns=["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"])

        with st.form(key=f"f_{sel}"):
            c1, c2 = st.columns(2)
            v_plan = c1.text_area("🌱 PLANTATION", value=notes.get("PLANTATION", ""))
            v_entr = c1.text_area("🛠️ ENTRETIEN", value=notes.get("ENTRETIEN", ""))
            v_sant = c1.text_area("🏥 SANTE", value=notes.get("SANTE", ""))
            v_rend = c2.text_area("📊 RENDEMENT", value=notes.get("RENDEMENT", ""))
            v_vari = c2.text_area("🧬 VARIETE", value=notes.get("VARIETE", ""))
            v_info = c2.text_area("➕ INFO SUPP", value=notes.get("INFO_SUPP", ""))
            
            submit = st.form_submit_button("💾 ENREGISTRER")

            if submit:
                try:
                    nouvelle_donnee = {
                        "LEGUME": sel, "PLANTATION": v_plan, "ENTRETIEN": v_entr,
                        "SANTE": v_sant, "RENDEMENT": v_rend, "VARIETE": v_vari, "INFO_SUPP": v_info
                    }
                    
                    # Mise à jour du tableau
                    if not df.empty and "LEGUME" in df.columns:
                        df = df[df['LEGUME'] != sel]
                    df = pd.concat([df, pd.DataFrame([nouvelle_donnee])], ignore_index=True)
                    
                    # ENVOI (Sans l'argument index qui posait problème)
                    conn.update(spreadsheet=SHEET_ID, worksheet="THO", data=df)
                    
                    st.success("✨ Enregistré !")
                    st.balloons()
                except Exception as e:
                    if "200" in str(e): st.success("✨ Enregistré !")
                    else: st.error(f"Erreur : {e}")
else:
    st.info("Sélectionnez un légume.")
