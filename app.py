import os
import json
import re
import requests
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from dotenv import load_dotenv
from io import BytesIO
import time

# ReportLab imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
# 🎨 Génération PDF avec ReportLab - CORRIGÉ
# =====================================================
def generate_pdf(data):
    """Génère un PDF professionnel à partir du brief musical"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        leftMargin=0.75*inch, 
        rightMargin=0.75*inch,
        topMargin=1*inch, 
        bottomMargin=0.75*inch
    )
    
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
        'style': {'icon': 'Style Musical', 'title': 'Style Musical'},
        'bpm': {'icon': 'Tempo', 'title': 'Tempo'},
        'key': {'icon': 'Tonalite', 'title': 'Tonalité'},
        'ambiance': {'icon': 'Ambiance', 'title': 'Ambiance'},
        'structure': {'icon': 'Structure', 'title': 'Structure'},
        'instruments': {'icon': 'Instruments', 'title': 'Instruments'},
        'drums_patterns': {'icon': 'Patterns Batterie', 'title': 'Patterns de Batterie'},
        'presets_plugins': {'icon': 'Presets & Plugins', 'title': 'Presets & Plugins'},
        'mix_tips': {'icon': 'Mixage', 'title': 'Conseils Mixage'},
        'mastering_tips': {'icon': 'Mastering', 'title': 'Conseils Mastering'},
        'effects': {'icon': 'Effets', 'title': 'Effets'},
        'automation_tips': {'icon': 'Automation', 'title': 'Automation'},
        'arrangement_guide': {'icon': 'Arrangement', 'title': 'Arrangement'}
    }
    
    # Construction du document
    story = []
    
    # Titre principal
    title = Paragraph("MUSIC BRIEF GENERATOR", title_style)
    story.append(title)
    story.append(Spacer(1, 0.3*inch))
    
    # Parcourir toutes les sections
    for key, value in data.items():
        if key in section_config:
            config = section_config[key]
            
            # Titre de section
            section_title = Paragraph(
                f"<b>{config['title']}</b>", 
                section_style
            )
            story.append(section_title)
            story.append(Spacer(1, 0.1*inch))
            
            # Contenu - Convertir en string proprement
            content_text = ""
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    formatted_key = sub_key.replace('_', ' ').title()
                    content_text += f"<b>{formatted_key}:</b> {sub_value}<br/>"
            elif isinstance(value, list):
                for item in value:
                    content_text += f"• {item}<br/>"
            else:
                # Texte simple - nettoyer et formater
                lines = str(value).split('\n')
                for line in lines:
                    if line.strip():
                        clean_line = line.strip().lstrip('-•').strip()
                        if clean_line:
                            content_text += f"• {clean_line}<br/>"
            
            # Ajouter le paragraphe de contenu
            if content_text:
                content = Paragraph(content_text, content_style)
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
        "Genere par Music Brief Generator - Brief professionnel pour production musicale",
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
    return jsonify({
        "status": "API running ✔️",
        "endpoints": ["/generate", "/generate-stream", "/generate-pdf", "/test-api"]
    })

# =====================================================
# 🔥 Route STREAMING - NOUVEAU
# =====================================================
@app.route("/generate-stream", methods=["POST"])
def generate_stream():
    data = request.json
    idea = data.get("idea", "")

    if not idea:
        return jsonify({"error": "Idea manquante"}), 400

    def generate():
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:streamGenerateContent?key={GEMINI_KEY}&alt=sse"
        payload = {
            "contents": [
                {"parts": [{"text": SYSTEM_PROMPT}, {"text": f"Idée utilisateur : {idea}"}]}
            ]
        }

        try:
            with requests.post(url, json=payload, stream=True) as r:
                if r.status_code == 403:
                    yield f"data: {json.dumps({'error': '403 Forbidden: Clé API invalide ou quota dépassé'})}\n\n"
                    return
                elif r.status_code != 200:
                    yield f"data: {json.dumps({'error': f'Erreur API Gemini {r.status_code}'})}\n\n"
                    return

                accumulated_text = ""
                for line in r.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            chunk_data = line_str[6:]  # Remove 'data: '
                            try:
                                chunk_json = json.loads(chunk_data)
                                if 'candidates' in chunk_json and len(chunk_json['candidates']) > 0:
                                    candidate = chunk_json['candidates'][0]
                                    if 'content' in candidate and 'parts' in candidate['content']:
                                        for part in candidate['content']['parts']:
                                            if 'text' in part:
                                                accumulated_text += part['text']
                                                # Envoyer le chunk au frontend
                                                yield f"data: {json.dumps({'chunk': part['text'], 'accumulated': accumulated_text})}\n\n"
                            except json.JSONDecodeError:
                                continue
                
                # À la fin, nettoyer et envoyer le JSON final
                clean_text = clean_gemini(accumulated_text)
                try:
                    parsed = json.loads(clean_text)
                    yield f"data: {json.dumps({'done': True, 'result': parsed})}\n\n"
                except:
                    yield f"data: {json.dumps({'error': 'Impossible de parser le JSON final'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

# =====================================================
# 🔥 Route principale / génération (ancienne, gardée pour compatibilité)
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
# 📄 Route génération PDF - CORRIGÉE
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
        print(f"Erreur PDF: {str(e)}")  # Pour debug
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)