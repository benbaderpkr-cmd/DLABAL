import streamlit as st
import json
import os

st.set_page_config(page_title="DLABAL - SYSTÈME EXPERT", layout="wide", page_icon="🌱")

# --- FONCTIONS DE GESTION DES FICHIERS ---
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Chargement des bases de données
DATA = load_json("data.json")
RENDEMENTS = load_json("rendements.json")
JDV_DATA = load_json("jdv.json")
THO_DATA = load_json("tho.json")

# Fusionner toutes les clés pour le menu latéral
tous_les_legumes = set(list(DATA.keys()) + list(RENDEMENTS.keys()) + list(JDV_DATA.keys()) + list(THO_DATA.keys()))
liste_triee = sorted(list(tous_les_legumes))

# --- SIDEBAR ---
st.sidebar.title("🌱 DLABAL")
st.sidebar.info("FR ITK DB")
sel = st.sidebar.selectbox("Choisir un légume :", ["---"] + liste_triee)

# --- CONTENU PRINCIPAL ---
if sel != "---":
    st.title(f"📊 {sel.upper()}")
    
    # Création des 4 onglets
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 SOURCE GAB / FRAB", 
        "🚜 SOURCE JMF", 
        "🌿 SOURCE JDV", 
        "📝 SOURCE THO"
    ])

    # --- ONGLET 1 : GAB ---
    with tab1:
        c = DATA.get(sel, {})
        g = c.get("GAB_FRAB", {})
        if not g:
            st.warning("Aucune donnée GAB/FRAB.")
        else:
            if "BLOCS_IDENTITE" in g:
                blocs = g["BLOCS_IDENTITE"]
                cols = st.columns(len(blocs))
                for i, b in enumerate(blocs):
                    cols[i].success(f"**{b['titre']}**\n\n{b['contenu']}")
            
            for k, v in g.get("TECHNIQUE", {}).items():
                with st.expander(f"📌 {k}", expanded=True):
                    st.markdown(v)

    # --- ONGLET 2 : JMF ---
    with tab2:
        c = DATA.get(sel, {})
        f = c.get("JMF_FORTIER", {})
        if not f:
            st.warning("Aucune donnée JMF.")
        else:
            for titre, contenu in f.items():
                with st.expander(f"📌 {titre}", expanded=True):
                    st.markdown(contenu)

    # --- ONGLET 3 : JDV ---
    with tab3:
        j = JDV_DATA.get(sel, {})
        if not j:
            st.warning("Aucune donnée JDV.")
        else:
            if "RENDEMENT JDV" in j:
                st.success(f"**🚜 RENDEMENT JDV :** {j['RENDEMENT JDV']}")
            for titre, contenu in j.items():
                if titre != "RENDEMENT JDV":
                    with st.expander(f"🌿 {titre}", expanded=True):
                        st.markdown(contenu)

    # --- ONGLET 4 : SOURCE THO (SAISIE TERRAIN) ---
    with tab4:
        st.subheader(f"📝 Saisie Terrain - {sel}")
        
        # On recharge les données pour être sûr
        tho_full = load_json("tho.json")
        notes_legume = tho_full.get(sel, {
            "PLANTATION": "", "ENTRETIEN": "", "SANTE": "",
            "RENDEMENT": "", "VARIETE": "", "INFORMATION_SUPPLEMENTAIRE": ""
        })

        # --- LE SECRET EST ICI : key=f"form_{sel}" ---
        with st.form(key=f"form_tho_{sel}"):
            col_left, col_right = st.columns(2)
            
            with col_left:
                # CHAQUE champ doit avoir une clé unique liée au légume {sel}
                v_plan = st.text_area("🌱 PLANTATION", value=notes_legume.get("PLANTATION", ""), key=f"tp_{sel}")
                v_entr = st.text_area("🛠️ ENTRETIEN", value=notes_legume.get("ENTRETIEN", ""), key=f"te_{sel}")
                v_sant = st.text_area("🏥 SANTE", value=notes_legume.get("SANTE", ""), key=f"ts_{sel}")
            
            with col_right:
                v_rend = st.text_area("📊 RENDEMENT", value=notes_legume.get("RENDEMENT", ""), key=f"tr_{sel}")
                v_vari = st.text_area("🧬 VARIETE", value=notes_legume.get("VARIETE", ""), key=f"tv_{sel}")
                v_info = st.text_area("➕ INFO SUPP", value=notes_legume.get("INFORMATION_SUPPLEMENTAIRE", ""), key=f"ti_{sel}")

            # Bouton de sauvegarde
            submit = st.form_submit_button("💾 ENREGISTRER DANS THO.JSON")
            
            if submit:
                tho_full[sel] = {
                    "PLANTATION": v_plan,
                    "ENTRETIEN": v_entr,
                    "SANTE": v_sant,
                    "RENDEMENT": v_rend,
                    "VARIETE": v_vari,
                    "INFORMATION_SUPPLEMENTAIRE": v_info
                }
                save_json("tho.json", tho_full)
                st.success(f"Données sauvegardées pour {sel} !")
                st.rerun() # Relance l'appli pour rafraîchir les données partout
else:
    st.info("Veuillez sélectionner un légume dans la barre latérale pour commencer.")	
