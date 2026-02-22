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

ARG_DATA = load_json("arg.json")
GAB_DATA = load_json("gab.json")
JMF_DATA = load_json("jmf.json")
JDV_DATA = load_json("jdv.json")
ITAB_DATA = load_json("itab.json")
FERTI_DATA = load_json("calcul_ferti.json")
RAW_JP1 = load_json("reglages_jp1.json")

legumes_uniques = [l for l in set(list(GAB_DATA.keys()) + list(JMF_DATA.keys()) + list(JDV_DATA.keys()) + list(ARG_DATA.keys())) 
                   if GAB_DATA.get(l) or JMF_DATA.get(l) or JDV_DATA.get(l) or ARG_DATA.get(l)]
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
        if "leg_sel" in st.session_state: del st.session_state["leg_sel"]
        st.rerun()
    
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.9em; margin-top: -15px;'>BDD ITK Maraîchage</p>", unsafe_allow_html=True)
    
    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes, key="leg_sel")
    
    if sel != "---":
        st.session_state["view_mode"] = "LEGUME"
    
    st.divider()
    
    if st.button("⚙️ RÉGLAGES JP1", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_JP1"
        if "leg_sel" in st.session_state: del st.session_state["leg_sel"]
        st.rerun()
        
    if st.button("🧪 CALCUL FERTI", use_container_width=True):
        st.session_state["view_mode"] = "PAGE_FERTI"
        if "leg_sel" in st.session_state: del st.session_state["leg_sel"]
        st.rerun()
        
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""; cookies.save(); st.session_state["password_correct"] = False; st.rerun()

    st.markdown("---")
    st.markdown("### 🌦️ Météo locale")
    components.html('<iframe width="150" height="300" frameborder="0" scrolling="no" src="https://meteofrance.com/widget/prevision/852810##3D6AA2" style="border: none;"></iframe>', height=310)

# ==========================================
# 5. AFFICHAGE CENTRAL
# ==========================================

# --- CAS 1 : CALCUL FERTI ---
if st.session_state["view_mode"] == "PAGE_FERTI":
    st.title("🧪 CALCULATEUR DE FERTILISATION")
    st.markdown("---")
    legume_ferti = st.selectbox("Choisir un légume (base) :", ["---"] + sorted(FERTI_DATA.keys(), key=sans_accent))
    with st.expander("Saisie manuelle (u/ha)"):
        cn, cp, ck = st.columns(3)
        manuel_n = cn.number_input("N", min_value=0, value=0)
        manuel_p = cp.number_input("P", min_value=0, value=0)
        manuel_k = ck.number_input("K", min_value=0, value=0)
    
    col1, col2 = st.columns(2)
    longueur = col1.number_input("Longueur (m)", min_value=1, value=10)
    largeur = col2.number_input("Largeur (m)", min_value=0.1, value=1.0)
    surface = longueur * largeur

    st.markdown("#### Caractéristiques de l'engrais")
    t1, t2, t3 = st.columns(3)
    ten_N = t1.number_input("% N", value=6.0)
    ten_P = t2.number_input("% P", value=4.0)
    ten_K = t3.number_input("% K", value=10.0)
    ten_pat = st.number_input("Patentkali % K", value=30.0)

    rows = []
    facteur = surface / 10000

    def calc(n_ha, p_ha, k_ha, label):
        b_n, b_k = n_ha * facteur, k_ha * facteur
        dose_kg = round(b_n / (ten_N / 100), 1) if ten_N > 0 else 0
        k_app = round(dose_kg * (ten_K / 100), 2)
        manque_k = max(0, round(b_k - k_app, 2))
        dose_pat = round(manque_k / (ten_pat / 100), 2)
        return {"Source": label, "Besoin (U/ha)": f"N:{n_ha}|K:{k_ha}", "Dose Principal (kg)": dose_kg, "💎 Patentkali (kg)": dose_pat}

    if manuel_n > 0 or manuel_k > 0:
        rows.append(calc(manuel_n, manuel_p, manuel_k, "Manuel"))
    elif legume_ferti != "---":
        d = FERTI_DATA[legume_ferti]
        for s, v in d.items():
            if v: rows.append(calc(v["N"], v["P"], v["K"], s))
    
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# --- CAS 2 : RÉGLAGES JP1 ---
elif st.session_state["view_mode"] == "PAGE_JP1":
    st.title("⚙️ RÉGLAGES JP1")
    l_jp1 = st.selectbox("Légume :", ["---"] + sorted(RAW_JP1.keys(), key=sans_accent))
    if l_jp1 != "---":
        data = RAW_JP1[l_jp1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Pignon int", data["pignon_int"])
        c2.metric("Pignon ext", data["pignon_ext"])
        c3.metric("Disque", data["disque"])

# --- CAS 3 : PAGE LÉGUME ---
elif st.session_state["view_mode"] == "LEGUME" and sel != "---":
    st.title(f"📊 {sel.upper()}")
    tabs = st.tabs(["📘 ARG", "📋 GAB", "🚜 JMF", "🌿 JDV", "📗 ITAB", "📝 THO"])

    with tabs[0]: # Onglet ARG
        arg_l = ARG_DATA.get(sel, {})
        if arg_l:
            for titre, contenu in arg_l.items():
                with st.expander(f"📘 {titre}", expanded=True):
                    # --- CAS 1 : Format Tableau Claude (Entêtes + Lignes) ---
                    if isinstance(contenu, dict) and "lignes" in contenu:
                        df_temp = pd.DataFrame(contenu["lignes"])
                        if "col_0" in df_temp.columns:
                            df_temp = df_temp.rename(columns={"col_0": "Activité"})
                        st.table(df_temp)
                    
                    # --- CAS 2 : Format Liste simple ---
                    elif isinstance(contenu, list):
                        try:
                            st.table(pd.DataFrame(contenu))
                        except:
                            st.write(str(contenu))
                    
                    # --- CAS 3 : Format Texte classique avec nettoyage ---
                    else:
                        t = str(contenu).strip()
                        # Enlever les ":" ou "." orphelins en début de bloc
                        if t.startswith(":") or t.startswith("."):
                            t = t[1:].strip()
                        # Gestion des sauts de ligne incohérents
                        t = t.replace('\\\\n', '\n').replace('\\n', '\n')
                        # Forcer les sauts de ligne Markdown (double espace + \n)
                        st.markdown(t.replace('\n', '  \n'))
                    
                    popover_feedback("ARG", titre, sel)
        else:
            st.info("Aucune donnée ARG disponible pour ce légume.")

    with tabs[1]: # GAB
        g = GAB_DATA.get(sel, {})
        if "BLOCS_IDENTITE" in g:
            cols = st.columns(len(g["BLOCS_IDENTITE"]))
            for i, b in enumerate(g["BLOCS_IDENTITE"]):
                with cols[i]: st.success(f"**{b['titre']}**\n\n{str(b['contenu']).replace('\\\\n', '\\n').replace('\\n', '\n')}")
        for k, v in g.get("TECHNIQUE", {}).items():
            with st.expander(f"📌 {k}", expanded=True):
                st.markdown(str(v).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("GAB", k, sel)

    with tabs[2]: # JMF
        for t, c in JMF_DATA.get(sel, {}).items():
            with st.expander(f"🚜 {t}", expanded=True):
                st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("JMF", t, sel)

    with tabs[3]: # JDV
        for t, c in JDV_DATA.get(sel, {}).items():
            with st.expander(f"🌿 {t}", expanded=True):
                st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("JDV", t, sel)

    with tabs[4]: # ITAB
        for t, c in ITAB_DATA.get(sel, {}).items():
            with st.expander(f"📗 {t}", expanded=True):
                st.markdown(str(c).replace('\\\\n', '\\n').replace('\\n', '\n'))
                popover_feedback("ITAB", t, sel)

    with tabs[5]: # THO
        st.subheader("📝 Saisie Terrain (THO)")
        df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO", ttl=0)
        exist = df_gs[df_gs['LEGUME'] == sel]
        with st.form("form_tho"):
            c1, c2, c3 = st.columns(3)
            v_p = c1.text_area("Implantation :", value=exist['IMPLANTATION'].values[0] if not exist.empty else "")
            v_e = c2.text_area("Entretien :", value=exist['ENTRETIEN'].values[0] if not exist.empty else "")
            v_s = c3.text_area("Santé :", value=exist['SANTE'].values[0] if not exist.empty else "")
            c4, c5, c6 = st.columns(3)
            v_r = c4.text_area("Rendement :", value=exist['RENDEMENT'].values[0] if not exist.empty else "")
            v_v = c5.text_area("Variété :", value=exist['VARIETE'].values[0] if not exist.empty else "")
            v_i = c6.text_area("Info Supp :", value=exist['INFO_SUPP'].values[0] if not exist.empty else "")
            if st.form_submit_button("Enregistrer THO"):
                new_row = {"LEGUME": sel, "IMPLANTATION": v_p, "ENTRETIEN": v_e, "SANTE": v_s, "RENDEMENT": v_r, "VARIETE": v_v, "INFO_SUPP": v_i}
                df_final = pd.concat([df_gs[df_gs['LEGUME'] != sel], pd.DataFrame([new_row])], ignore_index=True)
                conn.update(spreadsheet=URL_SHEET, worksheet="THO", data=df_final)
                st.success("Données THO enregistrées !")

# --- ACCUEIL ---
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.markdown("---")
    st.markdown("""
    ### DLABAL - BDD ITK Maraîchage
    1. **Sélectionnez un légume** à gauche.
    2. **Consultez les fiches** via les onglets.
    3. **Contribuez** via l'icône 📝.
    ---
    *Toutes les modifications sont soumises à validation.*
    """)
