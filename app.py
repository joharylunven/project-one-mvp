import streamlit as st
import requests
import json
import google.generativeai as genai
import base64
from PIL import Image
from io import BytesIO
import time

# --- 1. CONFIGURATION & SECRETS ---
# On récupère les clés depuis st.secrets (pour déploiement local ou cloud)
SCRAPINGBEE_API_KEY = st.secrets.get("SCRAPINGBEE_API_KEY", "")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")

# Configuration globale de Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. CSS & UI DESIGN (Theme: Quiet Luxury) ---
def apply_custom_style():
    st.markdown("""
    <style>
        /* Importation des polices */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Cinzel:wght@400;700&display=swap');

        /* Variables globales */
        :root {
            --bg-color: #0a0a0a;
            --card-bg: #121212;
            --text-color: #e0e0e0;
            --accent-color: #D4AF37; /* Or vieilli */
            --subtle-border: #333333;
        }

        /* Application générale */
        .stApp {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Inter', sans-serif;
        }

        /* Titres */
        h1, h2, h3 {
            font-family: 'Cinzel', serif;
            font-weight: 400;
            letter-spacing: 1px;
            color: #ffffff !important;
        }

        /* Input Field Centré (Phase 1) */
        .stTextInput > div > div > input {
            background-color: var(--card-bg);
            color: white;
            border: 1px solid var(--subtle-border);
            text-align: center;
            font-size: 1.2rem;
            padding: 15px;
            border-radius: 8px;
        }
        .stTextInput > div > div > input:focus {
            border-color: var(--accent-color);
            box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);
        }

        /* Boutons */
        div.stButton > button {
            background-color: var(--accent-color);
            color: #000;
            border: none;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            padding: 12px 24px;
            border-radius: 4px;
            transition: all 0.3s ease;
            width: 100%;
        }
        div.stButton > button:hover {
            background-color: #f1c40f;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
        }

        /* Cards (Campagnes) */
        .campaign-card {
            background-color: var(--card-bg);
            border: 1px solid var(--subtle-border);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            transition: transform 0.2s;
        }
        .campaign-card:hover {
            border-color: #555;
        }

        /* Tags ADN */
        .dna-tag {
            display: inline-block;
            padding: 5px 12px;
            margin: 4px;
            background: rgba(255,255,255,0.05);
            border: 1px solid #333;
            border-radius: 20px;
            font-size: 0.8rem;
            color: #aaa;
        }
        
        /* Utilitaires */
        .centered-text { text-align: center; }
        .muted { color: #888; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BACKEND FUNCTIONS ---

def get_scrapingbee_dna(url):
    """Extrait l'ADN de marque via ScrapingBee."""
    endpoint = "https://app.scrapingbee.com/api/v1/"
    
    # Règles d'extraction strictes
    extract_rules = {
        "projectName": "Brand Name",
        "tagline": "Tagline or Slogan",
        "industry": "Industry Sector",
        "concept": "Short Concept Summary (max 20 words)",
        "colors": {
            "description": "Main hex colors",
            "type": "list",
            "output": { "hex_code": "#Hex" }
        },
        "aesthetic": {
            "description": "Visual aesthetic keywords (e.g., Minimalist, Grunge, Luxury)",
            "type": "list",
            "output": { "keyword": "Adjective" }
        },
        "values": {
            "description": "Core values",
            "type": "list",
            "output": { "value": "Value" }
        }
    }

    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': url,
        'render_js': 'true',
        'premium_proxy': 'true', # Important pour éviter les blocages
        'ai_extract_rules': json.dumps(extract_rules)
    }

    try:
        response = requests.get(endpoint, params=params, timeout=60)
        if response.status_code == 200:
            # Parfois ScrapingBee renvoie une string qu'il faut parser
            data = response.json()
            # Nettoyage basique si nécessaire
            return data
        else:
            st.error(f"Erreur ScrapingBee ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Erreur connexion ScrapingBee: {e}")
        return None

def generate_strategy_gemini(dna_json):
    """Génère 3 concepts de campagne basés sur l'ADN."""
    
    # Modèle optimisé pour le JSON (1.5 Flash est très rapide et fiable pour ça)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are a luxury Brand Strategist. Based on this Brand DNA, create 3 distinct social media campaign concepts.
    
    Brand DNA: {json.dumps(dna_json)}
    
    Output Requirements:
    Return a JSON object with a key "campaigns" containing a list of 3 objects.
    Each object must have:
    1. "id": (int) 1, 2, or 3
    2. "title": (string) Catchy campaign title
    3. "strategy": (string) A 2-sentence strategic justification.
    4. "visual_prompt": (string) A highly detailed, photorealistic image generation prompt for this campaign. Include lighting, texture, and composition details. Do not use markdown.
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)["campaigns"]
    except Exception as e:
        st.error(f"Erreur Gemini Strategy: {e}")
        return []

def generate_image_imagen(prompt):
    """Génère une image via l'API REST Google Imagen."""
    # Endpoint REST pour Imagen (fonctionne souvent mieux avec les clés API standard que le SDK Python actuel)
    # On utilise une version stable ou "preview" récente.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={GOOGLE_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [{ "prompt": prompt }],
        "parameters": {
            "aspectRatio": "4:5", # Format Instagram
            "sampleCount": 1
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            # Structure de réponse: { "predictions": [ { "bytesBase64Encoded": "..." } ] }
            predictions = result.get('predictions', [])
            if predictions:
                b64_data = predictions[0].get('bytesBase64Encoded')
                if b64_data:
                    image_data = base64.b64decode(b64_data)
                    return Image.open(BytesIO(image_data))
        
        # Fallback silencieux (retourne None) pour gestion d'erreur UI
        print(f"Imagen Error: {response.text}")
        return None
    except Exception as e:
        print(f"Imagen Exception: {e}")
        return None

# --- 4. STATE MANAGEMENT ---
# Initialisation des variables de session
if 'step' not in st.session_state: st.session_state.step = 1
if 'url' not in st.session_state: st.session_state.url = ""
if 'dna' not in st.session_state: st.session_state.dna = None
if 'campaigns' not in st.session_state: st.session_state.campaigns = []
if 'images' not in st.session_state: st.session_state.images = {} # Dict {id: image_obj}

# --- 5. MAIN APPLICATION FLOW ---

st.set_page_config(page_title="Project One", layout="wide", page_icon="⚡")
apply_custom_style()

# Header discret
st.markdown("<div style='margin-bottom: 40px; opacity: 0.5;'>PROJECT ONE <span style='font-size:0.8em'>| MVP v1.0</span></div>", unsafe_allow_html=True)

# --- PHASE 1: INPUT ---
if st.session_state.step == 1:
    # Centrage vertical via colonnes vides
    st.write("")
    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 class='centered-text'>Brand Intelligence</h1>", unsafe_allow_html=True)
        st.markdown("<p class='centered-text muted'>Enter the URL to extract DNA & Generate Strategy</p>", unsafe_allow_html=True)
        
        url_input = st.text_input("Brand URL", placeholder="https://www.example.com", label_visibility="collapsed")
        
        if st.button("INITIALIZE EXTRACTION"):
            if url_input:
                if not url_input.startswith("http"):
                    url_input = "https://" + url_input
                st.session_state.url = url_input
                st.session_state.step = 1.5
                st.rerun()
            else:
                st.warning("Please enter a valid URL.")

# --- PHASE 1.5: PROCESSING (Transition) ---
elif st.session_state.step == 1.5:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 class='centered-text'>Extracting Digital DNA...</h2>", unsafe_allow_html=True)
        progress = st.progress(0)
        
        with st.spinner("Scraping website structure & aesthetics..."):
            dna_result = get_scrapingbee_dna(st.session_state.url)
            progress.progress(100)
            
            if dna_result:
                st.session_state.dna = dna_result
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("Extraction failed. Please check the URL or API quota.")
                if st.button("Back"):
                    st.session_state.step = 1
                    st.rerun()

# --- PHASE 2: DASHBOARD & VALIDATION ---
elif st.session_state.step == 2:
    dna = st.session_state.dna
    
    # Header Dashboard
    st.markdown(f"<h1>DNA: {dna.get('projectName', 'Unknown Brand')}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("Core Identity")
        st.markdown(f"**Industry:** {dna.get('industry', 'N/A')}")
        st.markdown(f"**Concept:** *{dna.get('concept', 'N/A')}*")
        
        st.subheader("Values")
        values = dna.get('values', [])
        if values:
            for v in values:
                val = v.get('value') if isinstance(v, dict) else v
                st.markdown(f"<span class='dna-tag'>{val}</span>", unsafe_allow_html=True)
    
    with c2:
        st.subheader("Aesthetic & Colors")
        
        # Colors
        colors = dna.get('colors', [])
        cols_ui = st.columns(6)
        for idx, c in enumerate(colors[:6]):
            hex_code = c.get('hex_code', '#333')
            cols_ui[idx].markdown(f"<div style='background-color:{hex_code}; width:40px; height:40px; border-radius:50%; border:1px solid #555;' title='{hex_code}'></div>", unsafe_allow_html=True)
            
        st.write("")
        # Keywords
        keywords = dna.get('aesthetic', [])
        if keywords:
            for k in keywords:
                kw = k.get('keyword') if isinstance(k, dict) else k
                st.markdown(f"<span class='dna-tag' style='border-color: var(--accent-color); color: var(--accent-color);'>{kw}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.write("")
    
    # Action Button
    c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
    with c_btn2:
        if st.button("GENERATE STRATEGIC CAMPAIGNS"):
            st.session_state.step = 3
            st.rerun()

# --- PHASE 3: GENERATION & RESULTS ---
elif st.session_state.step == 3:
    st.markdown("<h1>Strategic Output</h1>", unsafe_allow_html=True)
    
    # 1. Génération Texte (Si pas encore fait)
    if not st.session_state.campaigns:
        with st.spinner("Gemini is brainstorming campaign concepts..."):
            st.session_state.campaigns = generate_strategy_gemini(st.session_state.dna)
            # Petit hack pour forcer le refresh si la génération est instantanée
            time.sleep(0.5) 
    
    # Affichage des Campagnes
    if st.session_state.campaigns:
        for campaign in st.session_state.campaigns:
            c_id = campaign.get('id')
            
            # Cadre visuel
            st.markdown(f"<div class='campaign-card'>", unsafe_allow_html=True)
            col_text, col_img = st.columns([1, 1], gap="large")
            
            with col_text:
                st.markdown(f"<h3>0{c_id}. {campaign.get('title')}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size:1.1rem; line-height:1.6;'>{campaign.get('strategy')}</p>", unsafe_allow_html=True)
                
                with st.expander("View Visual Prompt"):
                    st.code(campaign.get('visual_prompt'), language="text")
            
            with col_img:
                # 2. Génération Image (Lazy Loading)
                # On vérifie si l'image existe déjà dans le session_state
                if c_id not in st.session_state.images:
                    # On affiche un spinner localisé
                    with st.spinner(f"Rendering visual for Campaign {c_id}..."):
                        img = generate_image_imagen(campaign.get('visual_prompt'))
                        if img:
                            st.session_state.images[c_id] = img
                        else:
                            st.session_state.images[c_id] = "ERROR"
                
                # Affichage
                current_img = st.session_state.images.get(c_id)
                if current_img and current_img != "ERROR":
                    st.image(current_img, use_container_width=True, caption="Generated by Google Imagen")
                elif current_img == "ERROR":
                    st.warning("Visual rendering unavailable (API Quota or Filter).")
                else:
                    st.info("Waiting for generation...")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
    else:
        st.error("Failed to generate campaigns. Please restart.")
    
    # Reset
    st.write("")
    if st.button("START NEW PROJECT"):
        st.session_state.clear()
        st.rerun()
