import streamlit as st
import requests
import json
import google.generativeai as genai
import base64
from PIL import Image
from io import BytesIO
import time

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(page_title="PROJECT ONE | Luxury AI", layout="wide", initial_sidebar_state="collapsed")

SCRAPINGBEE_API_KEY = st.secrets.get("SCRAPINGBEE_API_KEY", "")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")

genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. DESIGN SYSTEM "ULTRA PREMIUM" (CSS INJECTION) ---
def inject_custom_css():
    st.markdown("""
    <style>
    /* IMPORTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap');

    /* VARIABLES */
    :root {
        --bg-color: #050505;
        --card-bg: #111111;
        --text-primary: #EAEAEA;
        --text-secondary: #888888;
        --accent-gold: #D4AF37; /* Or Luxe */
        --accent-gold-dim: #8a7020;
        --border-color: #222222;
    }

    /* GLOBAL RESET */
    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }
    
    h1, h2, h3, h4, .premium-font {
        font-family: 'Playfair Display', serif !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em;
    }
    
    h1 { font-size: 3.5rem !important; font-weight: 700; background: linear-gradient(to right, #fff, #999); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    h2 { font-size: 2rem !important; margin-top: 40px !important; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }
    
    /* CUSTOM CARDS */
    .glass-card {
        background: rgba(20, 20, 20, 0.6);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 24px;
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .glass-card:hover {
        border-color: var(--accent-gold-dim);
        transform: translateY(-2px);
    }

    /* INPUTS */
    .stTextInput > div > div > input {
        background-color: #0A0A0A;
        color: white;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 12px;
        font-family: 'Inter', sans-serif;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-gold);
        box-shadow: 0 0 0 1px var(--accent-gold);
    }

    /* BUTTONS */
    .stButton > button {
        background: linear-gradient(135deg, #D4AF37 0%, #AA8A28 100%);
        color: black !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: none;
        border-radius: 4px;
        padding: 14px 32px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        box-shadow: 0 8px 25px rgba(212, 175, 55, 0.25);
        transform: scale(1.01);
    }

    /* COLOR CIRCLES */
    .color-dot {
        height: 30px;
        width: 30px;
        border-radius: 50%;
        display: inline-block;
        border: 1px solid #333;
        margin-right: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }

    /* TAGS */
    .luxury-tag {
        display: inline-block;
        padding: 6px 14px;
        margin: 4px;
        background: rgba(255,255,255,0.05);
        border: 1px solid #333;
        border-radius: 30px;
        font-size: 0.8rem;
        color: #ccc;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* LOADING SPINNER CUSTOMIZATION */
    .stSpinner > div {
        border-top-color: var(--accent-gold) !important;
    }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 3. LOGIQUE MÉTIER : SCRAPING (ScrapingBee) ---
def get_brand_dna_scrapingbee(url):
    """Extrait l'ADN de la marque avec une précision chirurgicale via ScrapingBee AI."""
    
    rules = {
        "projectName": "The official brand name",
        "tagline": "The main luxurious slogan or promise",
        "industry": "The specific luxury or market niche",
        "concept": "A sophisticated 2-sentence description of the brand concept",
        "colors": {
            "description": "Extract the 5 primary hex codes",
            "type": "list",
            "output": {"hex_code": "hex color string"}
        },
        "fonts": {
            "description": "Extract font family names",
            "type": "list",
            "output": {"font_name": "Name of the font"}
        },
        "aesthetic": {
            "description": "5 Adjectives describing the visual mood (e.g. Minimalist, Noir, Ethereal)",
            "type": "list",
            "output": {"keyword": "Adjective"}
        },
        "values": {
            "description": "Core brand values",
            "type": "list",
            "output": {"value": "Value name"}
        }
    }
    
    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': url,
        'render_js': 'true',
        'ai_extract_rules': json.dumps(rules),
        'premium_proxy': 'true' # On force les proxys premium pour éviter les blocages
    }
    
    try:
        response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, timeout=60)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

# --- 4. LOGIQUE MÉTIER : STRATÉGIE (Gemini 2.5 Flash) ---
def generate_premium_campaigns(dna):
    """Génère une stratégie de contenu haut de gamme et des prompts d'images techniques."""
    
    # On injecte le DNA dans le prompt
    prompt = f"""
    You are the Creative Director of a world-renowned luxury advertising agency (like Publicis Luxe or Ogilvy).
    
    CLIENT DNA:
    {json.dumps(dna)}

    TASK:
    Develop 3 distinct, high-end social media campaigns.
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "campaigns": [
            {{
                "id": 1,
                "title": "The Campaign Name (Elegant & Catchy)",
                "strategy": "A sophisticated explanation of why this angle works for this brand (max 30 words).",
                "instagram_caption": "A ready-to-post caption including hashtags.",
                "image_prompt_components": {{
                    "subject": "Detailed description of the main subject (e.g., The bottle of perfume on black marble)",
                    "lighting": "Specific lighting setup (e.g., Cinematic warm lighting, shaft of light, chiaroscuro)",
                    "composition": "Camera angle and framing (e.g., Macro 100mm lens, bokeh background, rule of thirds)",
                    "vibe": "The mood (e.g., Ethereal, Moody, Sharp, High-Fashion)"
                }}
            }}
        ]
    }}
    """
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)['campaigns']
    except Exception as e:
        st.error(f"Erreur Stratégie: {e}")
        return []

# --- 5. LOGIQUE MÉTIER : IMAGES (Google Imagen Native) ---
def generate_luxury_image(components):
    """
    Construit un prompt 'Masterpiece' et appelle l'API Google Imagen.
    """
    
    # 1. Construction du Super-Prompt
    # On enrichit la demande de base avec des mots-clés "Qualité Studio"
    final_prompt = (
        f"Professional photography, {components['subject']}. "
        f"Lighting: {components['lighting']}. "
        f"Style: {components['vibe']}, highly detailed, 8k resolution, octane render, "
        f"shot on Phase One XF IQ4 150MP, {components['composition']}, "
        "commercial photography, award winning, sharp focus, instagram feed aspect ratio."
    )
    
    # 2. Appel API (Direct REST pour contourner les limitations de librairies)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={GOOGLE_API_KEY}"
    # Note: J'utilise imagen-3.0-generate-001 qui est très stable et produit des résultats incroyables.
    # Si tu as accès à la beta 4.0, tu peux changer l'URL.
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [{"prompt": final_prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "4:5" # Format Portrait Instagram
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            predictions = response.json().get('predictions', [])
            if predictions:
                # Gestion du format de retour Google (parfois bytesBase64Encoded, parfois direct)
                b64 = predictions[0].get('bytesBase64Encoded', predictions[0])
                return Image.open(BytesIO(base64.b64decode(b64)))
        else:
            st.error(f"Erreur Image API ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Exception Image: {e}")
        return None

# --- 6. INTERFACE UTILISATEUR (THE FLOW) ---

# Gestion des états
if 'step' not in st.session_state: st.session_state.step = 1
if 'dna' not in st.session_state: st.session_state.dna = None
if 'campaigns' not in st.session_state: st.session_state.campaigns = None
if 'images' not in st.session_state: st.session_state.images = {}

# HEADER COMMUN
st.markdown("""
<div style="text-align: center; padding: 40px 0;">
    <p style="font-family: 'Inter'; font-size: 0.8rem; letter-spacing: 3px; text-transform: uppercase; color: #D4AF37; margin-bottom: 10px;">Automated Brand Strategy</p>
    <h1>PROJECT ONE</h1>
</div>
""", unsafe_allow_html=True)

# --- PAGE 1 : ONBOARDING ---
if st.session_state.step == 1:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <h3 style="margin-bottom:20px;">Enter your Digital Identity</h3>
            <p style="color:#888; margin-bottom:30px;">We decode your brand essence to generate bespoke content.</p>
        </div>
        """, unsafe_allow_html=True)
        
        url_input = st.text_input("Website URL", placeholder="ex: www.yourbrand.com", label_visibility="collapsed")
        
        if st.button("Initialize Analysis"):
            if url_input:
                formatted_url = url_input if url_input.startswith('http') else 'https://' + url_input
                st.session_state.url = formatted_url
                st.session_state.step = 1.5
                st.rerun()

# --- LOADING STATE ---
elif st.session_state.step == 1.5:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.spinner("Distilling Brand DNA..."):
            dna = get_brand_dna_scrapingbee(st.session_state.url)
            if dna:
                st.session_state.dna = dna
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("Unable to access this prestige brand. Check URL.")
                if st.button("Return"): st.session_state.step = 1; st.rerun()

# --- PAGE 2 : BRAND DNA (DASHBOARD) ---
elif st.session_state.step == 2:
    dna = st.session_state.dna
    
    # Header DNA
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:40px;">
        <div>
            <h2 style="margin-top:0!important; border:none;">{dna.get('projectName')}</h2>
            <p style="font-style:italic; color:#D4AF37;">"{dna.get('tagline')}"</p>
        </div>
        <div style="text-align:right;">
            <span class="luxury-tag">{dna.get('industry')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Grid Layout
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<h3>Visual Signature</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#888; font-size:0.9rem; margin-bottom:15px;'>COLORS</p>", unsafe_allow_html=True)
        for color in dna.get('colors', [])[:5]:
            hex_c = color.get('hex_code')
            st.markdown(f"""
            <div style="display:flex; align-items:center; margin-bottom:10px;">
                <span class="color-dot" style="background-color:{hex_c};"></span>
                <span style="font-family:'Inter'; font-size:0.9rem;">{hex_c}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<br><p style='color:#888; font-size:0.9rem; margin-bottom:15px;'>AESTHETIC</p>", unsafe_allow_html=True)
        for a in dna.get('aesthetic', []):
            st.markdown(f"<span class='luxury-tag'>{a.get('keyword')}</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="glass-card" style="height:100%;">', unsafe_allow_html=True)
        st.markdown("<h3>Core Identity</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='line-height:1.8; color:#ccc;'>{dna.get('concept')}</p>", unsafe_allow_html=True)
        
        st.markdown("<br><p style='color:#888; font-size:0.9rem; margin-bottom:15px;'>VALUES</p>", unsafe_allow_html=True)
        for v in dna.get('values', []):
            st.markdown(f"<span class='luxury-tag' style='border-color:#D4AF37; color:#D4AF37;'>{v.get('value')}</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    if st.button("Generate Campaign Concepts & Visuals"):
        st.session_state.step = 3
        st.rerun()

# --- PAGE 3 : CAMPAIGNS (LE SHOW) ---
elif st.session_state.step == 3:
    
    # 1. Génération de la stratégie (si pas encore faite)
    if not st.session_state.campaigns:
        with st.spinner("Crafting strategic narratives..."):
            st.session_state.campaigns = generate_premium_campaigns(st.session_state.dna)
    
    st.markdown("<h2 style='text-align:center; border:none; margin-bottom:50px;'>Curated Campaigns</h2>", unsafe_allow_html=True)

    # 2. Boucle d'affichage des campagnes
    for camp in st.session_state.campaigns:
        cid = camp['id']
        
        # Container Principal
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid #333; padding-bottom:20px; margin-bottom:20px;">
                <h3 style="margin:0;">{camp['title']}</h3>
                <span style="color:#D4AF37; font-family:'Inter'; letter-spacing:2px;">CAMPAIGN 0{cid}</span>
            </div>
        """, unsafe_allow_html=True)
        
        col_text, col_img = st.columns([1, 1])
        
        with col_text:
            st.markdown(f"""
            <p style="font-size:1.1rem; line-height:1.6; margin-bottom:20px;">{camp['strategy']}</p>
            <div style="background:rgba(0,0,0,0.3); padding:15px; border-left:2px solid #D4AF37; margin-bottom:20px;">
                <p style="font-size:0.8rem; color:#888; margin:0;">CAPTION</p>
                <p style="font-style:italic; margin-top:5px;">{camp['instagram_caption']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Détails du prompt pour montrer l'intelligence
            with st.expander("VIEW CREATIVE DIRECTION (PROMPT DATA)"):
                st.json(camp['image_prompt_components'])

        with col_img:
            # Bouton ou Image
            img_key = f"img_{cid}"
            
            # Si l'image existe déjà en session, on l'affiche
            if img_key in st.session_state.images:
                st.image(st.session_state.images[img_key], use_container_width=True)
                st.markdown("<p style='text-align:center; font-size:0.8rem; color:#666; margin-top:10px;'>Generated by Google Imagen</p>", unsafe_allow_html=True)
            
            # Sinon, on affiche le bouton de génération
            else:
                st.markdown("""
                <div style="width:100%; height:300px; border:1px dashed #333; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,0.2);">
                    <p style="color:#666;">Visual Concept Ready to Render</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Render Visual 0{cid}", key=f"btn_{cid}"):
                    with st.spinner("Rendering 8K Visual..."):
                        img = generate_luxury_image(camp['image_prompt_components'])
                        if img:
                            st.session_state.images[img_key] = img
                            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True) # Fin Glass Card

    if st.button("Start New Analysis"):
        st.session_state.clear()
        st.rerun()
