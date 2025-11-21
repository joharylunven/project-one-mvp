import streamlit as st
import requests
import json
import google.generativeai as genai
import base64
from PIL import Image
from io import BytesIO
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="PROJECT ONE", layout="wide", initial_sidebar_state="collapsed")

SCRAPINGBEE_API_KEY = st.secrets.get("SCRAPINGBEE_API_KEY", "")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")

genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. STYLE SYSTEM (SILENT LUXURY) ---
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=Playfair+Display:wght@400;600&display=swap');

    /* VARIABLES */
    :root {
        --bg-color: #050505;
        --card-bg: #111;
        --text-primary: #FFFFFF;
        --text-secondary: #888;
        --border: #222;
    }

    /* GLOBAL RESET */
    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }
    
    /* TYPOGRAPHY */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        font-weight: 400 !important;
        letter-spacing: -0.02em;
    }
    
    h1 { font-size: 4rem !important; margin-bottom: 0.5rem !important; }
    p { font-weight: 300; letter-spacing: 0.02em; color: #ccc; }

    /* INPUTS */
    .stTextInput > div > div > input {
        background-color: transparent;
        color: white;
        border: none;
        border-bottom: 1px solid #444;
        border-radius: 0;
        padding: 15px 0;
        font-size: 1.2rem;
        font-family: 'Inter', sans-serif;
        text-align: center;
    }
    .stTextInput > div > div > input:focus {
        border-bottom-color: #fff;
        box-shadow: none;
    }

    /* BUTTONS */
    .stButton > button {
        background-color: white;
        color: black !important;
        border: 1px solid white;
        border-radius: 0px;
        padding: 16px 40px;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 2px;
        font-weight: 600;
        transition: all 0.4s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: black;
        color: white !important;
        border: 1px solid white;
    }

    /* CARDS */
    .minimal-card {
        border: 1px solid var(--border);
        padding: 30px;
        background: #0a0a0a;
        transition: border-color 0.3s;
    }
    .minimal-card:hover {
        border-color: #444;
    }

    /* COLOR CIRCLES */
    .color-dot {
        height: 40px;
        width: 40px;
        border-radius: 50%;
        display: inline-block;
        border: 1px solid #333;
        margin-right: 15px;
    }

    /* FULL SCREEN LOADER */
    .fullscreen-loader {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: #000;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .loader-text {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        color: white;
        animation: pulse 2s infinite;
    }
    @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
    
    /* HIDE DEFAULT STREAMLIT ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 3. SCRAPING (ScrapingBee AI) ---
def get_brand_dna(url):
    """Extraction fidèle de l'ADN via ScrapingBee."""
    rules = {
        "projectName": "Brand Name",
        "tagline": "Slogan or Tagline",
        "industry": "Industry Sector",
        "concept": "Brand Concept Summary (2 sentences)",
        "colors": {
            "description": "List of main HEX colors found in CSS",
            "type": "list",
            "output": {"hex_code": "#HexCode"}
        },
        "aesthetic": {
            "description": "5 aesthetic keywords (e.g. Minimalist, Bold)",
            "type": "list",
            "output": {"keyword": "Word"}
        },
         "values": {
            "description": "Brand values",
            "type": "list",
            "output": {"value": "Value"}
        }
    }
    
    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': url,
        'render_js': 'true',
        'ai_extract_rules': json.dumps(rules),
        'premium_proxy': 'true'
    }
    
    try:
        response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, timeout=45)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# --- 4. STRATÉGIE (Gemini 2.5) ---
def generate_strategy(dna):
    prompt = f"""
    Act as a Luxury Brand Strategist.
    
    BRAND DNA:
    {json.dumps(dna)}
    
    Create 3 distinct social media campaign concepts.
    
    OUTPUT JSON FORMAT:
    {{
        "campaigns": [
            {{
                "id": 1,
                "title": "Campaign Title",
                "strategy": "Why this fits the brand DNA (1 sentence).",
                "visual_prompt": "Detailed photography instructions: Subject, Lighting, Camera Angle, Texture, Vibe. MUST be high-end commercial photography description."
            }}
        ]
    }}
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(res.text)['campaigns']
    except:
        return []

# --- 5. GENERATION IMAGE (CORRECTION 404) ---
def generate_image_imagen(prompt_text):
    """
    Utilise le modèle EXACT de ta liste pour éviter l'erreur 404.
    """
    # MISE A JOUR DU MODELE ICI : imagen-4.0-generate-preview-06-06
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-preview-06-06:predict?key={GOOGLE_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [{"prompt": prompt_text + ", photorealistic, 8k, highly detailed, instagram feed ratio"}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "4:5"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            predictions = response.json().get('predictions', [])
            if predictions:
                # Le format 4.0 preview retourne souvent bytesBase64Encoded directement
                b64 = predictions[0].get('bytesBase64Encoded', predictions[0])
                return Image.open(BytesIO(base64.b64decode(b64)))
        else:
            # Debug silencieux console si besoin
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(e)
        return None

# --- 6. UI FLOW ---

if 'step' not in st.session_state: st.session_state.step = 1
if 'dna' not in st.session_state: st.session_state.dna = None
if 'campaigns' not in st.session_state: st.session_state.campaigns = None
if 'images' not in st.session_state: st.session_state.images = {}

# PAGE 1 : LANDING
if st.session_state.step == 1:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>PROJECT ONE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; margin-bottom:50px;'>ENTER YOUR WEBSITE. WE GENERATE YOUR BRAND IDENTITY.</p>", unsafe_allow_html=True)
        
        url = st.text_input("URL", placeholder="www.example.com", label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("GENERATE IDENTITY"):
            if url:
                st.session_state.url = url if url.startswith('http') else 'https://' + url
                st.session_state.step = 1.5
                st.rerun()

# LOADING SCREEN (FULL SCREEN)
elif st.session_state.step == 1.5:
    st.markdown("""
    <div class="fullscreen-loader">
        <div class="loader-text">ANALYZING BRAND DNA</div>
        <p style="color:#666; margin-top:20px;">Please wait while we extract visual codes...</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Le code s'exécute pendant que l'overlay est affiché
    dna = get_brand_dna(st.session_state.url)
    if dna:
        st.session_state.dna = dna
        st.session_state.step = 2
        st.rerun()
    else:
        st.error("Analysis Failed. Check URL.")
        if st.button("Back"): st.session_state.step = 1; st.rerun()

# PAGE 2 : DNA RESULTS
elif st.session_state.step == 2:
    dna = st.session_state.dna
    
    st.markdown(f"<p style='text-align:center; letter-spacing:3px; font-size:0.8rem;'>GENERATED IDENTITY</p>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center;'>{dna.get('projectName', 'Unknown').upper()}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; margin-bottom:60px; color:#888;'>{dna.get('tagline')}</p>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("<div class='minimal-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Visual Codes</h3><br>", unsafe_allow_html=True)
        
        # Couleurs (Affichage fidèle)
        st.write("PALETTE")
        cols = st.columns(5)
        for idx, color in enumerate(dna.get('colors', [])[:5]):
            hex_code = color.get('hex_code')
            # Carré de couleur simple et pur
            st.markdown(f"<div style='background-color:{hex_code}; height:60px; width:100%; margin-bottom:10px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:0.7rem; color:#666;'>{hex_code}</p>", unsafe_allow_html=True)
            
        st.write("AESTHETIC")
        tags = [a.get('keyword') for a in dna.get('aesthetic', [])]
        st.markdown(f"<p style='color:white;'>{' • '.join(tags).upper()}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='minimal-card' style='height:100%;'>", unsafe_allow_html=True)
        st.markdown("<h3>Core Concept</h3><br>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:1.1rem; line-height:1.6; color:#ddd;'>{dna.get('concept')}</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("VALUES")
        vals = [v.get('value') for v in dna.get('values', [])]
        st.markdown(f"<p style='color:white;'>{' • '.join(vals).upper()}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("GENERATE CAMPAIGNS & VISUALS"):
        st.session_state.step = 3
        st.rerun()

# PAGE 3 : CAMPAIGNS (LOADING FULL SCREEN + DISPLAY)
elif st.session_state.step == 3:
    
    # 1. Logic Generation (Full Screen Loader)
    if not st.session_state.campaigns:
        st.markdown("""
        <div class="fullscreen-loader">
            <div class="loader-text">DESIGNING CAMPAIGNS</div>
            <p style="color:#666; margin-top:20px;">AI is rendering high-fidelity visuals...</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate Text Strategy
        st.session_state.campaigns = generate_strategy(st.session_state.dna)
        
        # Generate Images (Loop)
        for camp in st.session_state.campaigns:
            img = generate_image_imagen(camp['visual_prompt'])
            if img:
                st.session_state.images[camp['id']] = img
        
        # Refresh to remove loader
        st.rerun()

    # 2. Display Results
    st.markdown("<h2 style='text-align:center; margin-bottom:50px;'>CAMPAIGN PROPOSALS</h2>", unsafe_allow_html=True)
    
    for camp in st.session_state.campaigns:
        cid = camp['id']
        st.markdown(f"<div class='minimal-card' style='margin-bottom:40px;'>", unsafe_allow_html=True)
        
        cols = st.columns([1, 1])
        with cols[0]:
            st.markdown(f"<span style='font-size:3rem; font-family:Playfair Display; color:#333;'>0{cid}</span>", unsafe_allow_html=True)
            st.markdown(f"<h3>{camp['title']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:1.1rem; line-height:1.6; margin-top:20px;'>{camp['strategy']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:0.8rem; color:#666; margin-top:20px; border-top:1px solid #222; padding-top:10px;'>PROMPT DATA: {camp['visual_prompt'][:100]}...</p>", unsafe_allow_html=True)

        with cols[1]:
            if cid in st.session_state.images:
                st.image(st.session_state.images[cid], use_container_width=True)
            else:
                st.warning("Visual render failed.")
        
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("START OVER"):
        st.session_state.clear()
        st.rerun()
