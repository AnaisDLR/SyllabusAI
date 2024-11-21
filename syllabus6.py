import streamlit as st
from openai import OpenAI
import PyPDF2
import pandas as pd 
import concurrent.futures 
import os
import streamlit_extras

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
import io
from io import BytesIO
from streamlit_extras.altex import scatter_chart
from streamlit_extras.altex import _chart
from streamlit_extras.customize_running import center_running
from pyngrok import ngrok


#API_KEY = os.environ.get("OPENAI_API_KEY")

#from itertools import combinations
# Access the API key from st.secrets
API_KEY = st.secrets["GPT_KEY"] == "your GPT key"

# Fonction pour initialiser le client OpenAI avec la clé API
def initialize_openai_client():
    return OpenAI(api_key=API_KEY)

# Initialisation du client avec la clé API incluse
client = initialize_openai_client()


st.set_page_config(page_title="TOC", page_icon="📚", layout="wide")

st.markdown(
    """
    <style>   
@import url('https://fonts.googleapis.com/css2?family=Faculty+Glyphic&family=Hanuman:wght@100;300;400;700;900&family=League+Spartan:wght@100..900&family=Orienta&display=swap');    
        .faculty-glyphic-regular {
             font-family: "League Spartan", sans-serif;
             font-optical-sizing: auto;
              font-weight: <weight>;
              font-style: normal;
              font-size : 25px;
        }
        
        .faculty-glyphic-regular2 {
             font-family: "League Spartan", serif;
             font-optical-sizing: auto;
              font-weight: 320;
              font-style: oblique;
              font-size : 26px;
              
        }

        body {
            font-family: "Orienta", serif;
            font-optical-sizing: auto;
              font-weight: 400;
              font-style: normal;
        }

    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)

def scroll_to_top():
    js = """
    <script>
    var body = window.parent.document.querySelector(".main");
    body.scrollTop = 0;
    </script>
    """
    st.components.v1.html(js, height=0)

# Fonction pour afficher le logo et le titre
def display_logo_and_title():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("logoVertSansFond.png", width=220)
    with col2:
        st.title("TOC")

# Fonction pour extraire le texte d'un seul PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        pages = list(pdf_reader.pages)
        text_chunks = list(executor.map(lambda page: page.extract_text(), pages))
    return "\n\n".join(filter(None, text_chunks))  # Ignore les pages vides



def extract_text_from_excel(excel_file):
    xls = pd.ExcelFile(excel_file)
    text = ""
    # Extraire le contenu de chaque feuille dans le fichier Excel
    for sheet_name in xls.sheet_names:
        sheet_df = pd.read_excel(xls, sheet_name)
        # Convertir les données de la feuille en texte brut
        text += sheet_df.to_string(index=False) + "\n\n"
    return text


# Fonction pour extraire le texte de plusieurs fichiers PDF ou Excel
def extract_text_from_files(files):
    texts = {}
    for file in files:
        if file.name.endswith('.pdf'):
            texts[file.name] = extract_text_from_pdf(file)
        elif file.name.endswith('.xlsx'):
            texts[file.name] = extract_text_from_excel(file)
    return texts


# Fonction pour diviser le texte en chunks (permet plus grand pdf)
def chunk_text(text, chunk_size=1500):
    words = text.split()
    chunks,current_chunk = [],[]
    
    current_size = 0
    
    for word in words:
        if current_size + len(word) + 1 > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
        else:
            current_chunk.append(word)
            current_size += len(word) + 1
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Fonction pour générer un résumé à partir des chunks
def generate_summary_from_chunks(chunks, client):
    summaries = []
    summary_container = st.empty()  # Crée un conteneur pour affichage en temps réel

    for i, chunk in enumerate(chunks):
        prompt = f"Résumez le contenu suivant de manière concise :\n\n{chunk}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un assistant capable de résumer du contenu de manière concise et complète."},
                {"role": "user", "content": prompt}
            ]
        )
        chunk_summary = response.choices[0].message.content
        summaries.append(chunk_summary)

    return " ".join(summaries)

# Function to display PDF group selection with safe handling of session state
def display_pdf_group_selection(uploaded_files, num_syllabus):
    st.write("### Répartition des PDFs par syllabus")
    
    # Initialize the groups in session state safely
    if 'pdf_groups' not in st.session_state or len(st.session_state.pdf_groups) != num_syllabus:
        st.session_state.pdf_groups = {i: [] for i in range(num_syllabus)}
    
    # Display each PDF and allow manual assignment to groups
    for file in uploaded_files:
        st.write("---")
        st.write(f"📄 **{file.name}**")
        
        # Create columns for each syllabus
        cols = st.columns(num_syllabus)
        
        # Checkbox for each syllabus option
        for i, col in enumerate(cols):
            with col:
                checkbox_key = f"checkbox_{file.name}_{i}"
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = False
                
                if st.checkbox(f"Syllabus {i+1}", key=checkbox_key):
                    if file.name not in st.session_state.pdf_groups[i]:
                        st.session_state.pdf_groups[i].append(file.name)
                else:
                    if file.name in st.session_state.pdf_groups[i]:
                        st.session_state.pdf_groups[i].remove(file.name)
    
    # Display a summary of the syllabus groups
    st.write("---")
    st.write("### Résumé des Syllabus")
    
    for i in range(num_syllabus):
        with st.expander(f"📚 Syllabus {i+1}"):
            if i in st.session_state.pdf_groups and st.session_state.pdf_groups[i]:
                for pdf in st.session_state.pdf_groups[i]:
                    st.write(f"- {pdf}")
            else:
                st.write("*Aucun PDF sélectionné*")



# Fonction pour générer un syllabus à partir d'un ou plusieurs PDFs
def generate_syllabus_from_pdfs(pdf_contents, client):
    if isinstance(pdf_contents, str):
        chunks = chunk_text(pdf_contents)
    else:
        combined_text = "\n\n".join(pdf_contents.values())
        chunks = chunk_text(combined_text)
    
    summary = generate_summary_from_chunks(chunks, client)
    #prompt du prof en fançais
    prompt = f"""En tant qu'expert en création de syllabus académiques, votre tâche est de développer un syllabus complet et détaillé basé sur le résumé des contenus PDF fournis. Voici le résumé :

            {summary}

            Veuillez créer un syllabus structuré en utilisant les informations pertinentes du résumé. Utilisez le format de tableau suivant :

            | Catégorie | Détail |
            | Intitulé du cours | |
            | Durée du cours | |
            | Objectif du cours (compétences visées) | |
            | Contenu détaillé du cours (grands chapitres) | |
            | Méthodes et/ou moyens pédagogiques | |
            | Modalités d'évaluation | |
            | Bibliographie/Webographie | |
            | Nom de l'enseignant | |

            Remplissez chaque catégorie avec les informations appropriées extraites du résumé en synthétisant les informations provenant de tous les documents fournis."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Tu es un expert en création de syllabus académiques avec une vaste expérience dans divers domaines d'études."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def generate_pdf_with_table(syllabus):
    # Créer un buffer pour le PDF
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    
    # Style pour le texte dans les cellules
    cell_style = ParagraphStyle(
        name="CellStyle",
        fontSize=10,
        alignment=1,  # Centré
        leading=12,
        spaceAfter=6
    )

    # Transformer chaque ligne du syllabus en liste [Catégorie, Détail]
    syllabus_lines = syllabus.splitlines()
    data = []  # Ajout des en-têtes
    
    # Vérifiez si "Catégorie | Détail" est déjà présent dans le texte
    if not any("Catégorie" in line and "Détail" in line for line in syllabus_lines):
        data.append(["Catégorie", "Détail"])  # Ajout des en-têtes si absent

    for line in syllabus_lines:
        # Suppression des `|` et division en deux colonnes
        line = line.strip('|')  # Retirer les `|` en début et fin de ligne
        parts = line.split('|')
        
        # Vérifie si la ligne est bien divisée en deux colonnes
        if len(parts) == 2:
            # Remplace les <br> par des nouvelles lignes pour le texte dans les cellules
            category = Paragraph(parts[0].strip(), cell_style)
            detail_text = parts[1].strip().replace("<br>", "\n")  # Remplacement des <br> par des \n
            detail = Paragraph(detail_text, cell_style)
            data.append([category, detail])

        elif len(parts) == 1:
            # Si la ligne ne comporte qu'une partie, l'ajouter dans la colonne Détail uniquement
            detail_text = parts[0].replace("<br>", "\n")  # Remplacement des <br> par des \n
            data.append(["", Paragraph(detail_text, cell_style)])
        else:
            # Si la ligne ne comporte pas deux parties, on la met dans la colonne Détail uniquement
            detail_text = line.strip().replace("<br>", "\n")  # Remplacement des <br> par des \n
            data.append(["", Paragraph(detail_text, cell_style)])

    # Création du tableau
    table = Table(data, colWidths=[100, 400])  # Largeur des colonnes ajustées pour "Catégorie" et "Détail"
    
    # Appliquer le style de tableau
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),            # En-tête de tableau en gris
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),       # Texte de l'en-tête en blanc
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),                   # Centrer le texte
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),             # Police de base
        ('FONTSIZE', (0, 0), (-1, -1), 10),                      # Taille de la police
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),                  # Marge en bas des cellules
        ('TOPPADDING', (0, 0), (-1, -1), 8),                     # Marge en haut des cellules
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),           # Grille de bordure
        ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),       # Fond gris clair pour la colonne "Catégorie"
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),                  # Alignement vertical au milieu
    ]))

    # Générer le PDF
    elements = [table]
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer



# Afficher le syllabus et ajouter un bouton de téléchargement si le syllabus est généré
def display_syllabus_with_download_option(syllabus_content):
    st.markdown("### Syllabus généré")
    st.write(syllabus_content)  # Afficher le syllabus généré
    
    # Générer un bouton de téléchargement du PDF
    pdf_buffer = generate_pdf_with_table(syllabus_content)
    st.download_button(
        label="Télécharger le syllabus en PDF",
        data=pdf_buffer,
        file_name="syllabus.pdf",
        mime="application/pdf"
    )

# Fonction pour générer ou modifier le syllabus
def generate_or_modify_syllabus(course_name, current_syllabus=None, modification=None):
    if not client:
        st.error("Erreur : Le client OpenAI n'a pas pu être initialisé.")
        return None
    
    if current_syllabus and modification:
        prompt = f"""En tant qu'expert en création de syllabus académiques, ta tâche est de modifier le syllabus existant pour le cours "{course_name}" selon la demande suivante : {modification}

            Syllabus actuel :
            {current_syllabus}

            Apporte les modifications demandées sans ajouter d’introduction comme 'Syllabus révisé' et conserve le format du tableau pour chaque catégorie."""  
    else:
        prompt = f"""En tant qu'expert en création de syllabus académiques, ta tâche est de développer un syllabus complet et détaillé pour le cours intitulé "{course_name}".

                ### Instructions
                - Utilise tes connaissances approfondies en pédagogie et en conception de programmes d'études pour créer un syllabus exhaustif.
                - Assure-toi que chaque section du syllabus soit remplie de manière détaillée et pertinente pour le cours spécifié.
                - Le contenu doit être informatif, bien structuré et adapté au niveau d'études approprié.
                - Utilise un langage clair et professionnel tout au long du document.

                ### Format du syllabus
                Remplis le tableau suivant avec les informations appropriées pour le cours "{course_name}" :

                | Catégorie | Détail |
                | Intitulé du cours | {course_name} |
                | Durée du cours | |
                | Objectif du cours (compétences visées) | |
                | Contenu détaillé du cours (grands chapitres) | |
                | Méthodes et/ou moyens pédagogiques | |
                | Modalités d'évaluation | |
                | Bibliographie/Webographie | |
                | Nom de l'enseignant | |

                Remplissez chaque catégorie sans ajouter de texte superflu ou de phrases introductives."""  

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Tu es un expert en création de syllabus académiques avec une vaste expérience dans divers domaines d'études."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


# Affichage du logo et du titre
display_logo_and_title()
st.markdown('<p class="faculty-glyphic-regular2">Générateur de Syllabus Interactif :</p>', unsafe_allow_html=True)

# Interface principale

# Initialisation des états de session
if "syllabus_generated" not in st.session_state:
    st.session_state.syllabus_generated = False
    st.session_state.syllabus_content = None
    st.session_state.syllabi = {}
    st.session_state.pdf_groups = {}



syllabus_display = st.empty()  # Placeholder vide en attente des syllabus

#Réinitialisation de la session
def reset_session_state():
    st.session_state.syllabus_generated = False
    st.session_state.syllabus_content = None
    st.session_state.syllabi = {}
    st.session_state.pdf_groups = {}
    if 'uploaded_files' in st.session_state:
        del st.session_state.uploaded_files

#Sinon...
if not st.session_state.syllabus_generated:
    st.markdown('<p class="faculty-glyphic-regular">Choisissez une option pour générer le Syllabus :</p>', unsafe_allow_html=True)
    # Utilisation de l'argument 'label_visibility' pour masquer le label par défaut
    option = st.radio("", ("Entrez le nom du cours", "Chargez des fichiers PDF ou Excel"),label_visibility="collapsed")
    if option == "Entrez le nom du cours":
        st.markdown('<p class="faculty-glyphic-regular">Entrez le nom du cours pour générer un Syllabus :</p>', unsafe_allow_html=True)
        course_name = st.text_input("", label_visibility="collapsed")
        if st.button("Générer le Syllabus"):
            if not API_KEY:
                st.error("Veuillez entrer votre clé API OpenAI dans la barre latérale.")
            elif not course_name:
                st.error("Veuillez entrer le nom du cours.")
            else:
                with st.spinner("Génération du Syllabus en cours..."):
                    syllabus = generate_or_modify_syllabus(course_name)
                    st.session_state.syllabi = {"Syllabus principal": syllabus}
                    st.session_state.syllabus_generated = True
                    st.session_state.course_name = course_name
                    st.rerun()
    else:
        st.markdown('<p class="faculty-glyphic-regular">Choisissez vos fichiers PDF ou Excel:</p>',unsafe_allow_html=True)
        uploaded_files = st.file_uploader("", type=["pdf","xlsx"], accept_multiple_files=True, label_visibility="collapsed")
        
        # Réinitialiser l'état si de nouveaux fichiers sont chargés
        if 'uploaded_files' not in st.session_state or st.session_state.uploaded_files != uploaded_files:
            reset_session_state()
            st.session_state.uploaded_files = uploaded_files
        
        if uploaded_files:
            st.write(f"Nombre de fichiers sélectionnés : {len(uploaded_files)}")
            file_names = [file.name for file in uploaded_files]
            st.write("Fichiers sélectionnés :", ", ".join(file_names))
            
            # Menu déroulant pour choisir le nombre de syllabus à générer
            max_syllabus = len(uploaded_files)
            num_syllabus = st.selectbox(
                "Combien de Syllabus souhaitez-vous générer ?",
                range(1, max_syllabus + 1),
                index=max_syllabus - 1,
                help="Sélectionnez le nombre de Syllabus à générer. Chaque Syllabus peut combiner un ou plusieurs PDFs."
            )

            # Option pour choisir comment grouper les PDFs (uniquement "Sélection manuelle")
            if num_syllabus>1 and num_syllabus < max_syllabus:
                display_pdf_group_selection(uploaded_files, num_syllabus)
            
            if st.button("Générer les Syllabus"):
                if not API_KEY:
                    st.error("Veuillez entrer votre clé API OpenAI dans la barre latérale.")
                else:
                    client = OpenAI(api_key=API_KEY)
                    with st.spinner(f"Génération de {num_syllabus} Syllabus en cours..."):
                        pdf_contents = extract_text_from_files(uploaded_files)
                        
                        if num_syllabus == 1:
                            # Générer un seul syllabus à partir de tous les PDFs
                            syllabus = generate_syllabus_from_pdfs(pdf_contents, client)
                            st.session_state.syllabi = {"Syllabus": syllabus}
                        
                        elif num_syllabus == max_syllabus:
                            # Générer un syllabus par PDF
                            st.session_state.syllabi = {}
                            for file_name, content in pdf_contents.items():
                                syllabus = generate_syllabus_from_pdfs({file_name: content}, client)
                                st.session_state.syllabi[f"Syllabus - {file_name}"] = syllabus
                        else:
                            # Sélection manuelle uniquement
                            st.session_state.syllabi = {}
                            
                            # Générer un syllabus pour chaque groupe
                            for i in range(num_syllabus):
                                group_files = st.session_state.pdf_groups[i]
                                if group_files:  # Ne générer que si le groupe contient des fichiers
                                    group_content = {name: pdf_contents[name] for name in group_files if name in pdf_contents}
                                    syllabus = generate_syllabus_from_pdfs(group_content, client)
                                    st.session_state.syllabi[f"Syllabus groupe {i+1}"] = syllabus
                        
                        st.session_state.syllabus_generated = True
                        st.rerun()

# Affichage des syllabus générés et options de modification
if st.session_state.syllabus_generated:
    for title, syllabus in st.session_state.syllabi.items():
        st.subheader(title)
        st.markdown(syllabus)
        
        modification = st.text_area(f"Entrez les modifications pour {title}:", 
                                    key=f"modification_{title}",
                                    placeholder="Ex: Je veux que la durée du cours soit un trimestre au lieu d'un semestre.")
        
        if st.button(f"Modifier {title}", key=f"modify_{title}"):
            if modification:
                with st.spinner(f"Modification de {title} en cours..."):
                    st.session_state.syllabi[title] = generate_or_modify_syllabus(
                        title,
                        syllabus,
                        modification
                    )
                    st.rerun()
            else:
                st.warning("Veuillez entrer une modification à apporter au Syllabus.")
        
        # Bouton de téléchargement du syllabus en PDF
        pdf_buffer = generate_pdf_with_table(syllabus)
        st.download_button(label=f"Télécharger {title} en PDF",
                           data=pdf_buffer,
                           file_name=f"{title}.pdf",
                           mime="application/pdf")
    
    # Option pour générer d'autres syllabus
    if st.button("Générer d'autres Syllabus"):
        reset_session_state()
        st.rerun()
