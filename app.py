import streamlit as st
from datetime import datetime
import pandas as pd
import io
from fpdf import FPDF
from PIL import Image
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Configuration de la page
st.set_page_config(page_title="Visite de Copropriété ORPI", layout="wide")

# Fonction pour nettoyer le texte des émojis
def clean_text_for_pdf(text):
    text = text.replace("✅ ", "")
    text = text.replace("❌ ", "")
    return text

# Fonction pour envoyer l'email
def send_pdf_by_email(pdf_content, date, address):
    try:
        recipient_email = "skita@orpi.com"
        
        msg = MIMEMultipart()
        msg['From'] = st.secrets["email"]["sender"]
        msg['To'] = recipient_email
        msg['Subject'] = f"Rapport de visite - {address} - {date}"
        
        body = f"""
        Bonjour,

        Veuillez trouver ci-joint le rapport de la visite effectuée le {date} à l'adresse : {address}.

        Cordialement,
        Service Syndic ORPI
        """
        msg.attach(MIMEText(body, 'plain'))
        
        pdf_attachment = MIMEApplication(pdf_content, _subtype='pdf')
        pdf_attachment.add_header('Content-Disposition', 'attachment', 
                                filename=f'rapport_visite_{date}.pdf')
        msg.attach(pdf_attachment)
        
        with smtplib.SMTP_SSL(st.secrets["email"]["smtp_server"], 
                             st.secrets["email"]["smtp_port"]) as server:
            server.login(st.secrets["email"]["username"], 
                        st.secrets["email"]["password"])
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'envoi de l'email : {str(e)}")
        return False

# Fonction pour créer le PDF
def create_pdf(data, main_image_file, observations):
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
    if main_image_file is not None:
        temp_image_path = "temp_main_image.jpg"
        try:
            with open(temp_image_path, "wb") as f:
                f.write(main_image_file.getvalue())
            pdf.image(temp_image_path, x=10, y=None, w=190)
        finally:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
    
    # Observations
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Observations', 0, 1)
    
    for idx, obs in enumerate(observations):
        pdf.set_font('Arial', 'B', 12)
        obs_type = "Positive" if "Positive" in obs['type'] else "Négative"
        pdf.cell(0, 10, f"Observation {idx + 1} - {obs_type}", 0, 1)
        
        pdf.set_font('Arial', '', 12)
        description = clean_text_for_pdf(obs['description'])
        pdf.multi_cell(0, 10, description)
        
        if obs['photo'] is not None:
            temp_obs_path = f"temp_obs_{idx}.jpg"
            try:
                with open(temp_obs_path, "wb") as f:
                    f.write(obs['photo'].getvalue())
                pdf.image(temp_obs_path, x=10, y=None, w=190)
            finally:
                if os.path.exists(temp_obs_path):
                    os.remove(temp_obs_path)
        
        pdf.cell(0, 10, '', 0, 1)
    
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
            if description:
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
    if st.button("Générer le rapport PDF", use_container_width=True):
        if address and building_code:
            with st.spinner("Génération et envoi du rapport en cours..."):
                data = {
                    "date": date,
                    "address": address,
                    "redacteur": redacteur,
                    "arrival_time": arrival_time,
                    "departure_time": departure_time,
                    "building_code": building_code
                }
                
                try:
                    pdf = create_pdf(data, main_image, st.session_state.observations)
                    pdf_output = pdf.output(dest='S').encode('latin1')
                    
                    # Envoi du PDF par email
                    if send_pdf_by_email(pdf_output, date.strftime('%Y-%m-%d'), address):
                        st.success("✅ PDF généré et envoyé par email avec succès!")
                    
                    # Proposition de téléchargement
                    st.download_button(
                        label="Télécharger le rapport PDF",
                        data=pdf_output,
                        file_name=f"rapport_visite_{date.strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Erreur lors de la génération du PDF: {str(e)}")
        else:
            st.warning("Veuillez remplir au moins l'adresse et le code immeuble.")
