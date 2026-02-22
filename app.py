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

# ... (Sections 1, 2 et 3 : Sécurité, Fonctions et Chargement restent identiques) ...

# ==========================================
# 4. SIDEBAR ET NAVIGATION
# ==========================================
with st.sidebar:
    if st.button("**DLABAL**", use_container_width=True):
        st.session_state["view_mode"] = "ACCUEIL"
        st.session_state["nav_sidebar"] = "---" # Reset le légume
        st.rerun()
    
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.9em; margin-top: -15px;'>BDD ITK Maraîchage</p>", unsafe_allow_html=True)
    
    # Correction ICI : On s'assure que le changement de légume force le mode "LEGUME"
    def on_change_sidebar():
        if st.session_state["nav_sidebar"] != "---":
            st.session_state["view_mode"] = "LEGUME"

    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes, key="nav_sidebar", on_change=on_change_sidebar)
    
    st.divider()

    if st.button("⚙️ RÉGLAGES JP1", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_JP1"
        st.rerun()
        
    if st.button("🧪 CALCUL FERTI", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_FERTI"
        st.rerun()

    st.link_button("📂 Fiches légumes JA", "https://drive.google.com/drive/u/0/folders/1nj4ZGdFExm-_xs8xRYBBxmSkqmVEvdmM", use_container_width=True)
        
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""; cookies.save(); st.session_state["password_correct"] = False; st.rerun()

# ==========================================
# 5. AFFICHAGE CENTRAL
# ==========================================

# --- PAGE FERTILISATION (Identique au correctif précédent) ---
if st.session_state["view_mode"] == "PAGE_FERTI":
    st.title("🧪 CALCULATEUR DE FERTILISATION")
    leg_f = st.selectbox("Légume pour base :", ["---"] + sorted(FERTI_DATA.keys(), key=sans_accent), key="sel_ferti")
    # ... (code ferti) ...

# --- PAGE REGLAGES JP1 (Identique au correctif précédent) ---
elif st.session_state["view_mode"] == "PAGE_JP1":
    st.title("⚙️ RÉGLAGES JP1")
    l_jp1 = st.selectbox("Choisir un légume :", ["---"] + full_list, key="sel_jp1")
    # ... (code tableau JP1) ...

# --- PAGE LEGUME (RÉTABLISSEMENT DES DONNÉES) ---
elif st.session_state["view_mode"] == "LEGUME":
    # CRUCIAL : On utilise la valeur de 'nav_sidebar' pour extraire les données
    sel_legume = st.session_state.get("nav_sidebar", "---")
    
    if sel_legume != "---":
        st.title(f"📊 {sel_legume.upper()}")
        tabs = st.tabs(["📘 ARG", "📋 GAB", "🚜 JMF", "🌿 JDV", "📗 ITAB", "📝 THO"])

        with tabs[0]: # ARG
            # On cherche bien avec sel_legume
            arg_l = ARG_DATA.get(sel_legume, {})
            if arg_l:
                for titre, contenu in arg_l.items():
                    with st.expander(f"📘 {titre}", expanded=True):
                        if isinstance(contenu, dict) and "lignes" in contenu:
                            df_temp = pd.DataFrame(contenu["lignes"])
                            # ... (code mapping colonnes) ...
                            st.dataframe(df_temp, use_container_width=True)
                        else:
                            st.markdown(str(contenu).replace('\\\\n', '  \n').replace('\\n', '  \n'))
                        popover_feedback("ARG", titre, sel_legume)
            else: st.info(f"Aucune donnée ARG disponible pour {sel_legume}.")

        with tabs[1]: # GAB
            g = GAB_DATA.get(sel_legume, {})
            if g:
                if "BLOCS_IDENTITE" in g:
                    cols = st.columns(len(g["BLOCS_IDENTITE"]))
                    for i, b in enumerate(g["BLOCS_IDENTITE"]):
                        with cols[i]: st.success(f"**{b['titre']}**\n\n{str(b['contenu']).replace('\\\\n', '\\n')}")
                if "TECHNIQUE" in g:
                    for k, v in g.get("TECHNIQUE", {}).items():
                        with st.expander(f"📌 {k}", expanded=True):
                            st.markdown(str(v).replace('\\\\n', '\\n'))
                            popover_feedback("GAB", k, sel_legume)
            else: st.info(f"Données GAB absentes.")

        with tabs[2]: # JMF
            j = JMF_DATA.get(sel_legume, {})
            if j:
                for t, c in j.items():
                    with st.expander(f"🚜 {t}", expanded=True):
                        st.markdown(str(c).replace('\\\\n', '\\n'))
                        popover_feedback("JMF", t, sel_legume)

        with tabs[3]: # JDV
            v = JDV_DATA.get(sel_legume, {})
            if v:
                for t, c in v.items():
                    with st.expander(f"🌿 {t}", expanded=True):
                        st.markdown(str(c).replace('\\\\n', '\\n'))
                        popover_feedback("JDV", t, sel_legume)

        with tabs[4]: # ITAB
            itab = ITAB_DATA.get(sel_legume, {})
            if itab:
                for t, c in itab.items():
                    with st.expander(f"📗 {t}", expanded=True):
                        st.markdown(str(c).replace('\\\\n', '\\n'))
                        popover_feedback("ITAB", t, sel_legume)

        with tabs[5]: # THO (Saisie Terrain)
            st.subheader("📝 Saisie Terrain (THO)")
            df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO", ttl=0)
            exist = df_gs[df_gs['LEGUME'] == sel_legume]
            # ... (Formulaire THO identique, utilisant sel_legume) ...

else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.markdown("---")
    st.info("Utilisez la barre latérale pour commencer.")

