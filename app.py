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
    st.error("API Keys are missing. Please configure SCRAPINGBEE_API_KEY and GOOGLE_API_KEY.")
    st.stop()

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# --- CSS FOR PROJECT ONE THEME ---
st.markdown("""
<style>
    /* --- GLOBAL DARK THEME --- */
    .stApp {
        background-color: #0e1117; /* Dark Gray Background */
        color: #e0e0e0;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    p, div, label {
        color: #c0c0c0;
        font-family: 'Inter', sans-serif;
    }

    /* --- FULL SCREEN TRANSITION (LOADING) --- */
    /* Custom Loading Overlay */
    .stSpinner {
        display: none !important; /* Hide default spinner */
    }
    
    .custom-loader {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: #0e1117;
        z-index: 999999;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .loader-ring {
        display: inline-block;
        width: 60px;
        height: 60px;
        margin-bottom: 20px;
    }
    .loader-ring:after {
        content: " ";
        display: block;
        width: 50px;
        height: 50px;
        margin: 8px;
        border-radius: 50%;
        border: 4px solid #3b82f6;
        border-color: #3b82f6 transparent #3b82f6 transparent;
        animation: ring-spin 1.2s linear infinite;
    }
    @keyframes ring-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loader-text {
        font-size: 1.2rem;
        color: #fff;
        font-weight: 500;
        letter-spacing: 0.5px;
    }

    /* --- CHIP/BADGE STYLING --- */
    .chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 8px;
    }
    
    .chip {
        background-color: #161b22; /* Dark Card BG */
        border: 1px solid #30363d; /* Subtle Border */
        color: #eff6ff;
        padding: 8px 16px;
        border-radius: 4px; /* Squared corners for professional look */
        font-size: 0.9rem;
        font-weight: 500;
        display: inline-block;
    }

    /* --- CARDS --- */
    .st-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* --- COLOR SWATCHES --- */
    .color-swatch {
        width: 100%;
        height: 60px;
        border-radius: 4px;
        margin-bottom: 6px;
        border: 1px solid #444;
    }
    .color-label {
        font-size: 0.75rem;
        color: #888;
        font-family: monospace;
        text-align: center;
    }

    /* --- IMAGES --- */
    .brand-img {
        width: 100%;
        height: 180px;
        object-fit: cover;
        border-radius: 4px;
        opacity: 0.9;
        transition: opacity 0.3s;
        border: 1px solid #30363d;
    }
    .brand-img:hover {
        opacity: 1;
        border-color: #3b82f6;
    }

    /* --- BUTTONS --- */
    .stButton button {
        background-color: #3b82f6; /* Blue Button */
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: background 0.2s;
    }
    .stButton button:hover {
        background-color: #2563eb;
    }
    
    /* EXPANDER Styling */
    .streamlit-expanderHeader {
        background-color: #161b22;
        color: #fff;
        border: 1px solid #30363d;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- BACKEND FUNCTIONS ---

def get_brand_data(url):
    """Calls ScrapingBee to extract brand DNA."""
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
        else:
            st.error(f"ScrapingBee Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

def generate_campaign_strategy(brand_data):
    """Generates campaigns using Gemini 2.0 Flash."""
    try:
        # Updated to available model in your list
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        prompt = f"""
        Act as a Senior Creative Director.
        
        Brand Analysis JSON:
        {json.dumps(brand_data)}

        TASK:
        Create 3 high-end marketing campaign concepts.
        For each, construct a detailed image generation prompt for a smartphone mockup.

        OUTPUT FORMAT (Strict JSON List):
        [
          {{
            "campaign_name": "Title",
            "campaign_description": "Strategic summary (max 40 words).",
            "image_prompt_structure": {{
                 "final_constructed_prompt": "Subject: Photorealistic macro shot of a premium smartphone displaying the Instagram Profile for [Brand]. UI: [Brand Colors] accents, [Font Names]. Content: [Imagery description]. Lighting: Cinematic, moody. Quality: 8k, Octane Render." 
            }}
          }}
        ]
        """
        
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
        
    except Exception as e:
        st.error(f"Strategy Generation Error: {e}")
        return []

def generate_image_from_prompt(prompt_text):
    """Generates image using Imagen 4 (Preview)."""
    try:
        # Using the specific model ID from your list
        model = genai.GenerativeModel('models/imagen-4.0-generate-preview-06-06')
        
        result = model.generate_images(
            prompt=prompt_text,
            number_of_images=1,
            aspect_ratio="9:16",
            safety_filter="block_only_high"
        )
        if result.images:
            return result.images[0].image
        return None
    except Exception as e:
        print(f"Image Gen Error: {e}")
        # Fallback attempt if 4.0 specific syntax differs in library version
        try:
             model = genai.GenerativeModel('models/imagen-3.0-generate-001')
             result = model.generate_images(prompt=prompt_text)
             return result.images[0].image
        except:
             return None

# --- HELPER: Chip Renderer ---
def render_chips(items, key_name='keyword'):
    """Renders a list of dicts as styled chips."""
    if not items:
        return
    
    html = '<div class="chip-container">'
    for item in items:
        val = item.get(key_name, item.get('value', ''))
        if val:
            html += f'<div class="chip">{val}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- CUSTOM LOADING SCREEN FUNCTION ---
def full_screen_loader(text):
    st.markdown(f"""
        <div class="custom-loader">
            <div class="loader-ring"></div>
            <div class="loader-text">{text}</div>
        </div>
    """, unsafe_allow_html=True)

# --- STATE ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'brand_data' not in st.session_state:
    st.session_state.brand_data = {}
if 'campaigns' not in st.session_state:
    st.session_state.campaigns = []

# --- PAGE 1: INPUT ---
if st.session_state.step == 1:
    st.markdown("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 3rem;'>Project One</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Automated Brand Intelligence & Strategy</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        url_input = st.text_input("URL", placeholder="ex: www.spacex.com", label_visibility="collapsed")
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        if st.button("Analyze Brand", use_container_width=True):
            if url_input:
                # Show custom loader
                placeholder = st.empty()
                with placeholder:
                    full_screen_loader("Analyzing Digital Footprint...")
                
                # Logic
                data = get_brand_data(url_input)
                
                # Clear loader
                placeholder.empty()
                
                if data:
                    st.session_state.brand_data = data
                    st.session_state.step = 2
                    st.rerun()

# --- PAGE 2: DASHBOARD ---
elif st.session_state.step == 2:
    data = st.session_state.brand_data
    
    # Header
    st.markdown(f"<h1>{data.get('projectName', 'Brand Analysis')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 1.2rem; color: #3b82f6;'>{data.get('tagline', '')}</p>", unsafe_allow_html=True)
    st.divider()

    # Row 1: Identity & Colors
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("### Core Identity")
        st.markdown(f"**Industry:** <span style='color:#ccc'>{data.get('industry', 'N/A')}</span>", unsafe_allow_html=True)
        st.markdown(f"**Concept:** <span style='color:#ccc'>{data.get('concept', 'N/A')}</span>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Brand Values")
        render_chips(data.get('values', []), key_name='value')
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Tone of Voice")
        render_chips(data.get('tone', []), key_name='keyword')
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Aesthetics")
        render_chips(data.get('aesthetic', []), key_name='keyword')

    with col2:
        st.markdown("### Palette")
        if data.get('colors'):
            # Grid for colors
            cols = st.columns(3)
            for i, color in enumerate(data['colors']):
                hex_code = color.get('hex_code', '#000')
                with cols[i % 3]:
                    st.markdown(f"<div class='color-swatch' style='background-color: {hex_code};'></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='color-label'>{hex_code}</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Typography")
        if data.get('fonts'):
            for f in data['fonts']:
                st.markdown(f"<div style='background:#161b22; padding:8px; border-radius:4px; margin-bottom:5px; border-left: 3px solid #3b82f6;'>{f.get('font_name')} <span style='opacity:0.5; font-size:0.8em'>({f.get('use')})</span></div>", unsafe_allow_html=True)

    # Row 2: Visuals (Conditional)
    if data.get('images') and len(data['images']) > 0:
        st.markdown("---")
        st.markdown("### Visual Assets")
        
        img_list = [img.get('src') for img in data['images'] if img.get('src')]
        if img_list:
            cols = st.columns(4)
            for i, img_url in enumerate(img_list[:4]): # Max 4 images
                 with cols[i]:
                     st.markdown(f"<img src='{img_url}' class='brand-img' onerror='this.style.display=\"none\"'/>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Action Button
    c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
    with c_btn2:
        if st.button("Generate Campaign Concepts", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# --- PAGE 3: RESULTS ---
elif st.session_state.step == 3:
    
    # LOGIC IN LOADER
    if not st.session_state.campaigns:
        # Display Custom Loader
        placeholder = st.empty()
        with placeholder:
            full_screen_loader("Synthesizing Strategy & Rendering Mockups...")
        
        # 1. Strategy
        campaign_data = generate_campaign_strategy(st.session_state.brand_data)
        
        # 2. Images
        final_campaigns = []
        for camp in campaign_data:
            prompt = camp.get('image_prompt_structure', {}).get('final_constructed_prompt', '')
            if prompt:
                img = generate_image_from_prompt(prompt)
                camp['generated_image'] = img
            final_campaigns.append(camp)
        
        st.session_state.campaigns = final_campaigns
        
        # Remove loader
        placeholder.empty()
        st.rerun()

    # DISPLAY
    st.markdown("<h1>Strategic Concepts</h1>", unsafe_allow_html=True)
    st.divider()

    if not st.session_state.campaigns:
        st.error("Generation failed. Please check API status.")
        if st.button("Retry"):
            st.session_state.campaigns = []
            st.session_state.step = 2
            st.rerun()
    
    for i, campaign in enumerate(st.session_state.campaigns):
        with st.container():
            st.markdown(f"### {i+1}. {campaign.get('campaign_name')}")
            
            c_txt, c_img = st.columns([1, 1], gap="large")
            
            with c_txt:
                st.markdown(f"<div style='font-size:1.1rem; line-height:1.6; color:#ccc; margin-bottom:20px;'>{campaign.get('campaign_description')}</div>", unsafe_allow_html=True)
                
                with st.expander("View Prompt Details"):
                    st.code(campaign.get('image_prompt_structure', {}).get('final_constructed_prompt'), language="text")
            
            with c_img:
                img = campaign.get('generated_image')
                if img:
                    st.image(img, caption="Generated Mockup", use_column_width=True)
                else:
                    st.info("Image generation unavailable.")
            
            st.markdown("---")

    if st.button("Start New Project"):
        st.session_state.clear()
        st.rerun()
