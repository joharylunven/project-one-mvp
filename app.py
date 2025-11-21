import streamlit as st
import requests
import json
import google.generativeai as genai
import base64
from PIL import Image
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Project One", layout="wide", initial_sidebar_state="collapsed")

SCRAPINGBEE_API_KEY = st.secrets.get("SCRAPINGBEE_API_KEY", "")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")

genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. DESIGN SYSTEM (PURE CENTERED) ---
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Playfair+Display:wght@400;600&display=swap');

    :root {
        --bg: #050505;
        --card: #0F0F0F;
        --text: #FFFFFF;
        --accent: #3B82F6; /* Bleu Premium */
    }

    .stApp {
        background-color: var(--bg);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }

    /* TYPOGRAPHIE */
    h1 { font-family: 'Playfair Display', serif !important; font-size: 3.5rem !important; font-weight: 400 !important; text-align: center; margin-bottom: 1rem !important; }
    h2 { font-family: 'Playfair Display', serif !important; font-size: 2rem !important; margin-bottom: 1.5rem !important; }
    h3 { font-family: 'Inter', sans-serif !important; font-size: 1.2rem !important; font-weight: 600 !important; margin-bottom: 0.5rem !important; }
    p { color: #AAA; line-height: 1.6; font-size: 1rem; }

    /* PAGE 1 : CENTRAGE ABSOLU */
    .landing-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 70vh; /* Prend une bonne partie de la hauteur */
        width: 100%;
        max-width: 600px;
        margin: 0 auto;
    }

    /* INPUT STYLISÉ */
    .stTextInput { width: 100% !important; }
    .stTextInput > div > div > input {
        background-color: #111;
        border: 1px solid #333;
        color: white;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        font-size: 1.1rem;
        transition: border-color 0.3s;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 1px var(--accent);
    }

    /* BOUTONS CENTRÉS ET LARGES */
    .stButton {
        display: flex;
        justify-content: center;
        width: 100%; 
    }
    .stButton > button {
        background-color: white;
        color: black !important;
        font-weight: 600;
        border-radius: 50px;
        padding: 16px 48px;
        border: none;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        width: 100%; /* Prend toute la largeur du conteneur parent */
        max-width: 400px; /* Limite pour l'esthétique */
        margin-top: 20px;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        background-color: #EAEAEA;
        transform: scale(1.02);
        color: black !important;
    }

    /* PREMIUM CARDS (Page 2 & 3) */
    .premium-card {
        background-color: var(--card);
        border: 1px solid #222;
        border-radius: 16px;
        padding: 40px;
        margin-bottom: 30px;
    }

    /* PALETTE DE COULEURS (FLEXBOX) */
    .palette-container {
        display: flex;
        gap: 15px;
        margin-bottom: 30px;
        flex-wrap: wrap;
    }
    .color-box {
        flex: 1;
        height: 60px;
        min-width: 60px;
        border-radius: 8px;
        border: 1px solid #333;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        color: rgba(255,255,255,0.8);
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }

    /* PILLS (VALUES & AESTHETICS) - TAILLE AUGMENTÉE */
    .pill-container {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 10px;
    }
    .pill {
        background: rgba(255,255,255,0.08);
        padding: 10px 24px; /* Plus grand padding */
        border-radius: 100px;
        font-size: 1.1rem; /* Police plus grande */
        color: #FFF;
        border: 1px solid #333;
    }

    /* FULLSCREEN LOADER */
    .loader-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: #050505; z-index: 99999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .pulse-text {
        font-family: 'Playfair Display', serif; font-size: 3rem; color: white;
        animation: pulse 1.5s infinite ease-in-out;
    }
    @keyframes pulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }

    /* CLEANUP */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 3. LOGIC: SCRAPING ---
def get_brand_dna(url):
    rules = {
        "projectName": "Brand Name",
        "tagline": "Tagline",
        "industry": "Industry",
        "concept": "Detailed Concept (Max 30 words)",
        "colors": {"description": "Hex colors", "type": "list", "output": {"hex_code": "#Hex"}},
        "aesthetic": {"description": "Aesthetic keywords", "type": "list", "output": {"keyword": "Word"}},
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

# --- 4. LOGIC: STRATEGY (LONGUE) ---
def generate_strategy(dna):
    prompt = f"""
    Role: Luxury Brand Strategist.
    Brand DNA: {json.dumps(dna)}
    
    Task: Create 3 social media campaigns.
    CRITICAL: The 'strategy' field must be DETAILED (at least 60-80 words) explaining the 'why', the audience, and the emotional hook.
    
    Output JSON:
    {{
        "campaigns": [
            {{
                "id": 1,
                "title": "Campaign Title",
                "strategy": "Long detailed strategy text here...",
                "visual_prompt": "High-end commercial photography description: Subject, Lighting, Composition, Texture."
            }}
        ]
    }}
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(res.text)['campaigns']
    except: return []

# --- 5. LOGIC: IMAGE (ROBUSTESSE MAXIMALE) ---
def generate_image_imagen(prompt_text):
    # Endpoint Imagen 4.0 (Predict)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-preview-06-06:predict?key={GOOGLE_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    # Payload simplifié pour éviter les erreurs de paramètres
    payload = {
        "instances": [{"prompt": prompt_text + ", 8k resolution, photorealistic, commercial photography, highly detailed"}],
        "parameters": {"aspectRatio": "4:5", "sampleCount": 1}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            predictions = response.json().get('predictions', [])
            if predictions:
                data = predictions[0]
                # Gestion des formats variables de l'API
                b64 = data.get('bytesBase64Encoded', data) if isinstance(data, dict) else data
                return Image.open(BytesIO(base64.b64decode(b64)))
            else:
                # Si 200 OK mais pas d'image (filtre sécurité souvent)
                print(f"API OK but no image: {response.json()}")
                return None
        else:
            # Erreur HTTP (400, 403, 404, 500)
            print(f"API Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

# --- 6. UI FLOW ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'dna' not in st.session_state: st.session_state.dna = None
if 'campaigns' not in st.session_state: st.session_state.campaigns = None
if 'images' not in st.session_state: st.session_state.images = {}

# --- PAGE 1: LANDING (CENTRÉ VIA HTML) ---
if st.session_state.step == 1:
    
    # Container Flexbox pour centrage parfait
    st.markdown('<div class="landing-container">', unsafe_allow_html=True)
    
    st.markdown("<h1>PROJECT ONE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; margin-bottom: 30px;'>ENTER YOUR WEBSITE. WE GENERATE YOUR BRAND IDENTITY.</p>", unsafe_allow_html=True)
    
    url = st.text_input("URL", placeholder="www.example.com", label_visibility="collapsed")
    
    # Le bouton est géré par le CSS .stButton pour être large et centré
    if st.button("GENERATE IDENTITY"):
        if url:
            st.session_state.url = url if url.startswith('http') else 'https://' + url
            st.session_state.step = 1.5
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- LOADER ---
elif st.session_state.step == 1.5:
    st.markdown("""
    <div class="loader-overlay">
        <div class="pulse-text">PROJECT ONE</div>
        <p style="color:#666; letter-spacing:3px; margin-top:20px;">ANALYZING IDENTITY</p>
    </div>
    """, unsafe_allow_html=True)
    
    dna = get_brand_dna(st.session_state.url)
    if dna:
        st.session_state.dna = dna
        st.session_state.step = 2
        st.rerun()
    else:
        st.error("Impossible d'analyser ce site. Vérifiez l'URL.")
        if st.button("Retour"): st.session_state.step = 1; st.rerun()

# --- PAGE 2: DNA RESULTS ---
elif st.session_state.step == 2:
    dna = st.session_state.dna
    
    st.markdown(f"<p style='text-align:center; font-size:0.9rem; letter-spacing:2px; color:#666;'>IDENTITY EXTRACTED</p>", unsafe_allow_html=True)
    st.markdown(f"<h1>{dna.get('projectName', 'BRAND').upper()}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-size:1.2rem; color:#FFF; max-width:800px; margin:0 auto 40px auto;'>{dna.get('concept')}</p>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Visual Palette</h3><br>", unsafe_allow_html=True)
        
        # Palette HTML Flexbox
        st.markdown('<div class="palette-container">', unsafe_allow_html=True)
        for color in dna.get('colors', [])[:5]:
            c = color.get('hex_code')
            st.markdown(f'<div class="color-box" style="background-color:{c};">{c}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<h3>Aesthetic</h3>", unsafe_allow_html=True)
        st.markdown('<div class="pill-container">', unsafe_allow_html=True)
        for a in dna.get('aesthetic', []):
            st.markdown(f'<div class="pill">{a.get("keyword")}</div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='premium-card' style='height:100%;'>", unsafe_allow_html=True)
        st.markdown("<h3>Core Values</h3>", unsafe_allow_html=True)
        st.markdown('<div class="pill-container">', unsafe_allow_html=True)
        for v in dna.get('values', []):
            st.markdown(f'<div class="pill">{v.get("value")}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Bouton centré via colonnes
    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        if st.button("GENERATE CAMPAIGNS"):
            st.session_state.step = 3
            st.rerun()

# --- PAGE 3: CAMPAIGNS ---
elif st.session_state.step == 3:
    
    if not st.session_state.campaigns:
        st.markdown("""
        <div class="loader-overlay">
            <div class="pulse-text">PROJECT ONE</div>
            <p style="color:#666; letter-spacing:3px; margin-top:20px;">CRAFTING VISUALS</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.campaigns = generate_strategy(st.session_state.dna)
        for camp in st.session_state.campaigns:
            img = generate_image_imagen(camp['visual_prompt'])
            if img: st.session_state.images[camp['id']] = img
        st.rerun()

    st.markdown("<h2>STRATEGIC CAMPAIGNS</h2>", unsafe_allow_html=True)
    
    for camp in st.session_state.campaigns:
        cid = camp['id']
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        
        cols = st.columns([1, 1])
        with cols[0]:
            st.markdown(f"<div style='font-family:Playfair Display; font-size:3rem; color:#333; margin-bottom:10px;'>0{cid}</div>", unsafe_allow_html=True)
            st.markdown(f"<h3>{camp['title']}</h3>", unsafe_allow_html=True)
            # Stratégie plus longue
            st.markdown(f"<p style='color:#CCC; margin-top:15px;'>{camp['strategy']}</p>", unsafe_allow_html=True)
            
            with st.expander("View Prompt Data"):
                st.code(camp['visual_prompt'])

        with cols[1]:
            if cid in st.session_state.images:
                st.image(st.session_state.images[cid], use_container_width=True)
            else:
                # Message d'erreur propre
                st.warning("Image generation failed. (API limit or Filter)")
        
        st.markdown("</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        if st.button("START OVER"):
            st.session_state.clear()
            st.rerun()
