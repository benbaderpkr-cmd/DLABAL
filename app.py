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
# 2. CONNEXION GSHEETS (Pilier 1)
# ==========================================
conn = GSheetsConnection("gsheets")
URL_SHEET = st.secrets["gsheets"]["spreadsheet"]

# ==========================================
# 3. BARRE LATERALE ET SELECTION
# ==========================================
with st.sidebar:
    st.image("https://www.itab.asso.fr/images/logo-itab.png", width=100) # Logo ITAB par défaut
    st.title("Menu DLABAL")
    
    # Chargement liste légumes depuis GSheets
    df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO")
    liste_legumes = sorted(df_gs['LEGUME'].dropna().unique().tolist())
    
    sel = st.selectbox("Choisir un légume :", [""] + liste_legumes)

# ==========================================
# 4. AFFICHAGE DES ONGLETS
# ==========================================
if sel:
    st.title(f"🥕 Fiche Technique : {sel}")
    
    # Définition des 5 onglets (ITAB inséré entre JDV et THO)
    tabs = st.tabs(["GAB", "JMF", "JDV", "ITAB", "THO"])

    # --- ONGLET 0 : GAB ---
    with tabs[0]:
        st.info("Données en cours de synchronisation avec le GAB...")

    # --- ONGLET 1 : JMF ---
    with tabs[1]:
        st.info("Référentiel Jean-Martin Fortier...")

    # --- ONGLET 2 : JDV ---
    with tabs[2]:
        st.info("Données Jardin du Vernois...")

    # --- ONGLET 3 : ITAB (NOUVEAU) ---
    with tabs[3]:
        st.header(f"📚 Expertise ITAB : {sel}")
        itab_data = load_itab_data()
        
        # On cherche la clé en majuscule dans le JSON (ex: "EPINARD")
        cle_legume = sel.upper()
        
        if itab_data and cle_legume in itab_data:
            data = itab_data[cle_legume]
            
            # Affichage en colonnes pour une meilleure lisibilité
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🔬 Botanique & Physiologie")
                st.json(data.get("BOTANIQUE", data.get("BOTANIQUE_ET_GENETIQUE", {})))
                
                st.markdown("### 🌡️ Exigences Thermiques")
                st.json(data.get("PHYSIOLOGIE", data.get("EXIGENCES_THERMIQUES_C", {})))
                
            with c2:
                st.markdown("### 🚜 Itinéraire Technique")
                st.json(data.get("TECHNIQUE_CULTURALE", data.get("ITINERAIRE_TECHNIQUE", {})))
                
                st.markdown("### 🧺 Logistique & Qualité")
                st.json(data.get("LOGISTIQUE", {}))
                
            st.markdown("---")
            st.markdown("### 🦟 Protection des Plantes (Santé)")
            st.json(data.get("PATHOLOGIE", data.get("PHYTOSANITAIRE", {})))
        else:
            st.warning(f"Aucune fiche ITAB détaillée n'est encore disponible pour '{sel}'.")
            st.write("Veuillez charger le PDF correspondant pour l'extraire.")

    # --- ONGLET 4 : THO (FORMULAIRE 6 CHAMPS) ---
    with tabs[4]:
        st.header("📝 Saisie Terrain (THO)")
        row = df_gs[df_gs['LEGUME'] == sel].iloc[0]
        
        with st.form("tho_form"):
            v_p = st.text_area("Plantation :", value=row.get('PLANTATION', ""))
            v_e = st.text_area("Entretien :", value=row.get('ENTRETIEN', ""))
            v_s = st.text_area("Santé :", value=row.get('SANTE', ""))
            v_r = st.text_area("Rendement :", value=row.get('RENDEMENT', ""))
            v_v = st.text_area("Variétés :", value=row.get('VARIETE', ""))
            v_i = st.text_area("Infos Supp :", value=row.get('INFO_SUPP', ""))
            
            if st.form_submit_button("💾 Enregistrer les modifications"):
                # Mise à jour GSheets (Pilier 1)
                new_row = {"LEGUME": sel, "PLANTATION": v_p, "ENTRETIEN": v_e, "SANTE": v_s, "RENDEMENT": v_r, "VARIETE": v_v, "INFO_SUPP": v_i}
                df_final = pd.concat([df_gs[df_gs['LEGUME'] != sel], pd.DataFrame([new_row])], ignore_index=True)
                conn.update(spreadsheet=URL_SHEET, worksheet="THO", data=df_final)
                st.success("Données THO enregistrées avec succès !")

# --- PAGE D'ACCUEIL ---
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.markdown("---")
    st.markdown("""
    ### DLABAL - BDD ITK Maraîchage
    
    Cet outil centralise les connaissances techniques : **GAB**, **JMF**, **JDV** et désormais l'expertise **ITAB**.
    
    **Instructions :**
    1. **Sélectionnez un légume** dans le menu à gauche.
    2. **Consultez l'onglet ITAB** pour les extractions ultra-détaillées des PDF.
    3. **Utilisez l'onglet THO** pour vos notes de terrain.
    """)
    st.info("👈 Choisissez un légume pour commencer.")
