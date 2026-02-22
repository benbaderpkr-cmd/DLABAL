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

if not check_password():
    st.stop()

if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "ACCUEIL"

# ==========================================
# 2. FONCTIONS UTILES
# ==========================================
def load_json(f):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as file: return json.load(file)
        except: return {}
    return {}

def sans_accent(texte):
    return ''.join(c for c in unicodedata.normalize('NFD', texte)
                   if unicodedata.category(c) != 'Mn').lower()

# ==========================================
# 3. CONNEXIONS ET CHARGEMENT DONNÉES
# ==========================================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"
URL_SHEET2 = "https://docs.google.com/spreadsheets/d/1wUngO5HjSCRYbWzd0hMxKBj4aUD4ThW1ishVvaOwOcc/edit#gid=0"
URL_SCRIPT_MAIL = "https://script.google.com/macros/s/AKfycbwMW0m4CJPvv5rJ0tFjmoU58F6LTnpNmB1BYsp3bKiKy9vBi3PFUQqmWP9n-axt-iqXZA/exec" 

conn = st.connection("gsheets", type=GSheetsConnection)

GAB_DATA = load_json("gab.json")
JMF_DATA = load_json("jmf.json")
JDV_DATA = load_json("jdv.json")
ITAB_DATA = load_json("itab.json")
RAW_JP1 = load_json("reglages_jp1.json")
REGLAGES_LISTE = RAW_JP1.get("reglages", [])

legumes_uniques = [l for l in set(list(GAB_DATA.keys()) + list(JMF_DATA.keys()) + list(JDV_DATA.keys())) 
                   if GAB_DATA.get(l) or JMF_DATA.get(l) or JDV_DATA.get(l)]
tous_les_legumes = sorted(legumes_uniques, key=sans_accent)

def envoyer_feedback(legume, nom_onglet_app, message, nom_bloc, nom_utilisateur):
    try:
        nom_sheet = legume.upper()
        new_row = pd.DataFrame([{
            "DATE": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "NOM": nom_utilisateur, "LEGUME": nom_sheet, "ONGLET": nom_onglet_app,
            "BLOC": nom_bloc, "FEEDBACK": message
        }])
        df_updated = pd.concat([conn.read(spreadsheet=URL_SHEET2, worksheet=nom_sheet, ttl=0), new_row], ignore_index=True)
        conn.update(spreadsheet=URL_SHEET2, worksheet=nom_sheet, data=df_updated)
        if "https" in URL_SCRIPT_MAIL:
            requests.get(f"{URL_SCRIPT_MAIL}?legume={nom_sheet}&nom={nom_utilisateur}", timeout=5)
        st.toast(f"🚀 Merci {nom_utilisateur} ! Enregistré.", icon="✅")
    except: st.error("Erreur d'enregistrement.")

def popover_feedback(onglet, bloc, legume_sel):
    pop = st.popover("📝")
    with pop.form(key=f"form_{onglet}_{bloc}_{legume_sel}"):
        nom_in = st.text_input("Nom :", value=st.session_state["user_name"])
        msg_in = st.text_area("Suggestion :")
        if st.form_submit_button("Envoyer"):
            st.session_state["user_name"] = nom_in 
            envoyer_feedback(legume_sel, onglet, msg_in, bloc, nom_in)
            st.rerun()

# ==========================================
# 4. SIDEBAR ET NAVIGATION
# ==========================================
with st.sidebar:
    if st.button("**DLABAL**", use_container_width=True):
        st.session_state["view_mode"] = "ACCUEIL"
        st.rerun()
    
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.9em; margin-top: -15px;'>BDD ITK Maraîchage</p>", unsafe_allow_html=True)
    st.write("") 
    
    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes)
    # FIX : on ne change la vue vers LEGUME que si le légume vient de changer.
    # Sans ce garde-fou, chaque re-run (ex: clic sur JP1/FERTI) forçait view_mode="LEGUME"
    # tant qu'un légume était sélectionné dans le widget.
    if sel != "---" and sel != st.session_state.get("_dernier_legume"):
        st.session_state["_dernier_legume"] = sel
        st.session_state["view_mode"] = "LEGUME"
        st.rerun()
    # Lire sel depuis la session pour qu'il reste stable même après navigation JP1/FERTI
    sel = st.session_state.get("_dernier_legume", "---")
    
    st.divider()

    if st.button("⚙️ RÉGLAGES JP1 TERRADONIS", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_JP1"
        st.rerun()

    if st.button("🌿 CALCUL FERTI", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_FERTI"
        st.rerun()

    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""; cookies.save(); st.session_state["password_correct"] = False; st.rerun()

# ==========================================
# 5. AFFICHAGE CENTRAL
# ==========================================

# --- CAS A : PAGE DÉDIÉE RÉGLAGES JP1 (TABLEAUX) ---
if st.session_state["view_mode"] == "PAGE_JP1":
    st.title("⚙️ RÉGLAGES JP1 TERRADONIS")
    st.caption(f"Source : {RAW_JP1.get('source', '')}")
    st.markdown("---")
    
    st.subheader("📋 Réglages Techniques (Source : JMF)")
    DATA_JMF = load_json("reglages_jmf.json")
    if DATA_JMF:
        df_jmf = pd.DataFrame(DATA_JMF["reglages"])
        st.dataframe(
            df_jmf.rename(columns={
                "AV": "Pignon AV", 
                "AR": "Pignon AR", 
                "OBS": "Observations"
            }), 
            use_container_width=True, 
            hide_index=True
        )
    st.caption("Source : Jean-Martin Fortier (JMF) - Guide technique")

    st.write("")
    st.divider()

    st.subheader("🌱 Guide de semis (Source : Terradonis / Terrain)")
    DATA_TERRA = load_json("reglages_jp1.json") 
    if DATA_TERRA and "reglages" in DATA_TERRA:
        df_terra = pd.DataFrame(DATA_TERRA["reglages"])[["CULTURE", "ROULEAUX"]]
        st.dataframe(
            df_terra.sort_values("CULTURE"), 
            use_container_width=True, 
            hide_index=True
        )
    st.caption("Source : Catalogue Terradonis & Observations Terrain")
    
# --- CAS B : PAGE CALCUL FERTI ---
elif st.session_state["view_mode"] == "PAGE_FERTI":
    FERTI_DATA = load_json("calcul_ferti.json")
    st.title("🌿 CALCUL FERTI")
    st.markdown("---")

    legume_ferti = st.selectbox("Choisir un légume :", ["---"] + sorted(FERTI_DATA.keys(), key=sans_accent))

    # Ajout du champ pour saisie directe
    with st.expander("Ou inscrire directement ses besoins de fertilisation (unités/ha)"):
        c_n, c_p, c_k = st.columns(3)
        manuel_n = c_n.number_input("N (u/ha) :", min_value=0, value=0)
        manuel_p = c_p.number_input("P (u/ha) :", min_value=0, value=0)
        manuel_k = c_k.number_input("K (u/ha) :", min_value=0, value=0)

    c1, c2 = st.columns(2)
    longueur = c1.number_input("Longueur (m) :", min_value=1, value=10, step=1)
    largeur = c2.number_input("Largeur (m) :", min_value=1, value=10, step=1)
    surface = longueur * largeur

    st.markdown("#### Teneur en azote de votre amendement")
    teneur_N = st.number_input("% N (Azote) :", min_value=0.0, value=0.0, step=0.1, format="%.2f")

    # Logique de calcul
    rows = []
    facteur = surface / 10000

    # Priorité 1 : Saisie manuelle (si au moins N est renseigné)
    if manuel_n > 0 or manuel_p > 0 or manuel_k > 0:
        besoin_N = round(manuel_n * facteur, 2)
        besoin_P = round(manuel_p * facteur, 2)
        besoin_K = round(manuel_k * facteur, 2)
        dose = round(besoin_N / (teneur_N / 100), 1) if teneur_N > 0 else "—"
        
        st.markdown(f"### Résultats personnalisés — {longueur} m × {largeur} m = **{surface} m²**")
        rows.append({
            "Source": "Saisie Manuelle",
            "Besoin N (kg)": besoin_N,
            "Besoin P (kg)": besoin_P,
            "Besoin K (kg)": besoin_K,
            "⚖️ Dose à épandre (kg)": dose,
        })

    # Priorité 2 : Sélection par légume
    elif legume_ferti != "---":
        donnees = FERTI_DATA[legume_ferti]
        st.markdown(f"### Résultats pour **{legume_ferti}** — {longueur} m × {largeur} m = **{surface} m²**")
        for source, vals in donnees.items():
            if vals:
                besoin_N = round(vals["N"] * facteur, 2)
                besoin_P = round(vals["P"] * facteur, 2)
                besoin_K = round(vals["K"] * facteur, 2)
                dose = round(besoin_N / (teneur_N / 100), 1) if teneur_N > 0 else "—"
                rows.append({
                    "Source": source,
                    "Besoin N (kg)": besoin_N,
                    "Besoin P (kg)": besoin_P,
                    "Besoin K (kg)": besoin_K,
                    "⚖️ Dose à épandre (kg)": dose,
                })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("La dose à épandre est calculée sur la base de l'azote (N) : besoin N de la culture ÷ teneur N de l'amendement.")

# --- CAS 2 : AFFICHAGE LÉGUME ---
elif st.session_state["view_mode"] == "LEGUME" and sel != "---":
    st.title(f"📊 {sel.upper()}")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 GAB", "🚜 JMF", "🌿 JDV", "📗 ITAB", "📝 THO"])

    with tab1:
        g = GAB_DATA.get(sel, {})
        if "BLOCS_IDENTITE" in g:
            cols = st.columns(len(g["BLOCS_IDENTITE"]))
            for i, b in enumerate(g["BLOCS_IDENTITE"]):
                with cols[i]:
                    st.success(f"**{b['titre']}**\n\n{b['contenu']}")
                    popover_feedback("GAB", b['titre'], sel)
        for k, v in g.get("TECHNIQUE", {}).items():
            with st.expander(f"📌 {k}", expanded=True):
                st.markdown(v); c1, c2 = st.columns([0.96, 0.04])
                with c2: popover_feedback("GAB", k, sel)

    with tab2:
        for t, c in JMF_DATA.get(sel, {}).items():
            with st.expander(f"📌 {t}", expanded=True):
                st.markdown(c); c1, c2 = st.columns([0.96, 0.04])
                with c2: popover_feedback("JMF", t, sel)

    with tab3:
        for t, c in JDV_DATA.get(sel, {}).items():
            with st.expander(f"🌿 {t}", expanded=True):
                st.markdown(str(c)); c1, c2 = st.columns([0.96, 0.04])
                with c2: popover_feedback("JDV", t, sel)

    with tab4:
        itab = ITAB_DATA.get(sel, {})
        if itab:
            for t, c in itab.items():
                with st.expander(f"📗 {t}", expanded=True):
                    st.markdown(str(c)); c1, c2 = st.columns([0.96, 0.04])
                    with c2: popover_feedback("ITAB", t, sel)
        else:
            st.info("Aucune donnée ITAB disponible pour ce légume.")

    with tab5:
        st.subheader("📝 Saisie Terrain")
        try:
            df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO", ttl=0)
            notes = df_gs[df_gs['LEGUME'] == sel].iloc[-1].to_dict() if not df_gs[df_gs['LEGUME'] == sel].empty else {}
        except:
            df_gs = pd.DataFrame(columns=["LEGUME", "PLANTATION", "ENTRETIEN", "SANTE", "RENDEMENT", "VARIETE", "INFO_SUPP"])
            notes = {}
        with st.form(key=f"f_tho_{sel}"):
            c1, c2 = st.columns(2)
            v_p = c1.text_area("🌱 PLANTATION", value=str(notes.get("PLANTATION", "")))
            v_e = c1.text_area("🛠️ ENTRETIEN", value=str(notes.get("ENTRETIEN", "")))
            v_s = c1.text_area("🏥 SANTE", value=str(notes.get("SANTE", "")))
            v_r = c2.text_area("📊 RENDEMENT", value=str(notes.get("RENDEMENT", "")))
            v_v = c2.text_area("🧬 VARIETE", value=str(notes.get("VARIETE", "")))
            v_i = c2.text_area("➕ INFO SUPP", value=str(notes.get("INFO_SUPP", "")))
            if st.form_submit_button("💾 ENREGISTRER"):
                new_row = {"LEGUME": sel, "PLANTATION": v_p, "ENTRETIEN": v_e, "SANTE": v_s, "RENDEMENT": v_r, "VARIETE": v_v, "INFO_SUPP": v_i}
                df_final = pd.concat([df_gs[df_gs['LEGUME'] != sel], pd.DataFrame([new_row])], ignore_index=True)
                conn.update(spreadsheet=URL_SHEET, worksheet="THO", data=df_final)
                st.success("Données THO enregistrées !")

# --- CAS 3 : PAGE D'ACCUEIL ---
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.markdown("---")
    st.markdown("""
    ### DLABAL - BDD ITK Maraîchage
    
    Cet outil centralise les connaissances techniques du **GAB**, de **JMF**, de **JDV** et de l'**ITAB**.
    
    **Comment utiliser l'application :**
    1. **Sélectionnez ou taper le nom d'un légume** dans le menu déroulant à gauche.
    2. **Consultez les fiches** via les onglets thématiques.
    3. **Contribuez** en cliquant sur l'icône 📝 pour suggérer une correction.
    4. **Saisie Terrain** : Utilisez l'onglet **THO** pour enregistrer vos observations en direct.
    
    ---
    *Toutes les modifications de données textuelles sont soumises à validation.*
    """)
    st.info("👈 Commencez par choisir un légume dans la barre latérale pour afficher les données.")

st.sidebar.markdown("---")
with st.sidebar:
    st.markdown("### 🌦️ Météo locale")
    components.html('<iframe width="150" height="300" frameborder="0" scrolling="no" src="https://meteofrance.com/widget/prevision/852810##3D6AA2" style="border: none;"></iframe>', height=310)

