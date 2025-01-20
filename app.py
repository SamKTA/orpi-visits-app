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
from streamlit_drawable_canvas import st_canvas
import base64
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Visite de Copropriété ORPI", layout="wide")

def clean_text_for_pdf(text):
    text = str(text)
    text = text.replace("✅ ", "")
    text = text.replace("❌ ", "")
    text = text.replace("'", "'")
    text = text.replace(""", '"')
    text = text.replace(""", '"')
    text = text.replace("é", "e")
    text = text.replace("è", "e")
    text = text.replace("à", "a")
    text = text.replace("ê", "e")
    return text

def send_pdf_by_email(pdf_content, date, address):
    try:
        recipient_email = "skita@orpi.com"
        
        msg = MIMEMultipart()
        msg['From'] = st.secrets["email"]["sender"]
        msg['To'] = recipient_email
        
        address_clean = clean_text_for_pdf(address)
        msg['Subject'] = f"Rapport de visite - {address_clean} - {date}"
        
        body = f"""
        Bonjour,

        Veuillez trouver ci-joint le rapport de la visite effectuee le {date} a l'adresse : {address_clean}.

        Cordialement,
        Service Syndic ORPI
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
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

def create_pdf(data, main_image_file, observations, signature_image=None):
    class PDF(FPDF):
        def header(self):
            self.set_fill_color(227, 31, 43)
            self.rect(10, 10, 30, 15, 'F')
            self.set_text_color(255, 255, 255)
            self.set_font('Arial', 'B', 12)
            self.text(15, 20, 'ORPI')
            
            self.set_text_color(0, 0, 0)
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'RAPPORT DE VISITE', 0, 1, 'C')
            self.ln(10)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Informations principales
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(10, 40, 190, 50, 'F')
    pdf.set_font('Arial', 'B', 12)
    pdf.set_xy(15, 45)
    
    col_width = 90
    line_height = 8
    
    # Mise en page en colonnes
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, line_height, 'Date:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(65, line_height, f"{data['date']}", 0, 0)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(35, line_height, 'Rédacteur:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(55, line_height, f"{data['redacteur']}", 0, 1)
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, line_height, 'Adresse:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(65, line_height, f"{data['address']}", 0, 0)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(35, line_height, 'Horaires:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(55, line_height, f"{data['arrival_time']} - {data['departure_time']}", 0, 1)
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, line_height, 'Code:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(65, line_height, f"{data['building_code']}", 0, 1)
    
    # Image principale
    if main_image_file is not None:
        temp_image_path = "temp_main_image.jpg"
        try:
            with open(temp_image_path, "wb") as f:
                f.write(main_image_file.getvalue())
            img = Image.open(temp_image_path)
            img_w, img_h = img.size
            aspect = img_h / img_w
            width = 190
            height = width * aspect
            pdf.image(temp_image_path, x=10, y=100, w=width, h=height)
        finally:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
    
    # Observations
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(227, 31, 43)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, 'OBSERVATIONS', 1, 1, 'C', True)
    pdf.set_text_color(0, 0, 0)
    
    for idx, obs in enumerate(observations):
        pdf.ln(5)
        pdf.set_fill_color(245, 245, 245)
        
        pdf.set_font('Arial', 'B', 12)
        obs_type = "Positive" if "Positive" in obs['type'] else "Négative"
        icon = "✓" if obs_type == "Positive" else "✗"
        header_color = (0, 150, 0) if obs_type == "Positive" else (200, 0, 0)
        pdf.set_text_color(*header_color)
        pdf.cell(0, 10, f"{icon} Observation {idx + 1} - {obs_type}", 0, 1, 'L')
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 10)
        description_clean = clean_text_for_pdf(obs['description'])
        pdf.multi_cell(0, 7, description_clean)
        
        if obs['photo'] is not None:
            temp_obs_path = f"temp_obs_{idx}.jpg"
            try:
                with open(temp_obs_path, "wb") as f:
                    f.write(obs['photo'].getvalue())
                pdf.image(temp_obs_path, x=10, y=pdf.get_y() + 5, w=190)
                pdf.ln(60)
            finally:
                if os.path.exists(temp_obs_path):
                    os.remove(temp_obs_path)
        
        pdf.ln(5)
        pdf.cell(0, 0, '', 'B')

    # Page de signature
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "VALIDATION DU RAPPORT", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, data['redacteur'], 0, 1, 'C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, "Gestionnaire de copropriété", 0, 1, 'C')
    
    # Ajout de la signature
    if signature_image is not None:
        temp_sig_path = "temp_signature.png"
        try:
            with open(temp_sig_path, "wb") as f:
                f.write(signature_image)
            pdf.image(temp_sig_path, x=60, y=pdf.get_y() + 10, w=90)
        finally:
            if os.path.exists(temp_sig_path):
                os.remove(temp_sig_path)
    
    return pdf

# Titre
st.title("📋 Visite de Copropriété ORPI")
st.markdown("---")

# Création des colonnes
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Informations générales")
    
    date = st.date_input("Date de la visite", datetime.now())
    address = st.text_input("Adresse")
    redacteur = st.selectbox("Rédacteur", ["David SAINT-GERMAIN", "Elodie BONNAY"])
    arrival_time = st.time_input("Heure d'arrivée")
    departure_time = st.time_input("Heure de départ")
    building_code = st.text_input("Code Immeuble")
    
    main_image = st.file_uploader("Photo principale de la copropriété", type=['png', 'jpg', 'jpeg'])
    if main_image:
        st.image(main_image, caption="Photo principale", use_column_width=True)

    # Ajout du canvas de signature
    st.markdown("### ✍️ Signature")
    signature_canvas = st_canvas(
        stroke_width=2,
        stroke_color="black",
        background_color="#ffffff",
        height=150,
        width=300,
        drawing_mode="freedraw",
        key="signature",
    )
    
    if st.button("Effacer la signature"):
        st.session_state.signature = None
        st.experimental_rerun()

with col2:
    st.subheader("🔍 Observations")
    
    if 'observations' not in st.session_state:
        st.session_state.observations = []
    
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0
    
    with st.form(f"observation_form_{st.session_state.form_key}"):
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
                st.session_state.form_key += 1
                st.experimental_rerun()
            else:
                st.error("Veuillez ajouter une description à votre observation.")

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
                
                # Récupération de la signature
                signature_image = None
                if signature_canvas.image_data is not None:
                    signature_buffer = BytesIO()
                    signature_canvas.image_data.save(signature_buffer, format="PNG")
                    signature_image = signature_buffer.getvalue()
                
                try:
                    pdf = create_pdf(data, main_image, st.session_state.observations, signature_image)
                    pdf_output = pdf.output(dest='S').encode('latin1')
                    
                    if send_pdf_by_email(pdf_output, date.strftime('%Y-%m-%d'), address):
                        st.success("✅ PDF généré et envoyé par email avec succès!")
                    
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
