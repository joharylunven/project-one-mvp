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

# --- CSS: PREMIUM UI & LAYOUT FIXES ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* --- GLOBAL THEME --- */
    .stApp {
        background-color: #0b0d11; /* Deep Obsidian */
        color: #f0f2f6;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 600;
        letter-spacing: -0.03em;
    }
    
    p, li, label {
        color: #cfd4da;
        font-weight: 400;
        line-height: 1.6;
    }

    /* --- PAGE 1 VERTICAL CENTERING --- */
    /* Creates a flex container for the input page */
    .vertical-center-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 80vh; /* Takes up most of the viewport */
        width: 100%;
    }

    /* --- INPUT FIELD STYLING (BLUE BORDER) --- */
    /* Force override of Streamlit's default red/gray borders */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        border-color: #3b82f6 !important; /* Project One Blue */
        background-color: #161b22;
        border-radius: 8px;
    }
    
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
        border-color: #3b82f6 !important;
    }
    
    input {
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
        width: 40px;
        height: 40px;
        border: 3px solid rgba(59, 130, 246, 0.3);
        border-top-color: #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    
    .loader-text {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #6b7280;
    }

    /* --- IMAGES & MOCKUPS --- */
    .social-mockup {
        width: 100%;
        aspect-ratio: 9 / 16;
        object-fit: cover;
        border-radius: 12px;
        border: 1px solid #1f2937;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    .brand-img {
        width: 100%;
        height: 150px;
        object-fit: cover;
        border-radius: 6px;
        opacity: 0.8;
        transition: opacity 0.3s;
    }
    .brand-img:hover { opacity: 1; }

    /* --- CHIPS & TAGS --- */
    .chip {
        display: inline-block;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    /* --- CTA SECTION --- */
    .cta-box {
        background-color: #111318; /* Flat dark, no weird gradient */
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 50px 20px;
        text-align: center;
        margin-top: 60px;
    }
    
    /* --- BUTTONS --- */
    .stButton button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        padding: 0.8rem 2rem;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #2563eb;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
</style>
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
        prompt = f"""
        Role: Luxury Brand Strategist. Brand Data: {json.dumps(brand_data)}
        Task: Create 3 campaign concepts.
        Output JSON: [{{
            "campaign_name": "Title", 
            "campaign_description": "Summary", 
            "image_prompt_structure": {{ "final_constructed_prompt": "Subject: 9:16 Direct screen UI design of Instagram Profile for [Brand]..." }} 
        }}]
        """
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return []

def generate_social_prompts(brand_data):
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        # PROMPT UPDATED FOR "UI ONLY" - NO PHONES, NO HANDS
        prompt = f"""
        Role: Senior Art Director. Brand Data: {json.dumps(brand_data)}
        
        Task: Generate 2 highly detailed image prompts for Nano Banana Pro.
        GOAL: Create a DIRECT SCREEN CAPTURE (UI Design) of social media profiles.
        CONSTRAINT: NO PHONE HARDWARE, NO HANDS, NO BEZELS, NO BACKGROUND. JUST THE UI INTERFACE.
        FORMAT: Vertical 9:16.
        
        1. Instagram Profile UI:
           - Subject: Direct full-screen UI design of the Instagram profile page for '{brand_data.get('projectName')}'.
           - Details: Professional Bio, Highlights circles matching brand colors {brand_data.get('colors')}, 3-column grid with high-end photography.
           - Style: Flat design, Digital Interface, 8k resolution, Figma export style.

        2. TikTok Profile UI:
           - Subject: Direct full-screen UI design of the TikTok profile page for '{brand_data.get('projectName')}'.
           - Details: User handle, 'Edit Profile' button, 3-column video grid with viral-style thumbnails.
           - Style: Dark/Light mode adapted to brand, Digital Interface, 8k resolution.

        Output JSON: {{ "instagram_final_prompt": "...", "tiktok_final_prompt": "..." }}
        """
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return {}

def generate_image_from_prompt(prompt_text):
    try:
        model = genai.GenerativeModel('models/nano-banana-pro-preview')
        # Enforcing UI keywords in the final call just in case
        refined_prompt = prompt_text + " . Digital UI Design, Full Screen Interface, No Phone Bezel, No Background, 9:16 Aspect Ratio, High Fidelity."
        response = model.generate_content(refined_prompt)
        if response.parts: return response.parts[0].inline_data.data
        return None
    except:
        return None

def render_chips(items, key='keyword'):
    if not items: return
    html = "<div>"
    for i in items:
        v = i.get(key, i.get('value'))
        if v: html += f"<span class='chip'>{v}</span>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def full_screen_loader(text):
    st.markdown(f"""<div class="custom-loader"><div class="loader-ring"></div><div class="loader-text">{text}</div></div>""", unsafe_allow_html=True)

# --- STATE ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'brand_data' not in st.session_state: st.session_state.brand_data = {}
if 'campaigns' not in st.session_state: st.session_state.campaigns = []
if 'social_images' not in st.session_state: st.session_state.social_images = {}

# --- PAGE 1: INPUT (VERTICALLY CENTERED) ---
if st.session_state.step == 1:
    # Container for vertical centering
    st.markdown('<div class="vertical-center-container">', unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 0;'>Project One</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6b7280; letter-spacing: 2px; font-size: 0.9rem; margin-top: 10px;'>BESPOKE BRAND INTELLIGENCE</p>", unsafe_allow_html=True)
    
    # Centered Input Block
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        url_input = st.text_input("URL", placeholder="ex: www.spacex.com", label_visibility="collapsed")
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        if st.button("Analyze Identity", use_container_width=True):
            if url_input:
                placeholder = st.empty()
                with placeholder: full_screen_loader("Decoding Digital Footprint...")
                data = get_brand_data(url_input)
                placeholder.empty()
                if data:
                    st.session_state.brand_data = data
                    st.session_state.step = 2
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True) # End vertical container

# --- PAGE 2: DASHBOARD ---
elif st.session_state.step == 2:
    data = st.session_state.brand_data
    
    st.markdown(f"<h1>{data.get('projectName', 'Identity')}</h1>", unsafe_allow_html=True)
    if data.get('tagline'): st.markdown(f"<p style='color: #3b82f6;'>{data.get('tagline')}</p>", unsafe_allow_html=True)
    st.divider()

    c1, c2 = st.columns([1.5, 1], gap="large")
    with c1:
        st.markdown("### Brand Essence")
        st.markdown(f"**Industry:** {data.get('industry', 'N/A')}")
        st.markdown(f"**Concept:** {data.get('concept', 'N/A')}")
        
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
        valid_imgs = [x.get('src') for x in data['images'] if x.get('src')]
        if valid_imgs:
            st.markdown("### Visual Assets")
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

# --- PAGE 3: STRATEGY (SCROLL TOP) ---
elif st.session_state.step == 3:
    
    # Logic: Generate if missing
    if not st.session_state.campaigns or not st.session_state.social_images:
        placeholder = st.empty()
        with placeholder: full_screen_loader("Synthesizing Strategies & Rendering UI Mockups...")
        
        if not st.session_state.campaigns:
            c_data = generate_campaign_strategy(st.session_state.brand_data)
            final_c = []
            for c in c_data:
                prompt = c.get('image_prompt_structure', {}).get('final_constructed_prompt')
                if prompt: c['generated_image'] = generate_image_from_prompt(prompt)
                final_c.append(c)
            st.session_state.campaigns = final_c
            
        if not st.session_state.social_images:
            s_prompts = generate_social_prompts(st.session_state.brand_data)
            if s_prompts.get('instagram_final_prompt'):
                st.session_state.social_images['instagram'] = generate_image_from_prompt(s_prompts['instagram_final_prompt'])
            if s_prompts.get('tiktok_final_prompt'):
                st.session_state.social_images['tiktok'] = generate_image_from_prompt(s_prompts['tiktok_final_prompt'])
        
        placeholder.empty()
        st.rerun()

    # Anchor to top
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
    st.markdown("<br><h2 style='text-align:center;'>Social Ecosystem</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; margin-bottom:40px;'>High-fidelity UI Visualization</p>", unsafe_allow_html=True)
    
    s1, s2 = st.columns(2, gap="large")
    with s1:
        st.markdown("<h4 style='text-align:center; margin-bottom:15px;'>Instagram Preview</h4>", unsafe_allow_html=True)
        if st.session_state.social_images.get('instagram'):
            # Display strict 9:16 mockup
            st.image(st.session_state.social_images['instagram'], use_column_width=True)
    with s2:
        st.markdown("<h4 style='text-align:center; margin-bottom:15px;'>TikTok Preview</h4>", unsafe_allow_html=True)
        if st.session_state.social_images.get('tiktok'):
            st.image(st.session_state.social_images['tiktok'], use_column_width=True)

    # Final CTA
    st.markdown("""
    <div class="cta-box">
        <h2 style="margin-bottom:10px;">Want us to spread your identity to the world?</h2>
        <p style="margin-bottom:30px;">From concept to execution, we handle everything.</p>
    </div>
    """, unsafe_allow_html=True)
    
    b1, b2, b3 = st.columns([1.5, 1, 1.5])
    with b2:
        st.button("Schedule Consultation", use_container_width=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("New Analysis"):
        st.session_state.clear()
        st.rerun()
