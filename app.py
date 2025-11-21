import streamlit as st
import requests
import json
import google.generativeai as genai
import base64
from PIL import Image
from io import BytesIO
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Project One",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SCRAPINGBEE_API_KEY = st.secrets.get("SCRAPINGBEE_API_KEY", "")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")

genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. DESIGN SYSTEM "SILICON VALLEY" ---
def inject_custom_css():
    st.markdown("""
    <style>
    /* IMPORT FONT INTER (Standard Tech) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-app: #0C0E14; /* Dark Blue/Black Deep */
        --surface: #151923;
        --surface-hover: #1E2330;
        --primary: #3B82F6; /* Tech Blue */
        --primary-hover: #2563EB;
        --text-main: #F9FAFB;
        --text-muted: #9CA3AF;
        --border: #2D3342;
        --radius: 8px;
        --radius-lg: 12px;
    }

    /* RESET & BASE */
    .stApp {
        background-color: var(--bg-app);
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
    }
    
    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em;
        color: var(--text-main) !important;
    }
    
    p, div, span, label {
        color: var(--text-muted);
        font-weight: 400;
    }

    /* INPUTS (Modern SaaS Style) */
    .stTextInput > div > div > input {
        background-color: var(--surface);
        color: var(--text-main);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 12px 16px;
        font-size: 1rem;
        transition: all 0.2s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
        background-color: var(--bg-app);
    }

    /* BUTTONS (Primary Action) */
    .stButton > button {
        background-color: var(--primary);
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: var(--radius);
        padding: 10px 24px;
        font-weight: 500;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: var(--primary-hover);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        border-color: rgba(255,255,255,0.2);
    }
    .stButton > button:active {
        transform: translateY(1px);
    }

    /* CARDS & CONTAINERS */
    .tech-card {
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 24px;
        margin-bottom: 20px;
        transition: border-color 0.2s ease;
    }
    .tech-card:hover {
        border-color: #4B5563;
    }

    /* BADGES / PILLS */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: rgba(59, 130, 246, 0.1);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.2);
        margin-right: 8px;
        margin-bottom: 8px;
    }

    /* COLORS DISPLAY */
    .color-swatch {
        width: 100%;
        height: 40px;
        border-radius: 6px;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 8px;
    }
    .color-label {
        font-family: 'Inter', monospace;
        font-size: 0.75rem;
        color: var(--text-muted);
        text-align: center;
    }

    /* FULLSCREEN LOADER */
    .fullscreen-loader {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: var(--bg-app);
        z-index: 999999;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(10px);
    }
    .loader-spinner {
        width: 40px; height: 40px;
        border: 3px solid rgba(59, 130, 246, 0.3);
        border-radius: 50%;
        border-top-color: var(--primary);
        animation: spin 1s ease-in-out infinite;
        margin-bottom: 20px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* UTILS */
    .text-center { text-align: center; }
    .mb-4 { margin-bottom: 1.5rem; }
    .text-sm { font-size: 0.875rem; }
    
    /* CLEANUP STREAMLIT UI */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 4rem; padding-bottom: 5rem; }
    
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 3. LOGIC: SCRAPING ---
def get_brand_dna(url):
    rules = {
        "projectName": "Brand Name",
        "tagline": "Tagline",
        "industry": "Industry",
        "concept": "Short Concept (Max 20 words)",
        "colors": {"description": "Hex colors", "type": "list", "output": {"hex_code": "#Hex"}},
        "aesthetic": {"description": "Aesthetic keywords", "type": "list", "output": {"keyword": "Word"}},
        "values": {"description": "Brand values", "type": "list", "output": {"value": "Value"}}
    }
    params = {
        'api_key': SCRAPINGBEE_API_KEY, 'url': url, 'render_js': 'true',
        'ai_extract_rules': json.dumps(rules), 'premium_proxy': 'true', 'wait': '2000'
    }
    try:
        response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, timeout=45)
        return response.json() if response.status_code == 200 else None
    except: return None

# --- 4. LOGIC: STRATEGY ---
def generate_strategy(dna):
    prompt = f"""
    Role: Tech/Startup Marketing Strategist.
    Brand DNA: {json.dumps(dna)}
    Task: Create 3 modern social media campaign concepts.
    Format: JSON list 'campaigns' with id, title, strategy (1 sentence), visual_prompt (detailed commercial photography description).
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(res.text)['campaigns']
    except: return []

# --- 5. LOGIC: IMAGE (IMAGEN 4.0 FIX) ---
def generate_image_imagen(prompt_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-preview-06-06:predict?key={GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [{"prompt": prompt_text + ", 8k, photorealistic, highly detailed, commercial photography"}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:5"}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            predictions = response.json().get('predictions', [])
            if predictions:
                b64 = predictions[0].get('bytesBase64Encoded', predictions[0]) if isinstance(predictions[0], dict) else predictions[0]
                return Image.open(BytesIO(base64.b64decode(b64)))
        return None
    except: return None

# --- 6. UI FLOW ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'dna' not in st.session_state: st.session_state.dna = None
if 'campaigns' not in st.session_state: st.session_state.campaigns = None
if 'images' not in st.session_state: st.session_state.images = {}

# --- PAGE 1: INPUT ---
if st.session_state.step == 1:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1 class='text-center'>Project One</h1>", unsafe_allow_html=True)
        st.markdown("<p class='text-center mb-4'>Enter a website URL to generate a complete brand identity and content strategy.</p>", unsafe_allow_html=True)
        
        url = st.text_input("Website URL", placeholder="example.com", label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Generate Identity"):
            if url:
                st.session_state.url = url if url.startswith('http') else 'https://' + url
                st.session_state.step = 1.5
                st.rerun()

# --- LOADING: FULL SCREEN ---
elif st.session_state.step == 1.5:
    st.markdown("""
    <div class="fullscreen-loader">
        <div class="loader-spinner"></div>
        <h3 style="margin:0;">Analyzing Brand</h3>
        <p>Extracting DNA & Visual Codes...</p>
    </div>
    """, unsafe_allow_html=True)
    
    dna = get_brand_dna(st.session_state.url)
    if dna:
        st.session_state.dna = dna
        st.session_state.step = 2
        st.rerun()
    else:
        st.error("Could not analyze this URL.")
        if st.button("Back"): st.session_state.step = 1; st.rerun()

# --- PAGE 2: DASHBOARD ---
elif st.session_state.step == 2:
    dna = st.session_state.dna
    
    st.markdown(f"<p class='text-center text-sm'>IDENTITY EXTRACTED</p>", unsafe_allow_html=True)
    st.markdown(f"<h1 class='text-center'>{dna.get('projectName', 'Brand Name')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='text-center' style='font-size: 1.1rem; color: #fff;'>{dna.get('tagline')}</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Visual Identity</h3><br>", unsafe_allow_html=True)
        
        # Colors
        st.markdown("<p class='text-sm'>PALETTE</p>", unsafe_allow_html=True)
        cols = st.columns(5)
        for color in dna.get('colors', [])[:5]:
            with cols[dna.get('colors').index(color) % 5]:
                st.markdown(f"<div class='color-swatch' style='background-color:{color.get('hex_code')}'></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='color-label'>{color.get('hex_code')}</div>", unsafe_allow_html=True)

        st.markdown("<br><p class='text-sm'>AESTHETIC</p>", unsafe_allow_html=True)
        for a in dna.get('aesthetic', []):
            st.markdown(f"<span class='badge'>{a.get('keyword')}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='tech-card' style='height:100%;'>", unsafe_allow_html=True)
        st.markdown("<h3>Core Strategy</h3><br>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #E5E7EB; line-height: 1.6;'>{dna.get('concept')}</p>", unsafe_allow_html=True)
        
        st.markdown("<br><p class='text-sm'>VALUES</p>", unsafe_allow_html=True)
        for v in dna.get('values', []):
            st.markdown(f"<span class='badge' style='color: #A78BFA; background: rgba(139, 92, 246, 0.1); border-color: rgba(139, 92, 246, 0.2);'>{v.get('value')}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        if st.button("Generate Campaigns"):
            st.session_state.step = 3
            st.rerun()

# --- PAGE 3: CAMPAIGNS ---
elif st.session_state.step == 3:
    
    # Loader Logic
    if not st.session_state.campaigns:
        st.markdown("""
        <div class="fullscreen-loader">
            <div class="loader-spinner"></div>
            <h3 style="margin:0;">Generating Content</h3>
            <p>Crafting strategy & Rendering visuals...</p>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.campaigns = generate_strategy(st.session_state.dna)
        for camp in st.session_state.campaigns:
            img = generate_image_imagen(camp['visual_prompt'])
            if img: st.session_state.images[camp['id']] = img
        st.rerun()

    st.markdown("<h2 class='text-center mb-4'>Strategic Campaigns</h2>", unsafe_allow_html=True)

    for camp in st.session_state.campaigns:
        cid = camp['id']
        st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
        
        cols = st.columns([1, 1])
        with cols[0]:
            st.markdown(f"<div class='badge'>CAMPAIGN 0{cid}</div>", unsafe_allow_html=True)
            st.markdown(f"<h3>{camp['title']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='margin-top:1rem; line-height:1.6;'>{camp['strategy']}</p>", unsafe_allow_html=True)
            
            with st.expander("View Visual Prompt"):
                st.code(camp['visual_prompt'], language="text")

        with cols[1]:
            if cid in st.session_state.images:
                st.image(st.session_state.images[cid], use_container_width=True)
            else:
                st.warning("Visual rendering unavailable.")
        
        st.markdown("</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        if st.button("Start Over"):
            st.session_state.clear()
            st.rerun()
