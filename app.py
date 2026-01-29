import os
import json
import re
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from io import BytesIO

# ReportLab imports
from reportlab.lib.pagesizes import letter, A4 # type: ignore
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

load_dotenv()
app = Flask(__name__)
CORS(app)

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# =====================================================
# 🔥 PROMPT ULTRA TECHNIQUE POUR GEMINI
# =====================================================
SYSTEM_PROMPT = """
Tu es un ingénieur du son professionnel et beatmaker.
Génère un BRIEF MUSICAL ULTRA COMPLET pour production audio et beatmaking.
Réponds UNIQUEMENT en JSON VALIDE (aucun markdown, aucun ```).
Format EXACT :
{
  "style": "",
  "bpm": "",
  "key": "",
  "ambiance": "",
  "structure": "",
  "instruments": "",
  "drums_patterns": "",
  "presets_plugins": "",
  "mix_tips": "",
  "mastering_tips": "",
  "effects": "",
  "automation_tips": "",
  "arrangement_guide": ""
}
Exigences :
- très technique
- inclure les presets exacts pour Serum, Kontakt, RC20, Valhalla, etc.
- tempo précis
- gamme musicale et accords
- patterns de batterie détaillés
- conseils mixage pro
- conseils mastering pro
- effets (reverb, delay, chorus, saturation)
- automation pour dynamique et mouvement
- guide d'arrangement avec positions des instruments
"""

# =====================================================
# 🔥 Nettoyage Gemini
# =====================================================
def clean_gemini(text):
    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return "{}"

# =====================================================
# 🎨 Génération PDF avec ReportLab
# =====================================================
def generate_pdf(data):
    """Génère un PDF professionnel à partir du brief musical"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          leftMargin=0.75*inch, rightMargin=0.75*inch,
                          topMargin=1*inch, bottomMargin=0.75*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style pour le titre principal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=colors.HexColor('#8b5cf6'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Style pour les sections
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#ec4899'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor=colors.HexColor('#8b5cf6'),
        borderPadding=5,
        backColor=colors.HexColor('#f9fafb')
    )
    
    # Style pour le contenu
    content_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        alignment=TA_LEFT,
        spaceAfter=8,
        textColor=colors.HexColor('#374151')
    )
    
    # Configuration des sections avec icônes
    section_config = {
        'style': {'icon': '🎨', 'title': 'Style Musical'},
        'bpm': {'icon': '⏱️', 'title': 'Tempo'},
        'key': {'icon': '🎹', 'title': 'Tonalité'},
        'ambiance': {'icon': '🌊', 'title': 'Ambiance'},
        'structure': {'icon': '🏗️', 'title': 'Structure'},
        'instruments': {'icon': '🎸', 'title': 'Instruments'},
        'drums_patterns': {'icon': '🥁', 'title': 'Patterns de Batterie'},
        'presets_plugins': {'icon': '🎛️', 'title': 'Presets & Plugins'},
        'mix_tips': {'icon': '🎚️', 'title': 'Conseils Mixage'},
        'mastering_tips': {'icon': '✨', 'title': 'Conseils Mastering'},
        'effects': {'icon': '🌀', 'title': 'Effets'},
        'automation_tips': {'icon': '🤖', 'title': 'Automation'},
        'arrangement_guide': {'icon': '📐', 'title': 'Arrangement'}
    }
    
    # Construction du document
    story = []
    
    # Titre principal avec emoji
    title = Paragraph("🎧 MUSIC BRIEF GENERATOR", title_style)
    story.append(title)
    story.append(Spacer(1, 0.3*inch))
    
    # Ligne de séparation
    story.append(Spacer(1, 0.1*inch))
    
    # Parcourir toutes les sections
    for key, value in data.items():
        if key in section_config:
            config = section_config[key]
            
            # Titre de section avec icône
            section_title = Paragraph(
                f"{config['icon']} {config['title']}", 
                section_style
            )
            story.append(section_title)
            story.append(Spacer(1, 0.1*inch))
            
            # Contenu
            if isinstance(value, dict):
                # Si c'est un objet, afficher clé-valeur
                for sub_key, sub_value in value.items():
                    formatted_key = sub_key.replace('_', ' ').title()
                    content = Paragraph(
                        f"<b>{formatted_key}:</b> {sub_value}",
                        content_style
                    )
                    story.append(content)
            elif isinstance(value, list):
                # Si c'est une liste
                for item in value:
                    content = Paragraph(f"• {item}", content_style)
                    story.append(content)
            else:
                # Texte simple - séparer par lignes
                lines = str(value).split('\n')
                for line in lines:
                    if line.strip():
                        # Détecter si c'est une liste avec tirets
                        if line.strip().startswith('-') or line.strip().startswith('•'):
                            clean_line = line.strip().lstrip('-•').strip()
                            content = Paragraph(f"• {clean_line}", content_style)
                        else:
                            content = Paragraph(line.strip(), content_style)
                        story.append(content)
            
            story.append(Spacer(1, 0.15*inch))
    
    # Footer
    story.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER
    )
    footer = Paragraph(
        "Généré par Music Brief Generator • Brief professionnel pour production musicale",
        footer_style
    )
    story.append(footer)
    
    # Construire le PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# =====================================================
# 🔹 Route test pour éviter 404
# =====================================================
@app.route("/")
def home():
    return "API running ✔️"

# =====================================================
# 🔥 Route principale / génération
# =====================================================
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    idea = data.get("idea", "")

    if not idea:
        return jsonify({"error": "Idea manquante"}), 400

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [
            {"parts": [{"text": SYSTEM_PROMPT}, {"text": f"Idée utilisateur : {idea}"}]}
        ]
    }

    try:
        r = requests.post(url, json=payload)
        if r.status_code == 403:
            return jsonify({"error": "403 Forbidden: Clé API invalide ou quota dépassé"}), 403
        elif r.status_code != 200:
            return jsonify({"error": f"Erreur API Gemini {r.status_code}: {r.text}"}), r.status_code

        raw_text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        clean_text = clean_gemini(raw_text)
        parsed = json.loads(clean_text)
        return jsonify(parsed)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# 📄 Route génération PDF
# =====================================================
@app.route("/generate-pdf", methods=["POST"])
def generate_pdf_route():
    data = request.json
    
    if not data:
        return jsonify({"error": "Aucune donnée fournie"}), 400
    
    try:
        # Générer le PDF
        pdf_buffer = generate_pdf(data)
        
        # Retourner le PDF
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='brief-musical.pdf'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    # =====================================================
# 🔥 Route pour tester la clé API
# =====================================================
@app.route("/test-api")
def test_api():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_KEY}"
    payload = {"contents":[{"parts":[{"text":"Test clé et quota"}]}]}
    try:
        r = requests.post(url, json=payload)
        return jsonify({
            "status_code": r.status_code,
            "response": r.text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# 🔹 RUN
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
