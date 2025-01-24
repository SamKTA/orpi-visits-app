import numpy as np
from PIL import Image as PILImage
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

def fix_image_rotation(image_data):
    # Convertir les bytes en image PIL
    img = Image.open(BytesIO(image_data))
    
    try:
        # Obtenir l'orientation EXIF
        exif = img._getexif()
        if exif is not None:
            orientation = exif.get(274)  # 274 est le tag pour l'orientation
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    except:
        # Si pas d'information EXIF, on force la rotation selon les dimensions
        if img.width < img.height:
            img = img.rotate(270, expand=True)
    
    # Sauvegarder l'image corrigée
    output_buffer = BytesIO()
    img.save(output_buffer, format='JPEG')
    return output_buffer.getvalue()

# Configuration de la page
st.set_page_config(page_title="Visite de Copropriété ORPI", layout="wide")

def clean_text_for_pdf(text):
    text = str(text)
    text = text.replace("✅", "+")  
    text = text.replace("❌", "-")  
    text = text.replace("'", "'")
    text = text.replace(""", '"')
    text = text.replace(""", '"')
    text = text.replace("é", "e")
    text = text.replace("è", "e")
    text = text.replace("à", "a")
    text = text.replace("ê", "e")
    text = text.replace("✓", "+")
    text = text.replace("✗", "-")
    return text

def send_pdf_by_email(pdf_content, date, address):
    try:
        if redacteur == "David SAINT-GERMAIN":
            recipient_email = "dsaintgermain@orpi.com"
        elif redacteur == "Elodie BONNAY":
            recipient_email = "ebonnay@orpi.com"
        else:  # Samuel KITA test
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
            self.rect(10, 10, 40, 15, 'F')  # Width changée de 30 à 40
            self.set_text_color(255, 255, 255)
            self.set_font('Arial', 'B', 12)
            self.text(12, 20, 'ORPI Adimmo')  # Position X ajustée de 15 à 12
            
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
    pdf.rect(10, 40, 190, 60, 'F')  # Hauteur augmentée à 60
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
    pdf.cell(65, line_height, f"{data['address']}", 0, 1)
    
    # Heure d'arrivée
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(35, line_height, "Heure d'arrivée:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(65, line_height, f"{data['arrival_time']}", 0, 1)
    
    # Heure de départ
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(35, line_height, "Heure de départ:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(65, line_height, f"{data['departure_time']}", 0, 1)
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, line_height, 'Code:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(65, line_height, f"{data['building_code']}", 0, 1)
    
    # Image principale
    if main_image_file is not None:
        temp_image_path = "temp_main_image.jpg"
        try:
            # Corriger la rotation
            corrected_image = fix_image_rotation(main_image_file.getvalue())
            with open(temp_image_path, "wb") as f:
                f.write(corrected_image)
            img = Image.open(temp_image_path)
            img_w, img_h = img.size
            aspect = img_h / img_w
            width = 190
            height = width * aspect
            pdf.image(temp_image_path, x=10, y=110, w=width, h=height)  # Y ajusté à 110 pour tenir compte du cadre plus grand
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
        # Espacement entre les observations
        pdf.ln(20)  # Augmentation de l'espacement entre les observations
        
        # Cadre gris clair pour chaque observation
        pdf.set_fill_color(245, 245, 245)
        start_y = pdf.get_y()
        pdf.rect(10, start_y, 190, 10, 'F')
        
        # En-tête de l'observation
        pdf.set_font('Arial', 'B', 12)
        obs_type_clean = clean_text_for_pdf(obs['type'])
        obs_type = "Positive" if "Positive" in obs_type_clean else "Negative"
        if obs_type == "Positive":
            header_color = (0, 150, 0)  # Vert pour positif
        else:
            header_color = (200, 0, 0)  # Rouge pour négatif
        
        pdf.set_text_color(*header_color)
        pdf.set_xy(15, start_y + 2)
        pdf.cell(0, 8, f"Observation {idx + 1} - {obs_type}", 0, 1, 'L')
        
        # Titre "Description :"
        pdf.ln(8)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, "Description :", 0, 1, 'L')
        
        # Contenu de la description
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 10)
        description_clean = clean_text_for_pdf(obs['description'])
        pdf.multi_cell(0, 7, description_clean)
        
        # Espacement avant l'image
        pdf.ln(8)
        
        # Photo de l'observation avec titre
        if obs['photo'] is not None:
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, "Photo :", 0, 1, 'L')
            pdf.ln(2)
            
            temp_obs_path = f"temp_obs_{idx}.jpg"
            try:
                # Corriger la rotation
                corrected_image = fix_image_rotation(obs['photo'].getvalue())
                with open(temp_obs_path, "wb") as f:
                    f.write(corrected_image)
                current_y = pdf.get_y()
                if current_y > 200:  # Si on est trop bas dans la page
                    pdf.add_page()
                    current_y = pdf.get_y()
                pdf.image(temp_obs_path, x=10, y=current_y, w=190)
                # Déplacer le curseur après l'image
                pdf.set_y(current_y + 190)  # Espace après l'image
                pdf.ln(20)  # Espace supplémentaire
            finally:
                if os.path.exists(temp_obs_path):
                    os.remove(temp_obs_path)

        # Nouvelle page si nécessaire
        if pdf.get_y() > 250:
            pdf.add_page()

    # Page de signature
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "VALIDATION DU RAPPORT", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, data['redacteur'], 0, 1, 'C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, "Gestionnaire de copropriété", 0, 1, 'C')
    
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
    redacteur = st.selectbox("Rédacteur", ["David SAINT-GERMAIN", "Elodie BONNAY", "Samuel KITA test"])
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
            if signature_canvas.image_data is None:
                st.error("Veuillez signer le document avant de générer le PDF")
            else:
                with st.spinner("Génération et envoi du rapport en cours..."):
                    data = {
                        "date": date,
                        "address": address,
                        "redacteur": redacteur,
                        "arrival_time": arrival_time,
                        "departure_time": departure_time,
                        "building_code": building_code
                    }
                    
                    # Conversion de la signature en image
                    try:
                        # Convertir le numpy array en image PIL
                        signature_array = signature_canvas.image_data.astype(np.uint8)
                        signature_image = PILImage.fromarray(signature_array)
                        
                        # Sauvegarder l'image en bytes
                        signature_buffer = BytesIO()
                        signature_image.save(signature_buffer, format="PNG")
                        signature_bytes = signature_buffer.getvalue()
                        
                        pdf = create_pdf(data, main_image, st.session_state.observations, signature_bytes)
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
    else:
        st.warning("Veuillez remplir au moins l'adresse et le code immeuble.")
