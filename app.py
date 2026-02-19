import streamlit as st
import json
import os
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_cookies_manager import EncryptedCookieManager

# ==========================================
# 1. CONFIGURATION, COOKIES ET SECURITE
# ==========================================
st.set_page_config(page_title="DLABAL - SYSTÈME EXPERT", layout="wide", page_icon="🌱")

cookies = EncryptedCookieManager(password="cle_secrete_dlabal_2026")
if not cookies.ready():
    st.stop()

def check_password():
    if st.session_state.get("password_correct") or cookies.get("auth_token") == "valide":
        st.session_state["password_correct"] = True
        return True
    
    st.title("🔐 Accès Restreint")
    with st.form("auth_form", clear_on_submit=False):
        pwd = st.text_input("Entrez le mot de passe DLABAL :", type="password")
        submit = st.form_submit_button("Valider")
        if submit:
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

# ==========================================
# 2. CONNEXIONS ET CHARGEMENT (PILIERS 1 & 5)
# ==========================================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1-NhzHwiedbc5asVHQW_WdwB0WWz_JTsELbR0l7vO9-s/edit#gid=0"
URL_SHEET2 = "https://docs.google.com/spreadsheets/d/1wUngO5HjSCRYbWzd0hMxKBj4aUD4ThW1ishVvaOwOcc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def envoyer_feedback(legume, nom_onglet_app, message):
    try:
        nom_sheet = legume.upper()
        # Création de la ligne avec tes 4 colonnes
        new_row = pd.DataFrame([{
            "DATE": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "LEGUME": nom_sheet,
            "ONGLET": nom_onglet_app,
            "FEEDBACK": message
        }])
        
        try:
            # On force la lecture sur URL_SHEET2
            df_existing = conn.read(spreadsheet=URL_SHEET2, worksheet=nom_sheet, ttl=0)
            df_updated = pd.concat([df_existing, new_row], ignore_index=True)
        except:
            # Si l'onglet n'existe pas, on commence avec la nouvelle ligne
            df_updated = new_row
        
        # On force l'écriture sur URL_SHEET2
        conn.update(spreadsheet=URL_SHEET2, worksheet=nom_sheet, data=df_updated)
        st.success(f"✅ Suggestion enregistrée dans l'onglet {nom_sheet} (Feedback)")
    except Exception as e:
        st.error(f"Erreur GSheets : {e}")
        
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

GAB_DATA = load_json("gab.json")
JMF_DATA = load_json("jmf.json")
JDV_DATA = load_json("jdv.json")
SOURCES_JMF = load_json("sources_jmf.json")
REGLAGES_JP1_OFFICIEL = load_json("reglages_jp1.json")

cles_itk = list(SOURCES_JMF.get("reglages_itk", {}).keys())
tous_les_legumes = sorted(list(set(list(GAB_DATA.keys()) + list(JMF_DATA.keys()) + list(JDV_DATA.keys()) + cles_itk)))

# ==========================================
# 3. SIDEBAR (INTERFACE ET NAVIGATION)
# ==========================================
with st.sidebar:
    # Titre Accueil en Gras (Pilier 4)
    if st.button("**DLABAL**", key="btn_home", use_container_width=True):
        st.session_state["view_mode"] = "DOSSIER"
        st.session_state["last_sel"] = "---"
        st.session_state["reset_key"] = st.session_state.get("reset_key", 0) + 1
        st.rerun()
    
    st.markdown("<p style='font-size: 0.85em; color: gray; margin-top: -15px; margin-bottom: 20px;'>Base de données maraîchère</p>", unsafe_allow_html=True)
    
    # Dropdown de sélection
    res_key = st.session_state.get("reset_key", 0)
    sel = st.selectbox("Choisir un légume :", ["---"] + tous_les_legumes, key=f"sel_{res_key}")
    
    if sel != "---":
        if "last_sel" not in st.session_state or st.session_state["last_sel"] != sel:
            st.session_state["view_mode"] = "DOSSIER"
            st.session_state["last_sel"] = sel

    st.divider()
    
    # Boutons d'outils (Compact)
    if st.button("📊 RÉGLAGES JP1 GLOBAUX", use_container_width=True):
        st.session_state["view_mode"] = "JP1_GLOBAL"
        st.rerun()

    st.link_button("📩 Me contacter", "https://docs.google.com/forms/d/e/1FAIpQLSf0xs8AXpRAkZ4yChDo1HtarrAsxxnudS5TXMVtaZRwrbClmQ/viewform?usp=dialog", use_container_width=True)
    
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        cookies["auth_token"] = ""
        cookies.save()
        st.session_state["password_correct"] = False
        st.rerun()

# ==========================================
# 4. LOGIQUE D'AFFICHAGE (PILIERS 2, 4 & 5)
# ==========================================

# --- MODE RÉGLAGES JP1 GLOBAUX ---
if st.session_state.get("view_mode") == "JP1_GLOBAL":
    st.title("🚜 RÉGLAGES OFFICIELS JP1 (CONSTRUCTEUR)")
    st.warning("**⚠️ AVERTISSEMENT :** Ces réglages sont indicatifs.")
    
    if st.button("⬅️ Retour au dossier"):
        st.session_state["view_mode"] = "DOSSIER"
        st.rerun()

    # Formulaire de suggestion (Fermé par défaut)
    with st.expander("💡 Propose ton réglage du JP1.", expanded=False):
        with st.form("form_sug_jp1", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            s_leg = c1.text_input("Légume concerné")
            s_rouleau = c2.text_input("rouleau")
            s_pav = c3.text_input("pignon AV")
            c4, c5, c6 = st.columns(3)
            s_par = c4.text_input("pignon AR")
            s_brosse = c5.text_input("Brosse")
            s_info = c6.text_input("info supp.")
            if st.form_submit_button("Enregistrer mon conseil"):
                if s_leg and s_rouleau:
                    try:
                        df_sug = conn.read(spreadsheet=URL_SHEET2, worksheet="SUGGESTIONS", ttl=0)
                    except:
                        df_sug = pd.DataFrame(columns=["DATE", "LEGUME", "ROULEAU", "PIGNON_AV", "PIGNON_AR", "BROSSE", "INFO_SUPP"])
                    new_sug = pd.DataFrame([{"DATE": datetime.now().strftime("%d/%m/%Y"), "LEGUME": s_leg, "ROULEAU": s_rouleau, "PIGNON_AV": s_pav, "PIGNON_AR": s_par, "BROSSE": s_brosse, "INFO_SUPP": s_info}])
                    df_updated = pd.concat([df_sug, new_sug], ignore_index=True)
                    conn.update(spreadsheet=URL_SHEET2, worksheet="SUGGESTIONS", data=df_updated)
                    st.success(f"Conseil pour le {s_leg} envoyé !")
                else:
                    st.error("Merci de renseigner au moins le légume et le type de rouleau.")

    st.divider()
    # Liste constructeur
    liste = REGLAGES_JP1_OFFICIEL.get("reglages", [])
    if liste:
        st.subheader("📋 Préconisations constructeur")
        df_c = pd.DataFrame(liste)
        rech = st.text_input("🔍 Filtrer la liste officielle...", key="filter_jp1")
        if rech: 
            df_c = df_c[df_c['légume'].str.contains(rech, case=False)]
        st.dataframe(df_c.rename(columns={"légume":"Légume", "pignon_av":"AV", "pignon_ar":"AR", "distance_cm":"cm"}), use_container_width=True, hide_index=True)

    st.divider()
    # Tableau technique
    st.subheader("⚙️ Tableau des distances de semis (mm)")
    dist_data = {"Nombre de trous": ["2", "3", "4", "6", "8", "10", "12", "16", "20", "24", "30", "36"], "14/9": [320, 210, 160, 105, 80, 64, 53, 40, 32, 27, 21, 18], "14/10": [360, 230, 180, 115, 90, 72, 58, 45, 36, 29, 24, 20], "13/10": [380, 250, 190, 125, 95, 76, 63, 48, 38, 32, 25, 21], "13/11": [420, 280, 210, 140, 105, 84, 70, 53, 42, 35, 28, 23], "11/10": [460, 300, 230, 150, 115, 92, 75, 58, 46, 38, 31, 26], "11/11": [500, 330, 250, 165, 125, 100, 83, 63, 50, 42, 33, 28], "10/11": [540, 360, 270, 180, 135, 108, 90, 68, 54, 45, 36, 30], "11/13": [580, 390, 290, 195, 145, 116, 98, 73, 58, 49, 39, 32], "10/13": [640, 430, 320, 215, 160, 128, 108, 80, 64, 54, 43, 36], "10/14": [700, 460, 350, 230, 175, 140, 115, 88, 70, 58, 47, 39], "9/14": [760, 510, 380, 255, 190, 152, 128, 95, 76, 64, 51, 42]}
    st.dataframe(pd.DataFrame(dist_data), use_container_width=True, hide_index=True)

# --- MODE DOSSIER / ACCUEIL ---
else:
    if sel == "---":
        st.title("🌱 Bienvenue sur DLABAL")
        st.markdown("### Une base de notes partagée, sans chichis.")
        st.markdown("""
        J’ai regroupé ici ce que j’ai pu glaner en formation ou sur le terrain. C’est sans prétention : je ne cherche pas à donner de leçon, juste à mettre mes notes au propre pour qu'elles servent à d'autres. L’outil est gratuit et je le bricole sur mon temps libre, donc c’est encore un peu rustique.
        
        **Si tu as de l'expérience à partager, n'hésite pas à mettre la main à la pâte :**
        
        * **Expériences de terrain :** Ça se passe dans l'onglet **THO**. Tes retours alimentent la base commune visible dans THO_RESULT.
        * **Réglages du semoir JP1 :** À gauche dans la page **Réglages JP1 globaux**, tu peux laisser tes propres réglages par légume. Ils sont compilés plus bas dans la section "Conseils persos JP1".
        
        L'idée, c'est que ça profite à tout le monde. Sers-toi, et complète si le cœur t'en dit.
        """)
        st.info("👈 Sélectionnez un légume dans le menu à gauche pour consulter les fiches techniques.")
    else:
        st.title(f"📊 {sel.upper()}")
        tab1, tab2, tab3, tab4 = st.tabs(["📋 GAB / FRAB", "🚜 JMF", "🌿 JDV", "📝 THO"])

        with tab1:
            g = GAB_DATA.get(sel, {})
            if g:
                if "BLOCS_IDENTITE" in g:
                    cols = st.columns(len(g["BLOCS_IDENTITE"]))
                    for i, b in enumerate(g["BLOCS_IDENTITE"]):
                        cols[i].success(f"**{b['titre']}**\n\n{b['contenu']}")
                for k, v in g.get("TECHNIQUE", {}).items():
                    with st.expander(f"📌 {k}", expanded=True): st.markdown(v)
            else:
                st.info(f"Aucune donnée de GAB / FRAB pour {sel}")
                
            st.divider()
            with st.expander("📝 Une erreur dans GAB / FRAB ?"):
                with st.form(key=f"fb_gab_{sel}", clear_on_submit=True):
                    msg = st.text_area("Ta suggestion :")
                    if st.form_submit_button("Envoyer"):
                        envoyer_feedback(sel, "GAB / FRAB", msg)

        with tab2:
            found_jmf = False
            # 1. Gestion des réglages ITK (Sources JMF)
            base = SOURCES_JMF.get("reglages_itk", {})
            # On cherche avec plusieurs variantes de casse pour être robuste
            reg = base.get(sel) or base.get(sel.capitalize()) or base.get(sel.upper())
            
            if reg:
                found_jmf = True
                c1, c2 = st.columns(2)
                c1.info(f"**📍 JMF**\n- Rouleau : `{reg.get('jmf', {}).get('rouleau', '?')}`")
                c2.warning(f"**🚜 Terrateck**\n- Rouleau : `{reg.get('terrateck', {}).get('rouleau', '?')}`")
            
            # 2. Gestion du contenu texte (JMF_DATA)
            # On cherche 'Ail', 'AIL' ou 'ail'
            f = JMF_DATA.get(sel) or JMF_DATA.get(sel.capitalize()) or JMF_DATA.get(sel.upper())
            
            if f:
                found_jmf = True
                for t, c in f.items():
                    with st.expander(f"📌 {t}", expanded=True): 
                        st.markdown(c)
            
            if not found_jmf:
                st.info(f"Aucune donnée de JMF pour {sel}")
                
            st.divider()
            with st.expander("📝 Une erreur dans JMF ?"):
                with st.form(key=f"fb_jmf_{sel}", clear_on_submit=True):
                    msg = st.text_area("Ta suggestion :")
                    if st.form_submit_button("Envoyer"):
                        envoyer_feedback(sel, "JMF", msg)
                        
        with tab3:
            j = JDV_DATA.get(sel, {})
            if j:
                if "RENDEMENT JDV" in j: st.success(f"**🚜 RENDEMENT JDV :** {j['RENDEMENT JDV']}")
                for t, c in j.items():
                    if t != "RENDEMENT JDV":
                        with st.expander(f"🌿 {t}", expanded=True): st.markdown(str(c))
            else:
                st.info(f"Aucune donnée de JDV pour {sel}")

            st.divider()
            with st.expander("📝 Une erreur dans JDV ?"):
                with st.form(key=f"fb_jdv_{sel}", clear_on_submit=True):
                    msg = st.text_area("Ta suggestion :")
                    if st.form_submit_button("Envoyer"):
                        envoyer_feedback(sel, "JDV", msg)

        with tab4:
            st.subheader(f"📝 Saisie Terrain - {sel}")
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
                    st.success("Enregistré dans GSheet !")

            st.divider()
            with st.expander("📝 Une erreur dans THO ?"):
                with st.form(key=f"fb_tho_err_{sel}", clear_on_submit=True):
                    msg = st.text_area("Ta suggestion :")
                    if st.form_submit_button("Envoyer"):
                        envoyer_feedback(sel, "THO", msg)

st.sidebar.markdown("---")
with st.sidebar:
    st.markdown("### 🌦️ Météo locale")
    
    # Votre iframe Météo-France
    mf_iframe = """
    <iframe id="widget_autocomplete_preview" 
            width="150" 
            height="300" 
            frameborder="0" 
            scrolling="no"
            src="https://meteofrance.com/widget/prevision/852810##3D6AA2" 
            title="Prévisions Sérigné par Météo-France"
            style="display: block; margin: 0 auto; border: none;"> 
    </iframe>
    """
    
    # Affichage du composant
    import streamlit.components.v1 as components
    components.html(mf_iframe, height=310)









