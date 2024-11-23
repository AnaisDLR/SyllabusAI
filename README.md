# TOC - Générateur de Syllabus Interactif 📚

## Description
TOC est une application web interactive développée avec Streamlit qui permet de générer automatiquement des syllabus académiques en utilisant l'IA (GPT-4). L'application offre la possibilité de créer des syllabus soit à partir d'un nom de cours, soit en analysant des documents existants (PDF/Excel).

## Fonctionnalités principales

### 🎯 Génération de syllabus
- Création de syllabus à partir du nom d'un cours
- Génération basée sur l'analyse de documents PDF ou Excel existants
- Support pour la génération multiple de syllabus
- Personnalisation du nombre de syllabus à générer

### 📄 Gestion des documents
- Support des formats PDF et Excel
- Extraction intelligente du contenu des documents
- Possibilité de combiner plusieurs documents pour un même syllabus
- Répartition manuelle des documents pour différents syllabus

### ✏️ Édition et personnalisation
- Modification interactive des syllabus générés
- Interface utilisateur intuitive pour les ajustements
- Mise à jour en temps réel des modifications

### 💾 Export et partage
- Export des syllabus au format PDF
- Mise en page professionnelle des documents générés
- Structure tabulaire claire et organisée

## Structure du syllabus
Chaque syllabus généré contient les sections suivantes :
- Intitulé du cours
- Durée du cours
- Objectifs du cours (compétences visées)
- Contenu détaillé (grands chapitres)
- Méthodes et moyens pédagogiques
- Modalités d'évaluation
- Bibliographie/Webographie
- Nom de l'enseignant

## Prérequis techniques
- Python 3.6+
- Streamlit
- OpenAI API (clé API requise)
- PyPDF2
- Pandas
- ReportLab
- Autres dépendances listées dans requirements.txt

## Installation

1. Clonez le répertoire :
```bash
git clone [URL-du-repo]
cd toc-syllabus-generator
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurez votre clé API OpenAI :
- Créez un fichier `.streamlit/secrets.toml`
- Ajoutez votre clé API :
```toml
GPT_KEY = "votre-clé-api-openai"
```

4. Lancez l'application :
```bash
streamlit run syllabus6.py
```

## Utilisation

1. Choisissez votre méthode de génération :
   - Saisissez le nom du cours pour une génération depuis zéro
   - Importez des documents existants pour une analyse basée sur le contenu

2. Pour l'import de documents :
   - Sélectionnez un ou plusieurs fichiers PDF/Excel
   - Choisissez le nombre de syllabus à générer
   - Répartissez manuellement les documents si nécessaire

3. Pour la modification :
   - Utilisez le champ de texte sous chaque syllabus
   - Décrivez les modifications souhaitées
   - Cliquez sur "Modifier" pour appliquer les changements

4. Pour l'export :
   - Utilisez le bouton "Télécharger en PDF" pour chaque syllabus
   - Les fichiers sont générés avec une mise en page professionnelle

## Sécurité
- L'application utilise des secrets Streamlit pour la gestion sécurisée des clés API
- Les documents uploadés sont traités localement
- Aucune donnée n'est stockée de manière permanente

## Contribution
Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## Licence
[Votre licence ici]

## Contact
[Vos informations de contact ici]

---
Développé avec ❤️ en utilisant Streamlit et OpenAI GPT-4
