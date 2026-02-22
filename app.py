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

if "user_name" not in st.session_state: st.session_state["user_name"] = ""
if "view_mode" not in st.session_state: st.session_state["view_mode"] = "ACCUEIL"

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
JP1_OFFICIEL = load_json("reglages_jp1.json")
JP1_JMF = load_json("reglages_jmf.json")

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
    # Navigation DLABAL
    if st.button("**DLABAL**", use_container_width=True):
        st.session_state["view_mode"] = "ACCUEIL"
        st.rerun()
    
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.9em; margin-top: -15px;'>BDD ITK Maraîchage</p>", unsafe_allow_html=True)
    
    def on_change_sidebar():
        if st.session_state["nav_sidebar"] != "---":
            st.session_state["view_mode"] = "LEGUME"

    st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes, key="nav_sidebar", on_change=on_change_sidebar)
    
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

    st.markdown("---")
    st.markdown("### 🌦️ Météo locale")
    components.html('<iframe width="150" height="300" frameborder="0" scrolling="no" src="https://meteofrance.com/widget/prevision/852810##3D6AA2" style="border: none;"></iframe>', height=310)

# ==========================================
# 5. AFFICHAGE CENTRAL
# ==========================================

# --- PAGE FERTILISATION ---
if st.session_state["view_mode"] == "PAGE_FERTI":
    st.title("🧪 CALCULATEUR DE FERTILISATION")
    leg_f = st.selectbox("Légume pour base de calcul :", ["---"] + sorted(FERTI_DATA.keys(), key=sans_accent), key="sel_ferti")
    
    with st.expander("Saisie manuelle (u/ha)"):
        cn, cp, ck = st.columns(3)
        manuel_n = cn.number_input("N", 0)
        manuel_p = cp.number_input("P", 0)
        manuel_k = ck.number_input("K", 0)
    col1, col2 = st.columns(2)
    longueur, largeur = col1.number_input("Longueur (m)", 1, 10), col2.number_input("Largeur (m)", 0.1, 1.0)
    surface = longueur * largeur
    st.markdown("#### Caractéristiques de l'engrais")
    t1, t2, t3 = st.columns(3)
    ten_N, ten_P, ten_K = t1.number_input("% N", value=6.0), t2.number_input("% P", value=4.0), t3.number_input("% K", value=10.0)
    ten_pat = st.number_input("Patentkali % K", value=30.0)
    
    rows = []; facteur = surface / 10000
    def calc(n_ha, p_ha, k_ha, label):
        b_n, b_k = n_ha * facteur, k_ha * facteur
        dose_kg = round(b_n / (ten_N / 100), 1) if ten_N > 0 else 0
        k_app = round(dose_kg * (ten_K / 100), 2)
        manque_k = max(0, round(b_k - k_app, 2))
        dose_pat = round(manque_k / (ten_pat / 100), 2) if ten_pat > 0 else 0
        return {"Source": label, "Besoin (U/ha)": f"N:{n_ha}|K:{k_ha}", "Dose Principal (kg)": dose_kg, "💎 Patentkali (kg)": dose_pat}
    
    if (manuel_n > 0 or manuel_k > 0):
        rows.append(calc(manuel_n, manuel_p, manuel_k, "Manuel"))
    elif leg_f != "---":
        d = FERTI_DATA.get(leg_f, {})
        for s, v in d.items():
            if v: rows.append(calc(v["N"], v["P"], v["K"], s))
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# --- PAGE REGLAGES JP1 ---
elif st.session_state["view_mode"] == "PAGE_JP1":
    st.title("⚙️ RÉGLAGES JP1 TERRADONIS")
    # Fusion des listes de légumes des deux fichiers reglages
    list_off = [item["CULTURE"] for item in JP1_OFFICIEL.get("reglages", [])]
    list_jmf_jp1 = [item["CULTURE"] for item in JP1_JMF.get("reglages", [])]
    full_list_jp1 = sorted(list(set(list_off + list_jmf_jp1)), key=sans_accent)
    
    l_jp1 = st.selectbox("Choisir un légume :", ["---"] + full_list_jp1, key="sel_jp1")
    
    if l_jp1 != "---":
        tableau_data = []
        off_item = next((i for i in JP1_OFFICIEL.get("reglages", []) if i["CULTURE"] == l_jp1), None)
        tableau_data.append({
            "Source": "OFFICIEL (Terrateck)", 
            "Rouleau(x)": off_item.get("ROULEAUX", "-") if off_item else "Aucune donnée",
            "Pignons (AV/AR)": "-", "Observations": "-"
        })
        jmf_item_jp1 = next((i for i in JP1_JMF.get("reglages", []) if i["CULTURE"] == l_jp1), None)
        if jmf_item_jp1:
            tableau_data.append({
                "Source": "JMF (Grelinette)", 
                "Rouleau(x)": jmf_item_jp1.get("ROULEAU", "-"),
                "Pignons (AV/AR)": f"{jmf_item_jp1.get('AV','-')} / {jmf_item_jp1.get('AR','-')}", 
                "Observations": jmf_item_jp1.get("OBS", "-")
            })
        st.table(pd.DataFrame(tableau_data))

# --- PAGE LEGUME (ONGLETS) ---
elif st.session_state["view_mode"] == "LEGUME":
    sel_legume = st.session_state.get("nav_sidebar", "---")
    if sel_legume != "---":
        st.title(f"📊 {sel_legume.upper()}")
        tabs = st.tabs(["📘 ARG", "📋 GAB", "🚜 JMF", "🌿 JDV", "📗 ITAB", "📝 THO"])
        
        with tabs[0]: # ARG
            arg_l = ARG_DATA.get(sel_legume, {})
            if arg_l:
                for t, c in arg_l.items():
                    with st.expander(f"📘 {t}", expanded=True):
                        if isinstance(c, dict) and "lignes" in c:
                            df_t = pd.DataFrame(c["lignes"]).rename(columns={"Janv.":"J","Fév.":"F","Mars":"M","Avril":"A","Mai":"M ","Juin":"J ","Juill.":"J  ","Août":"A ","Sept.":"S","Oct.":"O","Nov.":"N","Déc.":"D","col_0":"Activité"})
                            st.dataframe(df_t, use_container_width=True)
                        else: st.markdown(str(c).replace('\\\\n', '  \n').replace('\\n', '  \n'))
                        popover_feedback("ARG", t, sel_legume)
            else: st.info(f"Données ARG absentes pour {sel_legume}.")

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
            else: st.info("Données GAB absentes.")

        with tabs[2]: # JMF
            j_data = JMF_DATA.get(sel_legume, {})
            if j_data:
                for t, c in j_data.items():
                    with st.expander(f"🚜 {t}", expanded=True):
                        st.markdown(str(c).replace('\\\\n', '\\n'))
                        popover_feedback("JMF", t, sel_legume)

        with tabs[3]: # JDV
            v_data = JDV_DATA.get(sel_legume, {})
            if v_data:
                for t, c in v_data.items():
                    with st.expander(f"🌿 {t}", expanded=True):
                        st.markdown(str(c).replace('\\\\n', '\\n'))
                        popover_feedback("JDV", t, sel_legume)

        with tabs[4]: # ITAB
            i_data = ITAB_DATA.get(sel_legume, {})
            if i_data:
                for t, c in i_data.items():
                    with st.expander(f"📗 {t}", expanded=True):
                        st.markdown(str(c).replace('\\\\n', '\\n'))
                        popover_feedback("ITAB", t, sel_legume)

        with tabs[5]: # THO
            st.subheader("📝 Saisie Terrain (THO)")
            df_gs = conn.read(spreadsheet=URL_SHEET, worksheet="THO", ttl=0)
            exist = df_gs[df_gs['LEGUME'] == sel_legume]
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
                    new_row = {"LEGUME": sel_legume, "IMPLANTATION": v_p, "ENTRETIEN": v_e, "SANTE": v_s, "RENDEMENT": v_r, "VARIETE": v_v, "INFO_SUPP": v_i}
                    df_final = pd.concat([df_gs[df_gs['LEGUME'] != sel_legume], pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(spreadsheet=URL_SHEET, worksheet="THO", data=df_final)
                    st.success("Données THO enregistrées !")

# --- ACCUEIL ---
else:
    st.title("🌱 Bienvenue sur DLABAL")
    st.markdown("---")
    st.markdown("### DLABAL - BDD ITK Maraîchage\n\n"
                "Cette application centralise les données techniques pour le maraîchage.\n\n"
                "1. **Sélectionnez un légume** dans la barre latérale pour consulter les fiches (ARG, GAB, JMF, etc.).\n"
                "2. **Utilisez les outils** (⚙️ Réglages JP1, 🧪 Calcul Ferti) pour vos besoins spécifiques.\n"
                "3. **Contribuez** en utilisant l'icône 📝 pour envoyer vos retours ou remplir l'onglet THO.")
    st.info("Utilisez la barre latérale à gauche pour naviguer.")

