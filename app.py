import streamlit as st
import requests
import json
import google.generativeai as genai
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Project One", layout="wide", initial_sidebar_state="collapsed")

# Load API Keys
try:
    SCRAPINGBEE_API_KEY = st.secrets["SCRAPINGBEE_API_KEY"]
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except FileNotFoundError:
    st.error("System Configuration Error: API Keys missing.")
    st.stop()

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# --- CSS: PREMIUM & LEGIBILITY ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* --- GLOBAL DARK THEME --- */
    .stApp {
        background-color: #0b0d11; /* Deep Obsidian */
        color: #f0f2f6;
        font-family: 'Inter', sans-serif;
    }
    
    /* --- TYPOGRAPHY --- */
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    p, div, label, li {
        color: #d1d5db;
        font-size: 1rem;
        line-height: 1.6;
    }

    /* --- HEADER (PROJECT ONE) --- */
    .top-nav {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        padding: 15px 30px;
        background: rgba(11, 13, 17, 0.95);
        backdrop-filter: blur(10px);
        z-index: 9999;
        border-bottom: 1px solid #1f2937;
        display: flex;
        align-items: center;
    }
    .nav-logo {
        font-weight: 700;
        font-size: 1.2rem;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    .nav-badge {
        background: #3b82f6;
        color: white;
        font-size: 0.7rem;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 10px;
        text-transform: uppercase;
        font-weight: 600;
    }

    /* --- INPUT FIELD --- */
    div[data-baseweb="input"] {
        border: 1px solid #3b82f6 !important;
        background-color: #161b22 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stTextInput"] input {
        color: white !important;
    }

    /* --- FULL SCREEN LOADER --- */
    .stSpinner { display: none !important; }
    
    .custom-loader {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: #0b0d11;
        z-index: 999999;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .loader-ring {
        width: 50px;
        height: 50px;
        border: 3px solid rgba(59, 130, 246, 0.3);
        border-top-color: #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 24px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    
    /* --- UI ELEMENTS --- */
    .chip {
        display: inline-block;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 0.85rem;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .color-swatch {
        width: 100%;
        height: 70px;
        border-radius: 4px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .brand-img {
        width: 100%;
        height: 180px;
        object-fit: cover;
        border-radius: 4px;
        border: 1px solid rgba(255,255,255,0.1);
        transition: opacity 0.3s;
    }
    .brand-img:hover { border-color: #3b82f6; }

    /* --- BUTTONS --- */
    .stButton button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        padding: 0.8rem 2rem;
        text-transform: uppercase;
        font-size: 0.85rem;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #2563eb;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    /* Hide Streamlit Header */
    header {visibility: hidden;}
    
    /* Adjust top padding because of fixed header */
    .block-container {
        padding-top: 6rem;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER: TOP NAV ---
def show_header():
    st.markdown("""
        <div class="top-nav">
            <span class="nav-logo">Project One</span>
            <span class="nav-badge">Beta</span>
        </div>
    """, unsafe_allow_html=True)

# --- BACKEND LOGIC ---

def get_brand_data(url):
    target_url = url if url.startswith("http") else f"https://{url}"
    extract_rules = {
        "projectName": "the company or brand name",
        "tagline": "the website's main slogan or tagline",
        "industry": "the business's industry or sector",
        "concept": "short 50-word summary of business",
        "colors": {"type": "list", "output": {"hex_code": "hex format"}},
        "fonts": {"type": "list", "output": {"font_name": "name", "use": "usage"}},
        "aesthetic": {"type": "list", "output": {"keyword": "keyword"}},
        "values": {"type": "list", "output": {"value": "brand value"}},
        "tone": {"type": "list", "output": {"keyword": "tone keyword"}},
        "images": {"type": "list", "output": {"src": "image url"}}
    }
    params = {
        "api_key": SCRAPINGBEE_API_KEY,
        "url": target_url,
        "block_resources": "false",
        "wait": "3000", 
        "ai_extract_rules": json.dumps(extract_rules)
    }
    try:
        return requests.get("https://app.scrapingbee.com/api/v1", params=params).json()
    except:
        return None

def generate_campaign_strategy(brand_data):
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        # PROMPT UPDATED FOR LANDSCAPE (16:9)
        prompt = f"""
        Act as a Luxury Brand Strategist. Brand Profile: {json.dumps(brand_data)}
        TASK: Create 3 high-end campaign concepts. 
        
        For each, write a 'final_constructed_prompt' for image generation.
        IMPORTANT: The image prompt must describe a CINEMATIC LANDSCAPE SHOT (16:9 aspect ratio).
        Do NOT describe a phone screen. Describe a lifestyle or artistic commercial shot.

        OUTPUT JSON:
        [
          {{
            "campaign_name": "Title", 
            "campaign_description": "Summary (30 words).", 
            "image_prompt_structure": {{ "final_constructed_prompt": "Subject: Wide cinematic shot of [Scene Description] related to [Brand]..." }} 
          }}
        ]
        """
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return []

def generate_social_prompts(brand_data):
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        # PROMPT FOR PORTRAIT (9:16) UI MOCKUPS
        prompt = f"""
        Role: Senior Art Director. Brand Data: {json.dumps(brand_data)}
        TASK: Generate 2 highly detailed image prompts for Nano Banana Pro.
        
        GOAL: Create a DIRECT SCREEN CAPTURE (UI Design).
        CONSTRAINT: NO PHONE HARDWARE. JUST THE UI.
        FORMAT: Vertical 9:16.
        
        1. Instagram Profile UI:
           - Subject: Direct full-screen UI design of the Instagram profile page for '{brand_data.get('projectName')}'.
           - Details: Bio, Highlights circles {brand_data.get('colors')}, 3-column grid.
           - Style: Flat design, Digital Interface, 8k resolution.

        2. TikTok Profile UI:
           - Subject: Direct full-screen UI design of the TikTok profile page for '{brand_data.get('projectName')}'.
           - Details: User handle, 'Edit Profile' button, 3-column video grid.
           - Style: Digital Interface, 8k resolution.

        OUTPUT JSON:
        {{
            "instagram_final_prompt": "...",
            "tiktok_final_prompt": "..."
        }}
        """
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return {}

def generate_image_from_prompt(prompt_text, aspect_ratio="16:9"):
    """Nano Banana Pro Image Generation with Dynamic Aspect Ratio."""
    try:
        model = genai.GenerativeModel('models/nano-banana-pro-preview')
        
        # Inject aspect ratio instruction into the text prompt for the model
        if aspect_ratio == "16:9":
            refined_prompt = prompt_text + " . Cinematic Lighting, Wide Angle, 16:9 Aspect Ratio, High Resolution Photography."
        else:
            refined_prompt = prompt_text + " . Full Screen UI, No Bezels, 9:16 Aspect Ratio, High Fidelity Digital Art."

        response = model.generate_content(refined_prompt)
        if response.parts:
            return response.parts[0].inline_data.data
        return None
    except:
        return None

def render_chips(items, key_name='keyword'):
    if not items: return
    html = "<div>"
    for item in items:
        val = item.get(key_name, item.get('value', ''))
        if val: html += f"<span class='chip'>{val}</span>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def full_screen_loader(text):
    st.markdown(f"""<div class="custom-loader"><div class="loader-ring"></div><div style='color:#6b7280; letter-spacing:2px; font-size:0.9rem;'>{text}</div></div>""", unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'brand_data' not in st.session_state: st.session_state.brand_data = {}
if 'campaigns' not in st.session_state: st.session_state.campaigns = []
if 'social_images' not in st.session_state: st.session_state.social_images = {}

# --- PAGE 1: INPUT ---
if st.session_state.step == 1:
    show_header()
    
    # Spacer for vertical center
    st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom:10px;'>Project One</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 1.1rem; letter-spacing: 0.5px;'>AI-Powered Brand Strategy & Visual Ecosystem</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        url_input = st.text_input("URL", placeholder="ex: www.tesla.com", label_visibility="collapsed")
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        if st.button("Start Analysis", use_container_width=True):
            if url_input:
                placeholder = st.empty()
                with placeholder: full_screen_loader("DECODING BRAND DNA...")
                data = get_brand_data(url_input)
                placeholder.empty()
                if data:
                    st.session_state.brand_data = data
                    st.session_state.step = 2
                    st.rerun()

# --- PAGE 2: DASHBOARD ---
elif st.session_state.step == 2:
    show_header()
    data = st.session_state.brand_data
    
    st.markdown(f"<h1>{data.get('projectName', 'Brand Identity')}</h1>", unsafe_allow_html=True)
    if data.get('tagline'): st.markdown(f"<p style='color: #3b82f6; margin-top:-10px;'>{data.get('tagline')}</p>", unsafe_allow_html=True)
    st.divider()

    c1, c2 = st.columns([1.5, 1], gap="large")
    with c1:
        st.markdown("### Brand Essence")
        st.markdown(f"**Industry:** <span style='color:#fff'>{data.get('industry', 'N/A')}</span>", unsafe_allow_html=True)
        st.markdown(f"**Concept:** <span style='color:#fff'>{data.get('concept', 'N/A')}</span>", unsafe_allow_html=True)
        
        if data.get('values'):
            st.markdown("<br>### Values", unsafe_allow_html=True)
            render_chips(data.get('values'), 'value')
        if data.get('tone'):
            st.markdown("<br>### Tone", unsafe_allow_html=True)
            render_chips(data.get('tone'), 'keyword')

    with c2:
        if data.get('colors'):
            st.markdown("### Palette")
            cols = st.columns(3)
            for i, c in enumerate(data['colors']):
                hex = c.get('hex_code')
                if hex:
                    with cols[i%3]:
                        st.markdown(f"<div style='background:{hex}; height:60px; border-radius:4px; border:1px solid #333;'></div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='font-size:0.7em; color:#888; text-align:center;'>{hex}</div>", unsafe_allow_html=True)
        
        if data.get('fonts'):
            st.markdown("<br>### Typography", unsafe_allow_html=True)
            for f in data['fonts']:
                st.markdown(f"<div style='border-left:2px solid #3b82f6; padding-left:10px; margin-bottom:5px;'>{f.get('font_name')}</div>", unsafe_allow_html=True)

    if data.get('images'):
        st.markdown("---")
        st.markdown("### Visual Assets")
        valid_imgs = [x.get('src') for x in data['images'] if x.get('src')]
        cols = st.columns(4)
        for i, url in enumerate(valid_imgs[:4]):
            with cols[i]:
                st.markdown(f"<img src='{url}' class='brand-img' onerror='this.style.display=\"none\"'>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("Generate Strategic Vision", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# --- PAGE 3: STRATEGY ---
elif st.session_state.step == 3:
    show_header()
    
    # Generation Logic
    if not st.session_state.campaigns or not st.session_state.social_images:
        placeholder = st.empty()
        with placeholder: full_screen_loader("GENERATING VISUAL NARRATIVES...")
        
        # 1. Campaigns (Landscape)
        if not st.session_state.campaigns:
            c_data = generate_campaign_strategy(st.session_state.brand_data)
            final_c = []
            for c in c_data:
                prompt = c.get('image_prompt_structure', {}).get('final_constructed_prompt')
                if prompt: 
                    # Force 16:9 for Campaigns
                    c['generated_image'] = generate_image_from_prompt(prompt, aspect_ratio="16:9")
                final_c.append(c)
            st.session_state.campaigns = final_c
            
        # 2. Social (Portrait)
        if not st.session_state.social_images:
            s_prompts = generate_social_prompts(st.session_state.brand_data)
            if s_prompts.get('instagram_final_prompt'):
                # Force 9:16 for Social
                st.session_state.social_images['instagram'] = generate_image_from_prompt(s_prompts['instagram_final_prompt'], aspect_ratio="9:16")
            if s_prompts.get('tiktok_final_prompt'):
                st.session_state.social_images['tiktok'] = generate_image_from_prompt(s_prompts['tiktok_final_prompt'], aspect_ratio="9:16")
        
        placeholder.empty()
        st.rerun()

    # Top Anchor
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    
    st.markdown("<h1>Strategic Concepts</h1>", unsafe_allow_html=True)
    st.divider()

    # Campaigns
    for i, camp in enumerate(st.session_state.campaigns):
        with st.container():
            c1, c2 = st.columns([1, 1], gap="large", vertical_alignment="center")
            with c1:
                st.markdown(f"### {i+1}. {camp.get('campaign_name')}")
                st.write(camp.get('campaign_description'))
            with c2:
                if camp.get('generated_image'):
                    st.image(camp['generated_image'], use_column_width=True)
                else:
                    st.info("Visualization unavailable")
            st.markdown("---")

    # Social Ecosystem
    st.markdown("<br><h2 style='text-align:center;'>Omnichannel Presence</h2>", unsafe_allow_html=True)
    
    s1, s2 = st.columns(2, gap="large")
    with s1:
        st.markdown("<h4 style='text-align:center; margin-bottom:15px; font-size:1.1rem;'>Instagram Preview</h4>", unsafe_allow_html=True)
        if st.session_state.social_images.get('instagram'):
            st.image(st.session_state.social_images['instagram'], use_column_width=True)
    with s2:
        st.markdown("<h4 style='text-align:center; margin-bottom:15px; font-size:1.1rem;'>TikTok Preview</h4>", unsafe_allow_html=True)
        if st.session_state.social_images.get('tiktok'):
            st.image(st.session_state.social_images['tiktok'], use_column_width=True)

    # Final Button (Solitary)
    st.markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)
    
    # --- AJOUT DU CTA TEXTE SIMPLE ---
    st.markdown("""
        <div style='text-align: center; color: #ffffff; font-size: 1.2rem; font-weight: 500; margin-bottom: 15px;'>
            Ready to elevate your digital footprint?
        </div>
        <div style='text-align: center; color: #9ca3af; font-size: 0.95rem; margin-bottom: 25px;'>
            Let's turn these concepts into your reality.
        </div>
    """, unsafe_allow_html=True)
    # ---------------------------------

    b1, b2, b3 = st.columns([1.5, 1, 1.5])
    with b2:
        st.button("Schedule a Consultation", use_container_width=True)
    
    st.markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)
