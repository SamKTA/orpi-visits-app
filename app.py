import streamlit as st
from datetime import datetime
import pandas as pd
import io
from fpdf import FPDF
from PIL import Image
import os

# Configuration de la page
st.set_page_config(page_title="Visite de Copropriété ORPI", layout="wide")

# Fonction pour créer le PDF
def create_pdf(data, main_image, observation_images):
    pdf = FPDF()
    pdf.add_page()
    
    # En-tête
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(227, 31, 43)  # Rouge ORPI
    pdf.cell(0, 10, 'Rapport de Visite - ORPI', 0, 1, 'C')
    
    # Informations principales
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0, 0, 0)  # Noir
    pdf.cell(0, 10, f"Date: {data['date']}", 0, 1)
    pdf.cell(0, 10, f"Adresse: {data['address']}", 0, 1)
    pdf.cell(0, 10, f"Rédacteur: {data['redacteur']}", 0, 1)
    pdf.cell(0, 10, f"Horaires: {data['arrival_time']} - {data['departure_time']}", 0, 1)
    pdf.cell(0, 10, f"Code Immeuble: {data['building_code']}", 0, 1)
    
    # Image principale
    if main_image is not None:
        pdf.image(main_image, x=10, y=None, w=190)
    
    # Observations
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Observations', 0, 1)
    
    return pdf

# Titre
st.title("📋 Visite de Copropriété ORPI")
st.markdown("---")

# Création des colonnes
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Informations générales")
    
    # Champs obligatoires
    date = st.date_input("Date de la visite", datetime.now())
    address = st.text_input("Adresse")
    redacteur = st.selectbox("Rédacteur", ["David SAINT-GERMAIN", "Elodie BONNAY"])
    arrival_time = st.time_input("Heure d'arrivée")
    departure_time = st.time_input("Heure de départ")
    building_code = st.text_input("Code Immeuble")
    
    # Upload de l'image principale
    main_image = st.file_uploader("Photo principale de la copropriété", type=['png', 'jpg', 'jpeg'])
    if main_image:
        st.image(main_image, caption="Photo principale", use_column_width=True)

with col2:
    st.subheader("🔍 Observations")
    
    # Gestion des observations avec st.session_state
    if 'observations' not in st.session_state:
        st.session_state.observations = []
    
    # Formulaire d'ajout d'observation
    with st.form("observation_form"):
        obs_type = st.radio("Type d'observation", ["✅ Positive", "❌ Négative"])
        description = st.text_area("Description")
        photo = st.file_uploader("Photo de l'observation", type=['png', 'jpg', 'jpeg'])
        
        submit_button = st.form_submit_button("Ajouter l'observation")
        if submit_button:
            if description:  # Vérifie qu'il y a au moins une description
                st.session_state.observations.append({
                    "type": obs_type,
                    "description": description,
                    "photo": photo
                })
                st.success("Observation ajoutée avec succès!")
            else:
                st.error("Veuillez ajouter une description à votre observation.")

    # Affichage des observations
    if st.session_state.observations:
        st.markdown("### 📋 Liste des observations")
        for idx, obs in enumerate(st.session_state.observations):
            with st.expander(f"Observation {idx + 1} - {obs['type']}"):
                st.write(obs["description"])
                if obs["photo"]:
                    st.image(obs["photo"], caption=f"Photo observation {idx + 1}")
    else:
        st.info("Aucune observation ajoutée pour le moment.")

# Bouton de génération du rapport
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 Générer le rapport PDF", use_container_width=True):
        if address and building_code:  # Vérifie les champs obligatoires minimaux
            with st.spinner("Génération du rapport en cours..."):
                # Collecte des données
                data = {
                    "date": date,
                    "address": address,
                    "redacteur": redacteur,
                    "arrival_time": arrival_time,
                    "departure_time": departure_time,
                    "building_code": building_code
                }
                
                # Création du PDF
                try:
                    pdf = create_pdf(data, main_image, st.session_state.observations)
                    pdf_output = pdf.output(dest='S').encode('latin1')
                    
                    # Téléchargement du PDF
                    st.download_button(
                        label="📥 Télécharger le rapport PDF",
                        data=pdf_output,
                        file_name=f"rapport_visite_{date.strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Erreur lors de la génération du PDF: {str(e)}")
        else:
            st.warning("⚠️ Veuillez remplir au moins l'adresse et le code immeuble.")
