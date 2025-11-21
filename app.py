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

# --- 2. STYLE SYSTEM (ROUNDED PREMIUM) ---
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@400;600&display=swap');

    :root {
        --bg-color: #050505;
        --card-bg: #111;
        --text-primary: #FFFFFF;
        --text-secondary: #999;
        --accent-blue: #2E5CFF; /* Beau bleu premium */
        --border-radius: 24px;
        --btn-radius: 50px;
    }

    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }
    
    /* TYPOGRAPHY */
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; font-weight: 400 !important; letter-spacing: -0.02em; }
    h1 { font-size: 3.8rem !important; }
    
    /* INPUTS */
    .stTextInput > div > div > input {
        background-color: #0A0A0A;
        color: white;
        border: 1px solid #333;
        border-radius: var(--border-radius);
        padding: 15px 25px;
        font-size: 1rem;
        text-align: center;
        transition: border-color 0.3s ease;
    }
    /* LE BLEU PREMIUM AU FOCUS */
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 1px var(--accent-blue) !important;
    }

    /* BUTTONS (Centrés, Arrondis, Texte Sombre) */
    .stButton > button {
        background-color: white;
        color: #000 !important; /* Texte sombre */
        border: none;
        border-radius: var(--btn-radius);
        padding: 16px 40px;
        text-transform: uppercase;
        font-size: 0.9rem;
        letter-spacing: 1px;
        font-weight: 700;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        width: 100%;
        box-shadow: 0 5px 20px rgba(255,255,255,0.1);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255,255,255,0.2);
        color: #000 !important;
    }

    /* CARDS */
    .rounded-card {
        border: 1px solid #222;
        border-radius: var(--border-radius);
        padding: 35px;
        background: #0e0e0e;
        margin-bottom: 20px;
    }

    /* PILLS (Tags encadrés) */
    .pill-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 10px;
    }
    .pill {
        background: rgba(255,255,255,0.05);
        border: 1px solid #333;
        padding: 8px 18px;
        border-radius: 30px;
        font-size: 0.85rem;
        color: #ddd;
        white-space: nowrap;
    }

    /* LOADER FULLSCREEN */
    .fullscreen-loader {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: #000; z-index: 99999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .loader-small {
        font-family: 'Inter', sans-serif; font-size: 0.7rem; letter-spacing: 3px; 
        text-transform: uppercase; color: #666; margin-bottom: 15px;
    }
    .loader-large {
        font-family: 'Playfair Display', serif; font-size: 2.5rem; color: white;
        animation: pulse 2s infinite;
    }
    @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }

    /* EXPANDER STYLING */
    .streamlit-expanderHeader {
        background-color: transparent !important;
        color: #666 !important;
        font-size: 0.9rem !important;
    }
    
    /* HIDE ELEMENTS */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 3. SCRAPING ---
def get_brand_dna(url):
    rules = {
        "projectName": "Brand Name",
        "tagline": "Slogan",
        "industry": "Industry",
        "concept": "Detailed Concept Summary (2-3 sentences)",
        "colors": {"description": "Hex colors", "type": "list", "output": {"hex_code": "#Hex"}},
        "aesthetic": {"description": "Aesthetic keywords", "type": "list", "output": {"keyword": "Word"}},
        "values": {"description": "Brand values", "type": "list", "output": {"value": "Value"}},
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

# --- 4. STRATÉGIE (Gemini 2.5) ---
def generate_strategy(dna):
    prompt = f"""
    Role: Luxury Brand Strategist.
    Brand DNA: {json.dumps(dna)}
    
    Task: Develop 3 detailed social media campaigns.
    Output JSON:
    {{
        "campaigns": [
            {{
                "id": 1,
                "title": "Campaign Title",
                "strategy": "Detailed strategy explaining the angle, target audience, and why it fits the brand (approx 40 words).",
                "visual_prompt": "Extremely detailed commercial photography prompt: Subject, Lighting (e.g. softbox, golden hour), Camera (e.g. 85mm, f/1.8), Texture, Color Grading, Composition. Must ensure premium result."
            }}
        ]
    }}
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(res.text)['campaigns']
    except: return []

# --- 5. IMAGE (IMAGEN 4.0 - FIX 404) ---
def generate_image_imagen(prompt_text):
    # Utilisation du endpoint PREVIEW 06-06 (Le seul qui marche chez toi)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-preview-06-06:predict?key={GOOGLE_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [{"prompt": prompt_text + ", 8k, photorealistic, highly detailed, award winning photography"}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:5"}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            predictions = response.json().get('predictions', [])
            if predictions:
                b64 = predictions[0].get('bytesBase64Encoded', predictions[0])
                return Image.open(BytesIO(base64.b64decode(b64)))
        return None
    except: return None

# --- 6. UI FLOW ---

if 'step' not in st.session_state: st.session_state.step = 1
if 'dna' not in st.session_state: st.session_state.dna = None
if 'campaigns' not in st.session_state: st.session_state.campaigns = None
if 'images' not in st.session_state: st.session_state.images = {}

# PAGE 1 : LANDING
if st.session_state.step == 1:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>PROJECT ONE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; margin-bottom:40px; color:#888;'>ENTER YOUR WEBSITE. WE GENERATE YOUR BRAND IDENTITY.</p>", unsafe_allow_html=True)
        
        # Input centré
        url = st.text_input("URL", placeholder="www.example.com", label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bouton Centré
        b1, b2, b3 = st.columns([1, 1, 1]) # Astuce pour centrer le bouton
        with b2:
            if st.button("GENERATE IDENTITY"):
                if url:
                    st.session_state.url = url if url.startswith('http') else 'https://' + url
                    st.session_state.step = 1.5
                    st.rerun()

# LOADING SCREEN 1
elif st.session_state.step == 1.5:
    st.markdown("""
    <div class="fullscreen-loader">
        <div class="loader-small">PROJECT ONE</div>
        <div class="loader-large">ANALYZING DNA</div>
    </div>
    """, unsafe_allow_html=True)
    
    dna = get_brand_dna(st.session_state.url)
    if dna:
        st.session_state.dna = dna
        st.session_state.step = 2
        st.rerun()
    else:
        st.error("Failed.")
        if st.button("Back"): st.session_state.step = 1; st.rerun()

# PAGE 2 : DASHBOARD
elif st.session_state.step == 2:
    dna = st.session_state.dna
    
    # Header
    st.markdown(f"<p style='text-align:center; letter-spacing:2px; font-size:0.8rem; color:#666;'>IDENTITY EXTRACTED</p>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; margin-top:0;'>{dna.get('projectName', 'BRAND').upper()}</h1>", unsafe_allow_html=True)
    
    # Concept plus gros et lisible
    st.markdown(f"""
    <div style="text-align:center; max-width:700px; margin: 0 auto 50px auto;">
        <p style="font-size:1.3rem; line-height:1.5; color:#EEE; font-weight:300;">
            {dna.get('concept')}
        </p>
        <p style="color:#888; margin-top:10px; font-style:italic;">"{dna.get('tagline')}"</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("<div class='rounded-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Visual Codes</h3>", unsafe_allow_html=True)
        
        st.write("PALETTE")
        cols = st.columns(5)
        for color in dna.get('colors', [])[:5]:
            st.markdown(f"<div style='background-color:{color.get('hex_code')}; height:50px; border-radius:10px; margin-bottom:5px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.7rem; text-align:center; color:#666;'>{color.get('hex_code')}</div>", unsafe_allow_html=True)
            
        st.markdown("<br>AESTHETIC", unsafe_allow_html=True)
        st.markdown("<div class='pill-container'>", unsafe_allow_html=True)
        for a in dna.get('aesthetic', []):
            st.markdown(f"<div class='pill'>{a.get('keyword')}</div>", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='rounded-card' style='height:100%'>", unsafe_allow_html=True)
        st.markdown("<h3>Core Values</h3>", unsafe_allow_html=True)
        st.markdown("<div class='pill-container'>", unsafe_allow_html=True)
        for v in dna.get('values', []):
            st.markdown(f"<div class='pill'>{v.get('value')}</div>", unsafe_allow_html=True)
        st.markdown("</div><br>", unsafe_allow_html=True)
        
        # Affichage conditionnel des images
        scraped_imgs = dna.get('images', [])
        if scraped_imgs and len(scraped_imgs) > 0:
             st.write("INSPIRATION")
             ic1, ic2 = st.columns(2)
             if len(scraped_imgs) > 0: ic1.image(scraped_imgs[0]['src'], use_container_width=True)
             if len(scraped_imgs) > 1: ic2.image(scraped_imgs[1]['src'], use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        if st.button("GENERATE CAMPAIGNS & VISUALS"):
            st.session_state.step = 3
            st.rerun()

# PAGE 3 : CAMPAIGNS
elif st.session_state.step == 3:
    
    # Loader
    if not st.session_state.campaigns:
        st.markdown("""
        <div class="fullscreen-loader">
            <div class="loader-small">PROJECT ONE</div>
            <div class="loader-large">CRAFTING VISUALS</div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.campaigns = generate_strategy(st.session_state.dna)
        for camp in st.session_state.campaigns:
            img = generate_image_imagen(camp['visual_prompt'])
            if img: st.session_state.images[camp['id']] = img
        st.rerun()

    # Display
    st.markdown("<h2 style='text-align:center; margin-bottom:50px;'>STRATEGIC PROPOSALS</h2>", unsafe_allow_html=True)
    
    for camp in st.session_state.campaigns:
        cid = camp['id']
        st.markdown(f"<div class='rounded-card'>", unsafe_allow_html=True)
        cols = st.columns([1, 1])
        
        with cols[0]:
            st.markdown(f"<span style='font-size:3rem; font-family:Playfair Display; color:#333;'>0{cid}</span>", unsafe_allow_html=True)
            st.markdown(f"<h3>{camp['title']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:1.1rem; line-height:1.6; margin-top:20px; color:#ddd;'>{camp['strategy']}</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("VIEW PROMPT DATA"):
                st.code(camp['visual_prompt'], language="text")

        with cols[1]:
            if cid in st.session_state.images:
                st.image(st.session_state.images[cid], use_container_width=True)
            else:
                st.warning("Visual render failed. The AI model might be busy.")
        
        st.markdown("</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        if st.button("START OVER"):
            st.session_state.clear()
            st.rerun()
