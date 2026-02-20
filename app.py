import streamlit as st
import json
import os
import pandas as pd
import requests
import unicodedata
import streamlit.components.v1 as components
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_cookies_manager import EncryptedCookieManager

# ==========================================
# 1. CONFIGURATION ET SECURITE
# ==========================================
st.set_page_config(page_title="DLABAL - BDD ITK Maraîchage", layout="wide", page_icon="🌱")

cookies = EncryptedCookieManager(password="cle_secrete_dlabal_2026")
if not cookies.ready():
    st.stop()

def check_password():
    if st.session_state.get("password_correct") or cookies.get("auth_token") == "valide":
        st.session_state["password_correct"] = True
        return True
    st.title("🔐 Accès Restreint")
    with st.form("auth_form", clear_on_submit=False):
        pwd = st.text_input("Mot de passe DLABAL :", type="password")
        if st.form_submit_button("Valider"):
            if pwd == st.secrets["password"]:
                st.session_state["password_correct"] = True
                cookies["auth_token"] = "valide"
                cookies.save()
                st.rerun()
            else:
                st.error("Incorrect")
    return False

# Fonction pour charger les données ITAB (Extraites des PDF)
def load_itab_data():
    if os.path.exists("itab.json"):
        try:
            with open("itab.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erreur de lecture du fichier itab.json : {e}")
    return None

if not check_password():
    st.stop()

# ==========================================
# 2. CONNEXION GSHEETS (Correction)
# ==========================================
# On rétablit la connexion telle qu'elle était dans ton app (14).py
conn = st.connection("gsheets", type=GSheetsConnection)

# Si tu as besoin de l'URL pour une lecture spécifique, on l'appelle via la clé "spreadsheet" 
# mais avec une sécurité (get) pour ne pas faire planter l'app si elle manque
URL_SHEET = st.secrets.get("gsheets", {}).get("spreadsheet", "")

# ==========================================
# 3. BARRE LATERALE ET SELECTION
# ==========================================
with st.sidebar:
    st.image("https://www.itab.asso.fr/images/logo-itab.png", width=100)
    st.title("Menu DLABAL")
    
    # Lecture GSheets pour la liste des légumes
    try:
        # On utilise la configuration par défaut de st.connection
        df_gs = conn.read(worksheet="THO")
        liste_legumes = sorted(df_gs['LEGUME'].dropna().unique().tolist())
    except Exception as e:
        st.error(f"Erreur de lecture GSheets : {e}")
        liste_legumes = []
    
    sel = st.selectbox("Choisir un légume :", [""] + liste_legumes)

# ==========================================
# 4. AFFICHAGE DES ONGLETS
# ==========================================
if sel:
    st.title(f"🥕 Fiche Technique : {sel}")
    
    # ITAB est inséré ici en 4ème position (index 3)
    tabs = st.tabs(["GAB", "JMF", "JDV", "ITAB", "THO"])

    with tabs[0]: st.info("Données GAB...")
    with tabs[1]: st.info("Référentiel JMF...")
    with tabs[2]: st.info("Données JDV...")

    # --- NOUVEL ONGLET ITAB ---
    with tabs[3]:
        st.header(f"📚 Expertise ITAB : {sel}")
        itab_data = load_itab_data()
        cle_legume = sel.upper()
        
        if itab_data and cle_legume in itab_data:
            data = itab_data[cle_legume]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🔬 Botanique & Physiologie")
                st.json(data.get("BOTANIQUE", {}))
                st.markdown("### 🌡️ Exigences Thermiques")
                st.json(data.get("PHYSIOLOGIE", {}))
            with c2:
                st.markdown("### 🚜 Itinéraire Technique")
                st.json(data.get("TECHNIQUE_CULTURALE", {}))
                st.markdown("### 🧺 Logistique & Qualité")
                st.json(data.get("LOGISTIQUE", {}))
            st.markdown("---")
            st.markdown("### 🦟 Protection des Plantes")
            st.json(data.get("PATHOLOGIE", {}))
        else:
            st.warning(f"Aucune donnée ITAB disponible dans 'itab.json' pour '{sel}'.")

    # --- ONGLET THO ---
    with tabs[4]:
        st.header("📝 Saisie Terrain (THO)")
        row_data = df_gs[df_gs['LEGUME'] == sel]
        if not row_data.empty:
            row = row_data.iloc[0]
            with st.form("tho_form"):
                v_p = st.text_area("Plantation :", value=str(row.get('PLANTATION', "")))
                v_e = st.text_area("Entretien :", value=str(row.get('ENTRETIEN', "")))
                v_s = st.text_area("Santé :", value=str(row.get('SANTE', "")))
                v_r = st.text_area("Rendement :", value=str(row.get('RENDEMENT', "")))
                v_v = st.text_area("Variétés :", value=str(row.get('VARIETE', "")))
                v_i = st.text_area("Infos Supp :", value=str(row.get('INFO_SUPP', "")))
                
                if st.form_submit_button("💾 Enregistrer"):
                    new_row = {"LEGUME": sel, "PLANTATION": v_p, "ENTRETIEN": v_e, "SANTE": v_s, "RENDEMENT": v_r, "VARIETE": v_v, "INFO_SUPP": v_i}
                    df_updated = pd.concat([df_gs[df_gs['LEGUME'] != sel], pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(worksheet="THO", data=df_updated)
                    st.success("Modifications enregistrées dans GSheets !")
        else:
            st.error("Légume non trouvé dans la feuille THO.")

else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.info("👈 Choisissez un légume dans la barre latérale.")
