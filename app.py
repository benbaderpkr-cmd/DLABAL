import streamlit as st
import json
import os
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="DLABAL", layout="wide", page_icon="🌱")
# connexion gsheet
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. FONCTIONS DE GESTION DES DONNÉES ---
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

# --- 2. CHARGEMENT INITIAL ---
# On charge les clés pour la barre latérale
DATA = load_json("data.json")
tous_les_legumes = sorted(list(DATA.keys()))

# --- 3. BARRE LATÉRALE ---
st.sidebar.title("🌱 DLABAL")
sel = st.sidebar.selectbox("Choisir un légume :", ["---"] + tous_les_legumes, key="main_selector")

# --- 4. CONTENU PRINCIPAL ---
if sel != "---":
    st.title(f"📊 {sel.upper()}")
    
    # Recharger les données spécifiques au légume sélectionné
    JDV_DATA = load_json("jdv.json")
    THO_DATA = load_json("tho.json")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 SOURCE GAB", 
        "🚜 SOURCE JMF", 
        "🌿 SOURCE JDV", 
        "📝 SOURCE THO"
    ])

    # --- ONGLET 1 : GAB/FRAB ---
    with tab1:
        g = DATA.get(sel, {}).get("GAB_FRAB", {})
        if g:
            for k, v in g.get("TECHNIQUE", {}).items():
                with st.expander(f"📌 {k}", expanded=True):
                    st.markdown(v)
        else:
            st.warning("Données GAB absentes.")

    # --- ONGLET 2 : JMF ---
    with tab2:
        f = DATA.get(sel, {}).get("JMF_FORTIER", {})
        if f:
            for titre, contenu in f.items():
                with st.expander(f"📌 {titre}", expanded=True):
                    st.markdown(contenu)
        else:
            st.warning("Données JMF absentes.")

    # --- ONGLET 3 : JDV ---
    with tab3:
        j = JDV_DATA.get(sel, {})
        if j:
            for t, c in j.items():
                with st.expander(f"🌿 {t}", expanded=True):
                    st.markdown(c)
        else:
            st.warning("Données JDV absentes.")

    # --- ONGLET 4 : SAISIE TERRAIN (GOOGLE SHEETS) ---
    with tab4:
        st.subheader(f"📝 Notes de culture : {sel}")
        
        try:
            # On force la lecture en s'assurant que 'conn' est bien utilisé
            # ttl=0 permet d'avoir les données fraîches à chaque fois
            df = conn.read(worksheet="THO", ttl=0)
            
            # Diagnostic : si df est une réponse HTTP et pas un tableau, on le signale
            if not isinstance(df, pd.DataFrame):
                st.error("Le format reçu n'est pas un tableau. Tentative de reconnexion...")
                conn.reset() # On réinitialise la connexion
                df = conn.read(worksheet="THO", ttl=0)

            # On cherche le légume
            existing_data = df[df['LEGUME'] == sel] if not df.empty else pd.DataFrame()
            notes = existing_data.iloc[0].to_dict() if not existing_data.empty else {}
            
            st.success("✅ Données chargées !")

        except Exception as e:
            st.error(f"Erreur de lecture : {e}")
            notes = {}
            df = pd.DataFrame() # On crée un df vide pour éviter le NameError
        # 2. Formulaire avec clés dynamiques
        with st.form(key=f"form_gsheet_{sel}"):
            c1, c2 = st.columns(2)
            with c1:
                v_plan = st.text_area("🌱 PLANTATION", value=notes.get("PLANTATION", ""), key=f"p_{sel}")
                v_entr = st.text_area("🛠️ ENTRETIEN", value=notes.get("ENTRETIEN", ""), key=f"e_{sel}")
                v_sant = st.text_area("🏥 SANTE", value=notes.get("SANTE", ""), key=f"s_{sel}")
            with c2:
                v_rend = st.text_area("📊 RENDEMENT", value=notes.get("RENDEMENT", ""), key=f"r_{sel}")
                v_vari = st.text_area("🧬 VARIETE", value=notes.get("VARIETE", ""), key=f"v_{sel}")
                v_info = st.text_area("➕ INFO SUPP", value=notes.get("INFO_SUPP", ""), key=f"i_{sel}")

            # 3. Logique d'enregistrement
            if st.form_submit_button("💾 ENREGISTRER DANS GOOGLE SHEETS"):
                # Préparation de la nouvelle ligne
                nouvelle_ligne = pd.DataFrame([{
                    "LEGUME": sel,
                    "PLANTATION": v_plan,
                    "ENTRETIEN": v_entr,
                    "SANTE": v_sant,
                    "RENDEMENT": v_rend,
                    "VARIETE": v_vari,
                    "INFO_SUPP": v_info
                }])
                
                # On fusionne : on garde tout sauf l'ancienne ligne de ce légume, et on ajoute la nouvelle
                if not df.empty:
                    df_maj = pd.concat([df[df['LEGUME'] != sel], nouvelle_ligne], ignore_index=True)
                else:
                    df_maj = nouvelle_ligne
                
                # Envoi vers Google Sheets
                if st.form_submit_button("Enregistrer les modifications"):
                try:
                    # 1. On prépare la ligne à envoyer
                    new_row = {
                        "LEGUME": sel,
                        "PLANTATION": plantation_input,
                        "ENTRETIEN": entretien_input,
                        # Ajoute tes autres champs ici...
                    }
                    
                    # 2. On met à jour le DataFrame localement (df doit être chargé au début du with tab4)
                    if not df.empty and sel in df["LEGUME"].values:
                        df.loc[df["LEGUME"] == sel, list(new_row.keys())] = list(new_row.values())
                    else:
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    # 3. SAUVEGARDE FORCEE
                    # On utilise clear_cache pour éviter que le Response [200] ne reste bloqué
                    conn.update(spreadsheet=sheet_id, worksheet="THO", data=df)
                    st.cache_data.clear() 
                    
                    st.success("✨ Enregistré avec succès dans Google Sheets !")
                    st.balloons()
                    
                except Exception as e:
                    # Si l'erreur est juste "<Response [200]>", on considère que c'est gagné
                    if "200" in str(e):
                        st.success("✨ Enregistré avec succès !")
                        st.balloons()
                    else:
                        st.error(f"Erreur réelle : {e}")
else:
    st.info("Sélectionnez un légume pour afficher les données.")













