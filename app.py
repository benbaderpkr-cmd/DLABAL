import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_cookies_manager import EncryptedCookieManager

# 1. CONFIGURATION ET COOKIES
st.set_page_config(page_title="DLABAL - SYSTÈME EXPERT", layout="wide", page_icon="🌱")

cookies = EncryptedCookieManager(password="cle_secrete_dlabal_2026")
if not cookies.ready():
    st.stop()

# 2. SYSTÈME DE MOT DE PASSE
def check_password():
    if st.session_state.get("password_correct") or cookies.get("auth_token") == "valide":
        st.session_state["password_correct"] = True
        return True
    
    st.title("🔐 Accès Restreint")
    pwd = st.text_input("Entrez le mot de passe DLABAL :", type="password")
    if st.button("Valider"):
        if pwd == st.secrets["password"]:
            st.session_state["password_correct"] = True
            cookies["auth_token"] = "valide"
            cookies.save()
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
    return False

if not check_password():
    st.stop()

# 3. CONNEXION GSHEETS
URL_SHEET = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. CHARGEMENT DES DONNÉES
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

DATA = load_json("data.json")
JDV_DATA = load_json("jdv.json")
SOURCES_JMF = load_json("sources_jmf.json")
REGLAGES_JP1_OFFICIEL = load_json("reglages_jp1.json")

cles_itk = list(SOURCES_JMF.get("reglages_itk", {}).keys())
tous_les_legumes = sorted(list(set(list(DATA.keys()) + list(JDV_DATA.keys()) + cles_itk)))

# --- SIDEBAR ---
with st.sidebar:
    # TITRE CLIQUABLE POUR RETOUR ACCUEIL
    if st.button("🌱 DLABAL", use_container_width=True):
        st.session_state["view_mode"] = "DOSSIER"
        st.session_state["last_sel"] = "---"
        st.session_state["reset_key"] = st.session_state.get("reset_key", 0) + 1
        st.rerun()
    
    st.markdown("<p style='margin-top: -15px; font-weight: bold;'>Base de données des ITKs</p>", unsafe_allow_html=True)
    
    res_key = st.session_state.get("reset_key", 0)
    sel = st.selectbox(
        "Choisir ou taper le nom d'un légume :", 
        ["---"] + tous_les_legumes,
        key=f"selection_legume_{res_key}"
    )
    
    if sel != "---":
        if "last_sel" not in st.session_state or st.session_state["last_sel"] != sel:
            st.session_state["view_mode"] = "DOSSIER"
            st.session_state["last_sel"] = sel

    st.divider()
    if st.button("📊 RÉGLAGES JP1 GLOBAUX", use_container_width=True):
        st.session_state["view_mode"] = "JP1_GLOBAL"
        st.rerun()
    
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""
        cookies.save()
        st.session_state["password_correct"] = False
        st.rerun()

# --- LOGIQUE D'AFFICHAGE ---

if st.session_state.get("view_mode") == "JP1_GLOBAL":
    st.title("🚜 RÉGLAGES OFFICIELS JP1 (CONSTRUCTEUR)")
    if st.button("⬅️ Retour"):
        st.session_state["view_mode"] = "DOSSIER"
        st.rerun()
    # (Ici les tableaux JP1 que tu avais déjà)
    st.info("Consultez ici les abaques techniques du semoir.")
    # ... code des tableaux ...

else:
    if sel == "---":
        st.title("🌱 Bienvenue sur DLABAL")
        st.info("Sélectionnez un légume ci-contre ou consultez les réglages JP1 globaux.")
        
        st.markdown("### Une base de notes partagée, sans chichis.")
        st.markdown("""
        J’ai regroupé ici ce que j’ai pu glaner en formation ou sur le terrain. C’est sans prétention : 
        je ne cherche pas à donner de leçon, juste à mettre mes notes au propre pour qu'elles servent à d'autres. 
        L’outil est gratuit et je le bricole sur mon temps libre, donc c’est encore un peu rustique.

        **Si tu as de l'expérience à partager, n'hésite pas à mettre la main à la pâte :**

        * **Expériences de terrain :** Ça se passe dans l'onglet **THO**. Tes retours alimentent la base commune visible dans THO_RESULT.
        * **Réglages du semoir JP1 :** À gauche dans la page **Réglage JP1**, tu peux laisser tes propres réglages par légume. Ils sont compilés plus bas dans la section "Conseils persos JP1".

        L'idée, c'est que ça profite à tout le monde. Sers-toi, et complète si le cœur t'en dit.
        """)

    else:
        st.title(f"📊 {sel.upper()}")
        tab1, tab2, tab3, tab4 = st.tabs(["📋 GAB / FRAB", "🚜 JMF", "🌿 JDV", "📝 THO"])

        with tab1:
            g = DATA.get(sel, {}).get("GAB_FRAB", {})
            if g:
                if "BLOCS_IDENTITE" in g:
                    cols = st.columns(len(g["BLOCS_IDENTITE"]))
                    for i, b in enumerate(g["BLOCS_IDENTITE"]):
                        cols[i].success(f"**{b['titre']}**\n\n{b['contenu']}")
                for k, v in g.get("TECHNIQUE", {}).items():
                    # AJOUT DE expanded=True ici
                    with st.expander(f"📌 {k}", expanded=True):
                        st.markdown(v)

        with tab2:
            base = SOURCES_JMF.get("reglages_itk", {})
            reg = base.get(sel.strip())
            if reg:
                c1, c2 = st.columns(2)
                c1.info(f"**📍 JMF**\n- Rouleau : `{reg.get('jmf', {}).get('rouleau', '?')}`")
                c2.warning(f"**🚜 Terrateck**\n- Rouleau : `{reg.get('terrateck', {}).get('rouleau', '?')}`")
            f = DATA.get(sel, {}).get("JMF_FORTIER", {})
            for t, c in f.items():
                # AJOUT DE expanded=True ici
                with st.expander(f"📌 {t}", expanded=True):
                    st.markdown(c)
                        
        with tab3:
            j = JDV_DATA.get(sel, {})
            if "RENDEMENT JDV" in j: st.success(f"**🚜 RENDEMENT JDV :** {j['RENDEMENT JDV']}")
            for t, c in j.items():
                if t != "RENDEMENT JDV":
                    # AJOUT DE expanded=True ici
                    with st.expander(f"🌿 {t}", expanded=True):
                        st.markdown(str(c))

        with tab4:
            # (Ton formulaire THO reste tel quel)
            st.subheader(f"📝 Saisie Terrain - {sel}")
            # ...
