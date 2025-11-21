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
        color: #f0f2f6; /* High readability white */
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    p, div, label, li {
        color: #d1d5db; /* Light gray, high contrast */
        font-size: 1rem;
        line-height: 1.6;
    }

    /* --- INPUT FIELD: FORCE BLUE BORDER --- */
    /* Override Streamlit default red/gray focus borders */
    div[data-baseweb="input"] {
        border: 1px solid #3b82f6 !important;
        background-color: #161b22 !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stTextInput"] input {
        color: white !important;
    }
    
    /* Remove default red border on focus/error if present */
    div[data-baseweb="base-input"] {
        border-color: #3b82f6 !important;
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
        display: inline-block;
        width: 50px;
        height: 50px;
        margin-bottom: 24px;
    }
    .loader-ring:after {
        content: " ";
        display: block;
        width: 40px;
        height: 40px;
        margin: 6px;
        border-radius: 50%;
        border: 3px solid #3b82f6;
        border-color: #3b82f6 transparent #3b82f6 transparent;
        animation: ring-spin 1s cubic-bezier(0.5, 0, 0.5, 1) infinite;
    }
    @keyframes ring-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loader-text {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #6b7280;
        font-weight: 500;
    }

    /* --- UI ELEMENTS --- */
    .chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 8px;
    }
    
    .chip {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 0.02em;
    }

    .color-swatch {
        width: 100%;
        height: 70px;
        border-radius: 4px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .color-label {
        font-size: 0.75rem;
        color: #9ca3af;
        font-family: monospace;
        text-align: center;
        text-transform: uppercase;
    }

    .brand-img {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 4px;
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
    }
    .brand-img:hover {
        border-color: #3b82f6;
        transform: translateY(-2px);
    }

    /* --- CTA SECTION (CLEAN FLAT DARK) --- */
    .cta-container {
        text-align: center;
        padding: 60px 20px;
        background-color: #111318; /* Solid dark color, no gradient */
        border: 1px solid #1f2937;
        border-radius: 8px;
        margin-top: 60px;
    }
    .cta-heading {
        font-size: 1.8rem;
        font-weight: 600;
        color: #fff;
        margin-bottom: 10px;
    }
    .cta-sub {
        font-size: 1rem;
        color: #9ca3af;
        margin-bottom: 30px;
    }

    /* --- BUTTONS --- */
    .stButton button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        letter-spacing: 0.02em;
        transition: background 0.2s;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    .stButton button:hover {
        background-color: #2563eb;
    }
    
    /* --- DIVIDERS & SPACING --- */
    hr {
        border-color: #1f2937;
        margin-top: 3rem;
        margin-bottom: 3rem;
    }
    
    .stExpander {
        border: none !important;
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- BACKEND LOGIC ---

def get_brand_data(url):
    """ScrapingBee Extraction."""
    target_url = url if url.startswith("http") else f"https://{url}"
    
    extract_rules = {
        "projectName": "the company or brand name",
        "tagline": "the website's main slogan or tagline",
        "industry": "the business's industry or sector (e.g., tech, fashion)",
        "concept": "a short 50-word summary of what the business does",
        "colors": {
            "description": "list of the 5 main brand colors",
            "type": "list",
            "output": {"hex_code": "color in hexadecimal format (e.g., #1A1A1A)"}
        },
        "fonts": {
            "description": "list of the 2 main font names used",
            "type": "list",
            "output": {"font_name": "the name of the font", "use": "its main purpose (e.g., heading, body text)"}
        },
        "aesthetic": {
            "description": "list of 3-5 keywords describing the brand aesthetic",
            "type": "list",
            "output": {"keyword": "a single keyword (e.g., minimalist, bold)"}
        },
        "values": {
            "description": "a list of 3-5 brand values mentioned on the site",
            "type": "list",
            "output": {"value": "a single brand value (e.g., innovation, quality)"}
        },
        "tone": {
            "description": "a list of 3-5 keywords for the brand's tone of voice",
            "type": "list",
            "output": {"keyword": "a single tone keyword (e.g., professional, friendly)"}
        },
        "images": {
            "description": "list of the 6 most relevant brand or product images",
            "type": "list",
            "output": {"src": "the full absolute URL of the image", "alt": "the alt text of the image"}
        }
    }

    params = {
        "api_key": SCRAPINGBEE_API_KEY,
        "url": target_url,
        "block_resources": "false",
        "wait": "3000", 
        "ai_extract_rules": json.dumps(extract_rules)
    }

    try:
        response = requests.get("https://app.scrapingbee.com/api/v1", params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def generate_campaign_strategy(brand_data):
    """Gemini 2.0 Flash Strategy for 3 Campaigns."""
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        prompt = f"""
        Act as a Luxury Brand Strategist.
        Brand Profile: {json.dumps(brand_data)}

        TASK: Create 3 high-end campaign concepts. 
        For each, write a 'final_constructed_prompt' for image generation.

        OUTPUT JSON:
        [
          {{
            "campaign_name": "Name",
            "campaign_description": "Strategic summary (30-40 words).",
            "image_prompt_structure": {{
                 "final_constructed_prompt": "Subject: Photorealistic macro shot of a premium smartphone displaying the Instagram Profile for [Brand]. UI: [Brand Colors] accents, [Font Names]. Content: [Imagery description]. Lighting: Cinematic, moody. Quality: 8k, Octane Render." 
            }}
          }}
        ]
        """
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return []

def generate_social_prompts(brand_data):
    """Gemini 2.0 Flash for Bespoke Social Media Mockups (Insta & TikTok)."""
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        # --- PROMPT MODIFIE POUR UI ONLY / 9:16 / NO PHONE ---
        prompt = f"""
        You are a Global Creative Director. 
        Brand Data: {json.dumps(brand_data)}
        
        TASK: Create two extremely detailed image prompts for Nano Banana Pro.
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

        OUTPUT JSON:
        {{
            "instagram_final_prompt": "Full constructed string for Instagram...",
            "tiktok_final_prompt": "Full constructed string for TikTok..."
        }}
        """
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return {"instagram_final_prompt": "", "tiktok_final_prompt": ""}

def generate_image_from_prompt(prompt_text):
    """Nano Banana Pro Image Generation."""
    try:
        model = genai.GenerativeModel('models/nano-banana-pro-preview')
        # Force Aspect Ratio in prompt as model doesn't always support parameter
        refined_prompt = prompt_text + " --aspect_ratio 9:16" 
        response = model.generate_content(refined_prompt)
        if response.parts:
            return response.parts[0].inline_data.data
        return None
    except:
        return None

# --- HELPER: UI Components ---
def render_chips(items, key_name='keyword'):
    if not items: return
    html = '<div class="chip-container">'
    for item in items:
        val = item.get(key_name, item.get('value', ''))
        if val: html += f'<div class="chip">{val}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def full_screen_loader(text):
    st.markdown(f"""<div class="custom-loader"><div class="loader-ring"></div><div class="loader-text">{text}</div></div>""", unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'brand_data' not in st.session_state: st.session_state.brand_data = {}
if 'campaigns' not in st.session_state: st.session_state.campaigns = []
if 'social_images' not in st.session_state: st.session_state.social_images = {}

# --- PAGE 1: URL INPUT ---
if st.session_state.step == 1:
    # Adjusted spacer for visual vertical centering (25vh usually hits the sweet spot)
    st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; font-weight: 700;'>Project One</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6b7280; letter-spacing: 1px; margin-top: -10px;'>BESPOKE BRAND INTELLIGENCE</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        url_input = st.text_input("URL", placeholder="ex: www.example.com", label_visibility="collapsed")
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        if st.button("Decode Brand DNA", use_container_width=True):
            if url_input:
                placeholder = st.empty()
                with placeholder: full_screen_loader("Extracting Digital Footprint...")
                data = get_brand_data(url_input)
                placeholder.empty()
                if data:
                    st.session_state.brand_data = data
                    st.session_state.step = 2
                    st.rerun()

# --- PAGE 2: BRAND DASHBOARD ---
elif st.session_state.step == 2:
    data = st.session_state.brand_data
    
    # Header
    st.markdown(f"<h1 style='font-size: 2.5rem;'>{data.get('projectName', 'Brand Identity')}</h1>", unsafe_allow_html=True)
    if data.get('tagline'):
        st.markdown(f"<p style='font-size: 1.1rem; color: #3b82f6; margin-top: -15px;'>{data.get('tagline')}</p>", unsafe_allow_html=True)
    st.divider()

    # Main Layout
    col1, col2 = st.columns([1.5, 1], gap="large")
    
    with col1:
        st.markdown("### Brand Essence")
        st.markdown(f"**Industry:** <span style='color:#fff'>{data.get('industry', 'N/A')}</span>", unsafe_allow_html=True)
        st.markdown(f"**Concept:** <span style='color:#fff'>{data.get('concept', 'N/A')}</span>", unsafe_allow_html=True)
        
        if data.get('values'):
            st.markdown("<br>### Core Values", unsafe_allow_html=True)
            render_chips(data.get('values'), key_name='value')
        
        if data.get('tone'):
            st.markdown("<br>### Voice & Tone", unsafe_allow_html=True)
            render_chips(data.get('tone'), key_name='keyword')
        
        if data.get('aesthetic'):
            st.markdown("<br>### Visual Identity", unsafe_allow_html=True)
            render_chips(data.get('aesthetic'), key_name='keyword')

    with col2:
        # Conditional Rendering for Palette
        if data.get('colors') and len(data['colors']) > 0:
            st.markdown("### Chromatic Palette")
            cols = st.columns(3)
            for i, color in enumerate(data['colors']):
                hex_code = color.get('hex_code', '')
                if hex_code:
                    with cols[i % 3]:
                        st.markdown(f"<div class='color-swatch' style='background-color: {hex_code};'></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='color-label'>{hex_code}</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Conditional Rendering for Typography
        if data.get('fonts') and len(data['fonts']) > 0:
            st.markdown("### Typography System")
            for f in data['fonts']:
                st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:4px; margin-bottom:6px; border-left: 2px solid #3b82f6;'>{f.get('font_name')} <span style='opacity:0.5; font-size:0.8em'>({f.get('use')})</span></div>", unsafe_allow_html=True)

    # Visual Assets Section (Smart Hide)
    if data.get('images') and len([img for img in data['images'] if img.get('src')]) > 0:
        st.markdown("---")
        st.markdown("### Visual Assets")
        valid_images = [img.get('src') for img in data['images'] if img.get('src')]
        cols = st.columns(4)
        for i, img_url in enumerate(valid_images[:4]):
             with cols[i]:
                 st.markdown(f"<img src='{img_url}' class='brand-img' onerror='this.style.display=\"none\"'/>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Action
    c_b1, c_b2, c_b3 = st.columns([1, 2, 1])
    with c_b2:
        if st.button("Generate Tailored Strategies", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# --- PAGE 3: STRATEGIC VISION ---
elif st.session_state.step == 3:
    
    # Anchor to allow "Top of Page" feel
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)

    # Generation Logic
    if not st.session_state.campaigns or not st.session_state.social_images:
        placeholder = st.empty()
        with placeholder: full_screen_loader("Crafting Visual Narratives & Social Ecosystem...")
        
        # 1. Campaigns (if not already done)
        if not st.session_state.campaigns:
            campaign_data = generate_campaign_strategy(st.session_state.brand_data)
            final_campaigns = []
            for camp in campaign_data:
                prompt = camp.get('image_prompt_structure', {}).get('final_constructed_prompt', '')
                if prompt:
                    img_data = generate_image_from_prompt(prompt)
                    camp['generated_image'] = img_data
                final_campaigns.append(camp)
            st.session_state.campaigns = final_campaigns
        
        # 2. Social Mockups (if not already done)
        if not st.session_state.social_images:
            social_prompts = generate_social_prompts(st.session_state.brand_data)
            
            # Instagram
            if social_prompts.get("instagram_final_prompt"):
                insta_img = generate_image_from_prompt(social_prompts["instagram_final_prompt"])
                st.session_state.social_images['instagram'] = insta_img
            
            # TikTok
            if social_prompts.get("tiktok_final_prompt"):
                tiktok_img = generate_image_from_prompt(social_prompts["tiktok_final_prompt"])
                st.session_state.social_images['tiktok'] = tiktok_img

        placeholder.empty()
        st.rerun()

    # --- CONTENT DISPLAY ---
    st.markdown("<h1>Tailored Strategic Concepts</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6b7280;'>AI-Curated Marketing Directions</p>", unsafe_allow_html=True)
    st.divider()

    if not st.session_state.campaigns:
        st.error("Strategy generation unavailable.")
        if st.button("Retry Protocol"):
            st.session_state.clear()
            st.rerun()
    
    # Campaigns Loop
    for i, campaign in enumerate(st.session_state.campaigns):
        with st.container():
            col_text, col_img = st.columns([1, 1], gap="large", vertical_alignment="center")
            
            with col_text:
                st.markdown(f"<h3 style='font-size: 1.8rem; margin-bottom: 10px;'>{i+1}. {campaign.get('campaign_name')}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size:1.05rem; line-height:1.8; color:#d1d5db;'>{campaign.get('campaign_description')}</p>", unsafe_allow_html=True)
                
                with st.expander("View Prompt Specification"):
                    st.code(campaign.get('image_prompt_structure', {}).get('final_constructed_prompt'), language="text")
            
            with col_img:
                img = campaign.get('generated_image')
                if img:
                    st.image(img, use_column_width=True)
                else:
                    st.info("Visualization pending.")
            
            st.markdown("---")

    # --- SOCIAL PRESENCE SECTION ---
    st.markdown("<br><h2 style='text-align:center;'>Omnichannel Presence</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#6b7280; margin-bottom: 40px;'>Ecosystem Expansion Visualization</p>", unsafe_allow_html=True)

    s_col1, s_col2 = st.columns(2, gap="large")
    
    with s_col1:
        st.markdown("<h4 style='text-align:center; margin-bottom:20px;'>Instagram Preview</h4>", unsafe_allow_html=True)
        if st.session_state.social_images.get('instagram'):
            st.image(st.session_state.social_images['instagram'], use_column_width=True)
        else:
            st.info("Instagram mockup generation failed.")
            
    with s_col2:
        st.markdown("<h4 style='text-align:center; margin-bottom:20px;'>TikTok Preview</h4>", unsafe_allow_html=True)
        if st.session_state.social_images.get('tiktok'):
            st.image(st.session_state.social_images['tiktok'], use_column_width=True)
        else:
            st.info("TikTok mockup generation failed.")

    # --- FINAL CTA (CLEAN FLAT DESIGN) ---
    st.markdown("""
        <div class="cta-container">
            <div class="cta-heading">Ready to amplify your digital footprint?</div>
            <div class="cta-sub">Transform these concepts into your reality. Let's define your future.</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Centering the button using columns
    b1, b2, b3 = st.columns([1.5, 1, 1.5])
    with b2:
        st.button("Schedule a Consultation", use_container_width=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if st.button("Initialize New Analysis"):
        st.session_state.clear()
        st.rerun()
