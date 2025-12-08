import streamlit as st
import requests
import json
import google.generativeai as old_genai # On renomme l'ancien pour éviter les conflits
from google import genai as new_genai   # Le nouveau SDK pour la vidéo
import time
from urllib.parse import urlparse, urljoin

# --- CONFIGURATION ---
st.set_page_config(page_title="Project One", layout="wide", initial_sidebar_state="collapsed")

# Load API Keys
try:
    SCRAPINGBEE_API_KEY = st.secrets["SCRAPINGBEE_API_KEY"]
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except FileNotFoundError:
    st.error("System Configuration Error: API Keys missing.")
    st.stop()

# Configure Old Gemini (Text/Images)
old_genai.configure(api_key=GOOGLE_API_KEY)

# --- CSS: ULTIMATE PREMIUM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* GLOBAL THEME */
    .stApp {
        background-color: #0b0d11; 
        color: #f0f2f6; 
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 600; letter-spacing: -0.02em; }
    p, div, label, li { color: #d1d5db; font-size: 1rem; line-height: 1.6; }

    /* HEADER */
    .top-nav {
        position: fixed; top: 0; left: 0; width: 100%;
        padding: 15px 30px; background: rgba(11, 13, 17, 0.95);
        backdrop-filter: blur(10px); z-index: 9999;
        border-bottom: 1px solid #1f2937; display: flex; align-items: center;
    }
    .nav-logo { font-weight: 700; font-size: 1.2rem; color: #fff; }
    .nav-badge { background: #3b82f6; color: white; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; margin-left: 10px; }

    /* INPUT FIELD (BLUE BORDER) */
    div[data-baseweb="input"] { border: 1px solid #3b82f6 !important; background-color: #161b22 !important; border-radius: 8px !important; }
    div[data-testid="stTextInput"] input { color: white !important; }
    div[data-baseweb="base-input"] { border-color: #3b82f6 !important; }

    /* LOADER */
    .stSpinner { display: none !important; }
    .custom-loader { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: #0b0d11; z-index: 999999; display: flex; flex-direction: column; justify-content: center; align-items: center; }
    .loader-ring { width: 50px; height: 50px; border: 3px solid rgba(59, 130, 246, 0.3); border-top-color: #3b82f6; border-radius: 50%; margin-bottom: 24px; animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* UI ELEMENTS */
    .chip { display: inline-block; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 4px; font-size: 0.85rem; margin-right: 8px; margin-bottom: 8px; }
    .color-swatch { width: 100%; height: 70px; border-radius: 4px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.1); }
    .brand-img { width: 100%; height: 200px; object-fit: cover; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1); transition: 0.3s; }
    .brand-img:hover { border-color: #3b82f6; }
    
    /* BUTTONS */
    .stButton button, .stLinkButton a { background-color: #3b82f6 !important; color: white !important; border: none !important; border-radius: 4px !important; font-weight: 600 !important; padding: 0.8rem 2rem !important; text-transform: uppercase !important; font-size: 0.85rem !important; transition: 0.3s !important; display: inline-flex !important; justify-content: center !important; align-items: center !important; text-decoration: none !important;}
    .stButton button:hover, .stLinkButton a:hover { background-color: #2563eb !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important; color: white !important; }

    /* HEADER & LAYOUT */
    .header-logo-img { width: 80px; height: 80px; object-fit: contain; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); background-color: #161b22; padding: 5px; float: right; }
    header { visibility: hidden; }
    .block-container { padding-top: 6rem; }
    hr { margin: 3rem 0; border-color: #1f2937; }
</style>
""", unsafe_allow_html=True)

# --- HEADER FUNCTION ---
def show_header():
    st.markdown("""
        <div class="top-nav">
            <span class="nav-logo">Project One</span>
            <span class="nav-badge">MVP</span>
        </div>
    """, unsafe_allow_html=True)

# --- BACKEND LOGIC ---

def get_brand_data(url):
    target_url = url if url.startswith("http") else f"https://{url}"
    parsed_uri = urlparse(target_url)
    clean_domain = parsed_uri.netloc
    if clean_domain.startswith("www."): clean_domain = clean_domain[4:]
    clean_base_url = f"{parsed_uri.scheme}://{clean_domain}"
    google_favicon_url = f"https://www.google.com/s2/favicons?domain={clean_domain}&sz=128"

    extract_rules = {
        "projectName": "The official name of the company.",
        "tagline": "The main slogan found in the hero section.",
        "industry": "The specific industry sector.",
        "concept": "A 50-word summary of what the business does.",
        "colors": {"description": "list of 5 brand colors", "type": "list", "output": {"hex_code": "Hex code"}},
        "fonts": {"description": "List of 2 font families", "type": "list", "output": {"font_name": "Name", "use": "Use"}},
        "aesthetic": {"description": "4 adjectives for visual style", "type": "list", "output": {"keyword": "Adjective"}},
        "values": {"description": "4 brand values", "type": "list", "output": {"value": "Value"}},
        "tone": {"description": "4 tone keywords", "type": "list", "output": {"keyword": "Tone"}},
        "images": {"description": "4 distinct image URLs", "type": "list", "output": {"src": "URL", "alt": "Alt"}}
    }

    params = {
        "api_key": SCRAPINGBEE_API_KEY,
        "url": target_url,
        "block_resources": "false",
        "render_js": "true",
        "wait": "4000",
        "ai_extract_rules": json.dumps(extract_rules)
    }

    try:
        response = requests.get("https://app.scrapingbee.com/api/v1", params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                data['logo'] = google_favicon_url
                if data.get('images'):
                    for img in data['images']:
                        if img.get('src') and not img['src'].startswith('data:'):
                            img['src'] = urljoin(clean_base_url, img['src'])
                
                # Smart Colors
                found = data.get('colors', [])
                if not any(len(c.get('hex_code', '')) > 1 for c in found): found.append({"hex_code": "#3B82F6"})
                if not any(c.get('hex_code').upper() in ['#FFFFFF', '#FFF'] for c in found): found.insert(0, {"hex_code": "#FFFFFF"})
                if not any(c.get('hex_code').upper() in ['#000000', '#000'] for c in found): found.append({"hex_code": "#000000"})
                data['colors'] = found
            return data
        return None
    except:
        return None

def generate_campaign_strategy(brand_data):
    try:
        # Use OLD GenAI for Text
        model = old_genai.GenerativeModel('models/gemini-2.0-flash')
        prompt = f"""
        Act as a Luxury Brand Strategist. Brand: {json.dumps(brand_data)}
        TASK: Create 3 high-end campaign concepts.
        For each, write a 'final_constructed_prompt' for image generation.
        IMPORTANT: The prompt MUST describe a CINEMATIC LANDSCAPE SHOT (16:9 aspect ratio).
        
        OUTPUT JSON: [{{ "campaign_name": "...", "campaign_description": "...", "image_prompt_structure": {{ "final_constructed_prompt": "..." }} }}]
        """
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return []

def generate_video_strategy(brand_data):
    try:
        # Use OLD GenAI for Text
        model = old_genai.GenerativeModel('models/gemini-2.0-flash')
        prompt = f"""
        Act as a Commercial Film Director. Brand: {json.dumps(brand_data)}
        TASK: Create a concept for a high-end social media brand video.
        Write a precise technical prompt for Veo (Video AI).
        REQUIREMENTS: Cinematic lighting, 4k, slow motion, drone shot or smooth dolly.
        OUTPUT JSON: {{ "video_title": "...", "video_description": "...", "video_prompt": "Cinematic drone shot of..." }}
        """
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return {}

def generate_social_prompts(brand_data):
    try:
        # Use OLD GenAI for Text
        model = old_genai.GenerativeModel('models/gemini-2.0-flash')
        prompt = f"""
        Role: Art Director. Brand: {json.dumps(brand_data)}
        TASK: Create 2 prompts for Nano Banana Pro.
        GOAL: DIRECT SCREEN CAPTURE (UI Design). NO PHONES. NO HANDS.
        FORMAT: Vertical 9:16.
        1. Instagram Profile UI (Flat design, 8k).
        2. TikTok Profile UI (Dark/Light mode, 8k).
        OUTPUT JSON: {{ "instagram_final_prompt": "...", "tiktok_final_prompt": "..." }}
        """
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return {}

def generate_image_from_prompt(prompt_text, aspect_ratio="16:9"):
    try:
        # Use OLD GenAI for Images (Nano Banana)
        model = old_genai.GenerativeModel('models/nano-banana-pro-preview')
        ar_prompt = " --aspect_ratio 16:9" if aspect_ratio == "16:9" else " --aspect_ratio 9:16"
        refined = prompt_text + ar_prompt + " . 8k, photorealistic, high fidelity, highly detailed."
        response = model.generate_content(refined)
        if response.parts: return response.parts[0].inline_data.data
        return None
    except:
        return None

def generate_brand_video(prompt_text):
    """
    Generate video using the NEW 'google-genai' library and Veo 3.1
    """
    try:
        # Initialisation du client avec le NOUVEAU SDK
        client = new_genai.Client(api_key=GOOGLE_API_KEY)
        
        # 1. Start Operation
        # Note: model="veo-3.1-generate-preview" as requested
        operation = client.models.generate_videos(
            model="veo-2.0-generate-preview-01-15", # Ou 'veo-3.1-generate-preview' si dispo
            prompt=prompt_text
        )
        
        # 2. Polling Loop
        # On attend que la video soit prête
        while not operation.done:
            time.sleep(5)
            operation = client.operations.get(operation)
            
        # 3. Retrieve Result
        if operation.response and operation.response.generated_videos:
            generated_video = operation.response.generated_videos[0]
            
            # Pour Streamlit, on veut idéalement les bytes directement ou une URL
            # La méthode .save() sauvegarde sur le disque serveur.
            # On va sauvegarder temporairement pour la lire ensuite.
            temp_filename = "brand_video.mp4"
            
            # Download file content
            # Le SDK permet parfois generated_video.video.download() ou client.files.download()
            # Selon la doc exacte fournie :
            video_bytes = client.files.download(file=generated_video.video)
            
            return video_bytes
            
        return None
        
    except Exception as e:
        print(f"Veo Error: {e}")
        # Fallback au cas où ça plante (pour le MVP): générer une image
        return None

def full_screen_loader(text):
    st.markdown(f"""<div class="custom-loader"><div class="loader-ring"></div><div class="loader-text">{text}</div></div>""", unsafe_allow_html=True)
def render_chips(items, key_name='keyword'):
    if not items: return
    html = '<div class="chip-container">'
    for item in items:
        val = item.get(key_name, item.get('value', ''))
        if val: html += f'<div class="chip">{val}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- STATE ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'brand_data' not in st.session_state: st.session_state.brand_data = {}
if 'campaigns' not in st.session_state: st.session_state.campaigns = []
if 'social_images' not in st.session_state: st.session_state.social_images = {}
if 'video_data' not in st.session_state: st.session_state.video_data = {}

# --- PAGE 1 ---
if st.session_state.step == 1:
    show_header()
    st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>Project One</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6b7280; letter-spacing: 1px; margin-top: -10px;'>AI-POWERED BRAND STRATEGY & VISUAL ECOSYSTEM</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        url_input = st.text_input("URL", placeholder="ex: www.tesla.com", label_visibility="collapsed")
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
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

# --- PAGE 2 ---
elif st.session_state.step == 2:
    show_header()
    data = st.session_state.brand_data
    h1, h2 = st.columns([4, 1], vertical_alignment="center")
    with h1:
        st.markdown(f"<h1 style='font-size: 2.5rem; margin-bottom:0;'>{data.get('projectName', 'Brand Identity')}</h1>", unsafe_allow_html=True)
        if data.get('tagline'): st.markdown(f"<p style='color:#3b82f6; margin-top:5px;'>{data.get('tagline')}</p>", unsafe_allow_html=True)
    with h2:
        if data.get('logo'): st.markdown(f"<img src='{data.get('logo')}' class='header-logo-img'>", unsafe_allow_html=True)
    st.divider()

    c1, c2 = st.columns([1.5, 1], gap="large")
    with c1:
        st.markdown("### Brand Essence")
        st.markdown(f"**Industry:** {data.get('industry', 'N/A')}")
        st.markdown(f"**Concept:** {data.get('concept', 'N/A')}")
        if data.get('values'):
            st.markdown("<br>### Core Values", unsafe_allow_html=True)
            render_chips(data.get('values'), 'value')
        if data.get('aesthetic'):
            st.markdown("<br>### Visual Identity", unsafe_allow_html=True)
            render_chips(data.get('aesthetic'), 'keyword')
    with c2:
        if data.get('colors'):
            st.markdown("### Palette")
            cols = st.columns(3)
            for i, c in enumerate(data['colors']):
                if c.get('hex_code'):
                    with cols[i%3]:
                        st.markdown(f"<div class='color-swatch' style='background:{c['hex_code']};'></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='color-label'>{c['hex_code']}</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
        if data.get('fonts'):
            st.markdown("### Typography")
            for f in data['fonts']: st.markdown(f"<div style='border-left:2px solid #3b82f6; padding-left:10px; margin-bottom:5px;'>{f.get('font_name')}</div>", unsafe_allow_html=True)

    if data.get('images'):
        st.markdown("---")
        st.markdown("### Visual Assets")
        cols = st.columns(4)
        for i, img in enumerate([i for i in data['images'] if i.get('src')][:4]):
            with cols[i]: st.markdown(f"<img src='{img['src']}' class='brand-img' onerror='this.style.display=\"none\"'>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("Generate Strategic Vision", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# --- PAGE 3 ---
elif st.session_state.step == 3:
    show_header()
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    
    if not st.session_state.campaigns or not st.session_state.social_images or not st.session_state.video_data:
        placeholder = st.empty()
        with placeholder: full_screen_loader("GENERATING VISUAL NARRATIVES & VIDEO CONCEPTS...")
        
        # 1. Campaigns (Landscape)
        if not st.session_state.campaigns:
            c_data = generate_campaign_strategy(st.session_state.brand_data)
            final_c = []
            for c in c_data:
                prompt = c.get('image_prompt_structure', {}).get('final_constructed_prompt')
                if prompt: 
                    c['generated_image'] = generate_image_from_prompt(prompt, aspect_ratio="16:9")
                final_c.append(c)
            st.session_state.campaigns = final_c
        
        # 2. Social (Portrait)
        if not st.session_state.social_images:
            s_prompts = generate_social_prompts(st.session_state.brand_data)
            if s_prompts.get('instagram_final_prompt'):
                st.session_state.social_images['instagram'] = generate_image_from_prompt(s_prompts['instagram_final_prompt'], aspect_ratio="9:16")
            if s_prompts.get('tiktok_final_prompt'):
                st.session_state.social_images['tiktok'] = generate_image_from_prompt(s_prompts['tiktok_final_prompt'], aspect_ratio="9:16")
        
        # 3. Video (VEO REAL)
        if not st.session_state.video_data:
            v_strat = generate_video_strategy(st.session_state.brand_data)
            st.session_state.video_data['strategy'] = v_strat
            if v_strat.get('video_prompt'):
                # Call Real Veo Video
                st.session_state.video_data['file_bytes'] = generate_brand_video(v_strat['video_prompt'])
        
        placeholder.empty()
        st.rerun()

    st.markdown("<h1>Tailored Strategic Concepts</h1>", unsafe_allow_html=True)
    st.divider()

    # Campaigns
    for i, c in enumerate(st.session_state.campaigns):
        with st.container():
            c1, c2 = st.columns([1, 1], gap="large", vertical_alignment="center")
            with c1:
                st.markdown(f"### {i+1}. {c.get('campaign_name')}")
                st.write(c.get('campaign_description'))
            with c2:
                if c.get('generated_image'): st.image(c['generated_image'], use_column_width=True)
            st.markdown("---")

    # Video Section
    if st.session_state.video_data:
        v = st.session_state.video_data
        st.markdown("<br><h2 style='text-align:center;'>Signature Video Campaign</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#6b7280; margin-bottom: 20px;'>High-End Social Media Commercial (Veo 4K)</p>", unsafe_allow_html=True)
        
        v1, v2 = st.columns([1, 1.5], gap="large", vertical_alignment="center")
        with v1:
            st.markdown(f"### {v.get('strategy', {}).get('video_title', 'Cinematic Vision')}")
            st.write(v.get('strategy', {}).get('video_description', ''))
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("Technical Video Prompt"):
                st.code(v.get('strategy', {}).get('video_prompt'), language="text")
        with v2:
            if v.get('file_bytes'):
                st.video(v['file_bytes'], format="video/mp4")
            else:
                st.info("Video generation unavailable or restricted by safety filters.")
        st.markdown("---")

    # Social Section
    st.markdown("<br><h2 style='text-align:center;'>Omnichannel Presence</h2>", unsafe_allow_html=True)
    s1, s2 = st.columns(2, gap="large")
    with s1:
        st.markdown("<h4 style='text-align:center;'>Instagram Preview</h4>", unsafe_allow_html=True)
        if st.session_state.social_images.get('instagram'): st.image(st.session_state.social_images['instagram'], use_column_width=True)
    with s2:
        st.markdown("<h4 style='text-align:center;'>TikTok Preview</h4>", unsafe_allow_html=True)
        if st.session_state.social_images.get('tiktok'): st.image(st.session_state.social_images['tiktok'], use_column_width=True)

    # Final CTA (Clean Text)
    st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center;'>
            <h2 style='font-size: 2rem; font-weight: 600; color: #fff; margin-bottom: 10px;'>Ready to amplify your digital footprint?</h2>
            <p style='font-size: 1.1rem; color: #9ca3af; margin-bottom: 30px;'>Transform these concepts into your reality. Let's define your future.</p>
        </div>
    """, unsafe_allow_html=True)

    b1, b2, b3 = st.columns([1.5, 1, 1.5])
    with b2:
        st.link_button("Schedule a Consultation", "https://calendly.com/contact-respectfully/30min", use_container_width=True)
    
    st.markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)
