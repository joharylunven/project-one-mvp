import streamlit as st
import requests
import json
import google.generativeai as genai
import base64
from PIL import Image
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="PROJECT ONE", layout="wide", initial_sidebar_state="collapsed")

SCRAPINGBEE_API_KEY = st.secrets.get("SCRAPINGBEE_API_KEY", "")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")

genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. STYLE SYSTEM (PIXEL PERFECT) ---
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@400;600&display=swap');

    :root {
        --bg-color: #080808; /* Noir profond mais pas absolu pour le confort */
        --card-bg: rgba(25, 25, 25, 0.6); /* Glass effect */
        --text-primary: #FFFFFF;
        --text-secondary: #A0A0A0;
        --accent-blue: #2E5CFF;
        --border-color: rgba(255, 255, 255, 0.1);
    }

    /* RESET GLOBAL */
    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }

    /* TYPOGRAPHIE */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        font-weight: 400 !important;
        letter-spacing: -0.01em;
        color: white !important;
    }
    
    p, span, div {
        font-family: 'Inter', sans-serif;
        color: var(--text-secondary);
    }

    /* INPUT TEXTE (CORRECTION ROUGE -> BLEU) */
    .stTextInput > div > div > input {
        background-color: #111;
        color: white;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 12px 20px;
        font-size: 1rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    /* Force le bleu au focus et supprime le rouge par défaut de Streamlit */
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 1px var(--accent-blue) !important;
        outline: none;
    }

    /* BOUTONS (FIX LIGNE UNIQUE + HOVER) */
    .stButton > button {
        background-color: white;
        color: black !important;
        border: none;
        border-radius: 8px;
        padding: 14px 30px;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 1px;
        font-weight: 600;
        width: 100%;
        white-space: nowrap !important; /* Empêche le retour à la ligne */
        transition: background-color 0.3s ease, transform 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #E0E0E0; /* Gris très clair subtil */
        color: black !important;
        transform: translateY(-1px);
        border: none;
    }
    .stButton > button:active {
        background-color: #CCC;
    }

    /* CARTES (GLASSMORPHISM V4) */
    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }

    /* PILLS (TAGS VALEURS & ESTHÉTIQUE) */
    .pill-container {
        display: flex;
        flex-wrap: wrap;
        gap: 12px; /* Espace entre les tags */
        margin-top: 15px;
    }
    .pill {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #333;
        padding: 8px 20px;
        border-radius: 50px;
        font-size: 0.9rem;
        color: #EEE;
        text-transform: capitalize; /* Première lettre majuscule */
        letter-spacing: 0.5px;
        white-space: nowrap;
        display: inline-block;
    }

    /* COULEURS HEX */
    .color-row {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        background: rgba(255,255,255,0.03);
        padding: 8px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .color-preview {
        width: 24px; height: 24px;
        border-radius: 4px;
        margin-right: 15px;
        border: 1px solid rgba(255,255,255,0.2);
    }

    /* LOADER FULLSCREEN */
    .fullscreen-loader {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: #050505; z-index: 99999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .loader-brand {
        font-family: 'Inter', sans-serif; font-size: 0.75rem; letter-spacing: 4px; 
        text-transform: uppercase; color: #666; margin-bottom: 20px;
    }
    .loader-status {
        font-family: 'Playfair Display', serif; font-size: 2rem; color: white;
        animation: pulse 2s infinite;
    }
    @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }

    /* CLEANUP STREAMLIT */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container { padding-top: 3rem; padding-bottom: 5rem; }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 3. LOGIQUE : SCRAPING ---
def get_brand_dna(url):
    rules = {
        "projectName": "Brand Name",
        "tagline": "Tagline",
        "industry": "Industry",
        "concept": "Concept Summary (Max 25 words)",
        "colors": {"description": "Hex colors", "type": "list", "output": {"hex_code": "#Hex"}},
        "aesthetic": {"description": "Aesthetic adjectives", "type": "list", "output": {"keyword": "Adjective"}},
        "values": {"description": "Brand values", "type": "list", "output": {"value": "ValueName"}},
        "images": {"description": "Images", "type": "list", "output": {"src": "URL"}}
    }
    params = {
        'api_key': SCRAPINGBEE_API_KEY, 'url': url, 'render_js': 'true',
        'ai_extract_rules': json.dumps(rules), 'premium_proxy': 'true'
    }
    try:
        response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, timeout=45)
        return response.json() if response.status_code == 200 else None
    except: return None

# --- 4. LOGIQUE : STRATÉGIE (Gemini) ---
def generate_strategy(dna):
    prompt = f"""
    Role: Luxury Brand Strategist.
    Brand DNA: {json.dumps(dna)}
    
    Task: Create 3 distinct, high-end social media campaign angles.
    
    Output JSON:
    {{
        "campaigns": [
            {{
                "id": 1,
                "title": "Campaign Title (Short & Impactful)",
                "strategy": "One sentence explaining the strategic angle.",
                "visual_prompt": "Commercial photography description: Subject, Lighting, Composition, Textures. High fidelity."
            }}
        ]
    }}
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(res.text)['campaigns']
    except: return []

# --- 5. LOGIQUE : IMAGE (Imagen 4.0 - FIXE) ---
def generate_image_imagen(prompt_text):
    # Modèle validé dans ta liste
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-preview-06-06:predict?key={GOOGLE_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [{"prompt": prompt_text + ", photorealistic, 8k, highly detailed, commercial photography"}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:5"}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            predictions = response.json().get('predictions', [])
            if predictions:
                # Gestion robuste du format de retour
                data = predictions[0]
                b64 = data.get('bytesBase64Encoded', data) if isinstance(data, dict) else data
                return Image.open(BytesIO(base64.b64decode(b64)))
        return None
    except: return None

# --- 6. UI FLOW ---

if 'step' not in st.session_state: st.session_state.step = 1
if 'dna' not in st.session_state: st.session_state.dna = None
if 'campaigns' not in st.session_state: st.session_state.campaigns = None
if 'images' not in st.session_state: st.session_state.images = {}

# --- PAGE 1 : LANDING ---
if st.session_state.step == 1:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # Centrage vertical et horizontal
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>PROJECT ONE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; margin-bottom:40px;'>ENTER YOUR WEBSITE. WE GENERATE YOUR BRAND IDENTITY.</p>", unsafe_allow_html=True)
        
        # Input
        url = st.text_input("URL", placeholder="www.example.com", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bouton Centré et Clean
        b1, b2, b3 = st.columns([1, 2, 1]) 
        with b2:
            if st.button("GENERATE IDENTITY"):
                if url:
                    st.session_state.url = url if url.startswith('http') else 'https://' + url
                    st.session_state.step = 1.5
                    st.rerun()

# --- LOADING OVERLAY ---
elif st.session_state.step == 1.5:
    st.markdown("""
    <div class="fullscreen-loader">
        <div class="loader-brand">PROJECT ONE</div>
        <div class="loader-status">ANALYZING IDENTITY</div>
    </div>
    """, unsafe_allow_html=True)
    
    dna = get_brand_dna(st.session_state.url)
    if dna:
        st.session_state.dna = dna
        st.session_state.step = 2
        st.rerun()
    else:
        st.error("Unable to analyze this site.")
        if st.button("Back"): st.session_state.step = 1; st.rerun()

# --- PAGE 2 : BRAND DNA (CLEAN & USER FRIENDLY) ---
elif st.session_state.step == 2:
    dna = st.session_state.dna
    
    # Header
    st.markdown(f"<p style='text-align:center; font-size:0.8rem; letter-spacing:2px; color:#666; margin-bottom:10px;'>IDENTITY EXTRACTED</p>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; margin:0;'>{dna.get('projectName', 'BRAND').upper()}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-style:italic; margin-top:10px; color:#888;'>\"{dna.get('tagline')}\"</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_L, col_R = st.columns([1, 1])
    
    with col_L:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Visual Signature</h3>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Couleurs : Liste propre
        st.markdown("<span style='font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:1px;'>Color Palette</span>", unsafe_allow_html=True)
        for color in dna.get('colors', [])[:5]:
            hex = color.get('hex_code')
            st.markdown(f"""
            <div class="color-row">
                <div class="color-preview" style="background-color:{hex};"></div>
                <span style="font-family:'Inter'; font-size:0.9rem; color:#ccc;">{hex}</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br><span style='font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:1px;'>Aesthetic</span>", unsafe_allow_html=True)
        st.markdown('<div class="pill-container">', unsafe_allow_html=True)
        for a in dna.get('aesthetic', []):
            st.markdown(f"<div class='pill'>{a.get('keyword')}</div>", unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    with col_R:
        st.markdown("<div class='glass-card' style='height:100%;'>", unsafe_allow_html=True)
        st.markdown("<h3>Core Essence</h3>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown(f"<p style='font-size:1.1rem; line-height:1.6; color:#EEE;'>{dna.get('concept')}</p>", unsafe_allow_html=True)
        
        st.markdown("<br><span style='font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:1px;'>Values</span>", unsafe_allow_html=True)
        st.markdown('<div class="pill-container">', unsafe_allow_html=True)
        for v in dna.get('values', []):
            st.markdown(f"<div class='pill'>{v.get('value')}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Images (Seulement si présentes)
    scraped = dna.get('images', [])
    if scraped:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:0.8rem; letter-spacing:2px; color:#666;'>WEB INSPIRATION</p>", unsafe_allow_html=True)
        ic1, ic2, ic3, ic4 = st.columns(4)
        for i, img in enumerate(scraped[:4]):
            with [ic1, ic2, ic3, ic4][i]:
                st.image(img['src'], use_container_width=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Bouton Next
    b1, b2, b3 = st.columns([1, 2, 1])
    with b2:
        if st.button("GENERATE CAMPAIGNS & VISUALS"):
            st.session_state.step = 3
            st.rerun()

# --- PAGE 3 : CAMPAIGNS ---
elif st.session_state.step == 3:
    
    # Loader (Only first time)
    if not st.session_state.campaigns:
        st.markdown("""
        <div class="fullscreen-loader">
            <div class="loader-brand">PROJECT ONE</div>
            <div class="loader-status">CRAFTING VISUALS</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.campaigns = generate_strategy(st.session_state.dna)
        # Generation Images
        for camp in st.session_state.campaigns:
            img = generate_image_imagen(camp['visual_prompt'])
            if img: st.session_state.images[camp['id']] = img
        st.rerun()

    # Results
    st.markdown("<h2 style='text-align:center; margin-bottom:60px;'>STRATEGIC CAMPAIGNS</h2>", unsafe_allow_html=True)
    
    for camp in st.session_state.campaigns:
        cid = camp['id']
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        
        cols = st.columns([1, 1])
        with cols[0]:
            st.markdown(f"<span style='font-size:3rem; font-family:Playfair Display; color:#333;'>0{cid}</span>", unsafe_allow_html=True)
            st.markdown(f"<h3>{camp['title']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:1.1rem; line-height:1.6; color:#CCC; margin-top:20px;'>{camp['strategy']}</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("VIEW PROMPT DETAILS"):
                st.info(camp['visual_prompt'])

        with cols[1]:
            if cid in st.session_state.images:
                st.image(st.session_state.images[cid], use_container_width=True)
            else:
                st.warning("Visual generation failed. The model might be temporarily unavailable.")

        st.markdown("</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns([1, 2, 1])
    with b2:
        if st.button("START OVER"):
            st.session_state.clear()
            st.rerun()
