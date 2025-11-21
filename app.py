import streamlit as st
import requests
import json
import google.generativeai as genai
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Brand AI Generator", layout="wide", initial_sidebar_state="collapsed")

# Load API Keys
try:
    SCRAPINGBEE_API_KEY = st.secrets["SCRAPINGBEE_API_KEY"]
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except FileNotFoundError:
    st.error("API Keys are missing. Please configure SCRAPINGBEE_API_KEY and GOOGLE_API_KEY in .streamlit/secrets.toml")
    st.stop()

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# --- CSS FOR CLEAN UI & FULL SCREEN LOADER ---
st.markdown("""
<style>
    /* GENERAL TYPOGRAPHY & COLORS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #ffffff;
        color: #1a1a1a; 
    }
    
    h1, h2, h3 {
        color: #000000;
        font-weight: 600;
        letter-spacing: -0.5px;
    }

    /* CARD STYLE */
    .st-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* FULL SCREEN SPINNER HACK */
    /* This targets the streamlit spinner container and makes it fixed full screen */
    div[data-testid="stSpinner"] {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(255, 255, 255, 0.98);
        z-index: 999999;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    
    /* BRAND COLORS */
    .color-swatch {
        width: 100%;
        height: 80px;
        border-radius: 6px;
        margin-bottom: 8px;
        border: 1px solid #ddd;
    }
    .color-label {
        font-size: 0.85rem;
        color: #555;
        font-family: monospace;
    }

    /* IMAGES GRID */
    .img-grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 16px;
    }
    .brand-img {
        width: 100%;
        height: 150px;
        object-fit: cover;
        border-radius: 6px;
        border: 1px solid #eee;
    }
    
    /* BUTTONS */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- BACKEND FUNCTIONS ---

def get_brand_data(url):
    """Calls ScrapingBee to extract brand DNA."""
    target_url = url if url.startswith("http") else f"https://{url}"
    
    # The full extraction rules provided in the JSON
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
        "wait": "3000", # Increased wait slightly for safety
        "ai_extract_rules": json.dumps(extract_rules)
    }

    try:
        response = requests.get("https://app.scrapingbee.com/api/v1", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error connecting to ScrapingBee: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def generate_campaign_strategy(brand_data):
    """Generates campaigns using Gemini 1.5 Flash."""
    # ERROR HANDLING FOR MODEL NOT FOUND
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Robust Prompt
        prompt = f"""
        You are a luxury marketing strategist and art director.
        
        Brand Data:
        {json.dumps(brand_data)}

        TASK:
        Generate 3 distinct marketing campaign ideas.
        For each campaign, provide a 'final_constructed_prompt' to generate a high-quality mockup image of an Instagram Profile on a phone screen.

        OUTPUT FORMAT (Strict JSON List):
        [
          {{
            "campaign_name": "Name of campaign",
            "campaign_description": "Short strategic description (approx 30 words).",
            "image_prompt_structure": {{
                 "final_constructed_prompt": "Subject: A photorealistic macro shot of a smartphone displaying the Instagram profile for [Brand Name]. UI Style: Minimalist, Clean White Mode, using fonts [Brand Fonts]. Header: Bio reads '[Brand Tagline]'. Visuals: Grid images showing [Campaign Theme]. Lighting: Studio softbox. Tech: 8k, Octane render." 
            }}
          }}
        ]
        """
        
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
        
    except Exception as e:
        st.error(f"Error with Google Gemini API: {e}")
        st.warning("Tip: Ensure your Google Cloud Project has the 'Gemini API' enabled and your API Key is valid.")
        return []

def generate_image_from_prompt(prompt_text):
    """Generates image using Imagen 3."""
    try:
        model = genai.GenerativeModel('imagen-3.0-generate-001')
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
        # Graceful fallback or error logging
        print(f"Image generation error: {e}") 
        return None

# --- STATE MANAGEMENT ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'brand_data' not in st.session_state:
    st.session_state.brand_data = {}
if 'campaigns' not in st.session_state:
    st.session_state.campaigns = []

# --- PAGE 1: INPUT ---
if st.session_state.step == 1:
    st.markdown("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Brand Intelligence Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Enter your website URL to generate a full brand analysis and AI marketing strategies.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        url_input = st.text_input("Website URL", placeholder="e.g. www.apple.com", label_visibility="collapsed")
        
        # Spacer
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        if st.button("Analyze Brand", type="primary", use_container_width=True):
            if url_input:
                with st.spinner("Analyzing website architecture... Extracting design tokens..."):
                    data = get_brand_data(url_input)
                    if data:
                        st.session_state.brand_data = data
                        st.session_state.step = 2
                        st.rerun()

# --- PAGE 2: BRAND DNA ---
elif st.session_state.step == 2:
    data = st.session_state.brand_data
    
    # Top Navigation / Header
    st.markdown(f"<h1>{data.get('projectName', 'Brand Analysis')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 1.2rem; color: #555; margin-top: -10px;'>{data.get('tagline', '')}</p>", unsafe_allow_html=True)
    
    st.divider()

    # SECTION 1: CORE IDENTITY
    st.subheader("Core Identity")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"**Industry**<br>{data.get('industry', 'N/A')}", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Concept**<br>{data.get('concept', 'N/A')}", unsafe_allow_html=True)
    
    with c2:
        # Values
        st.markdown("**Brand Values**", unsafe_allow_html=True)
        if data.get('values'):
            for v in data['values']:
                st.markdown(f"- {v.get('value')}")

    # SECTION 2: AESTHETICS & DESIGN SYSTEM
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Design System")
    
    # Colors
    st.markdown("**Color Palette**")
    if data.get('colors'):
        cols = st.columns(len(data['colors']))
        for idx, color in enumerate(data['colors']):
            hex_code = color.get('hex_code', '#FFFFFF')
            with cols[idx]:
                st.markdown(f"<div class='color-swatch' style='background-color: {hex_code};'></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='color-label'>{hex_code}</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_font, col_style, col_tone = st.columns(3)
    
    with col_font:
        st.markdown("**Typography**")
        if data.get('fonts'):
            for f in data['fonts']:
                st.markdown(f"• {f.get('font_name')} <span style='color:#888; font-size:0.8em'>({f.get('use')})</span>", unsafe_allow_html=True)
    
    with col_style:
        st.markdown("**Aesthetic Keywords**")
        if data.get('aesthetic'):
            for a in data['aesthetic']:
                st.markdown(f"• {a.get('keyword')}")

    with col_tone:
        st.markdown("**Tone of Voice**")
        if data.get('tone'):
            for t in data['tone']:
                st.markdown(f"• {t.get('keyword')}")

    # SECTION 3: IMAGERY
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Visual Assets")
    
    if data.get('images'):
        # Creating a clean grid using Columns
        img_list = data['images']
        # Display in rows of 4
        for i in range(0, len(img_list), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(img_list):
                    img_url = img_list[i+j].get('src')
                    if img_url:
                        with cols[j]:
                            st.markdown(
                                f"<img src='{img_url}' class='brand-img' />", 
                                unsafe_allow_html=True
                            )

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # ACTION
    if st.button("Generate Campaign Concepts", type="primary"):
        st.session_state.step = 3
        st.rerun()

# --- PAGE 3: CAMPAIGNS ---
elif st.session_state.step == 3:
    
    # LOGIC (Runs inside the spinner for full screen effect)
    if not st.session_state.campaigns:
        with st.spinner("Developing strategic concepts... Rendering high-fidelity mockups..."):
            # 1. Generate Text Strategy
            campaign_data = generate_campaign_strategy(st.session_state.brand_data)
            
            # 2. Generate Images for each strategy
            final_campaigns = []
            for camp in campaign_data:
                # Safe prompt extraction
                prompt = camp.get('image_prompt_structure', {}).get('final_constructed_prompt', '')
                
                if prompt:
                    img = generate_image_from_prompt(prompt)
                    camp['generated_image'] = img
                
                final_campaigns.append(camp)
            
            st.session_state.campaigns = final_campaigns
            # Rerun to exit the spinner and render the page
            st.rerun()

    # DISPLAY
    st.markdown("<h1>Strategic Campaigns</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666;'>AI-generated marketing concepts based on brand DNA.</p>", unsafe_allow_html=True)
    st.divider()

    if not st.session_state.campaigns:
        st.error("No campaigns could be generated. Please try again.")
        if st.button("Retry"):
            st.session_state.campaigns = []
            st.session_state.step = 2
            st.rerun()
    
    for i, campaign in enumerate(st.session_state.campaigns):
        with st.container():
            st.markdown(f"### {i+1}. {campaign.get('campaign_name')}")
            
            col_text, col_img = st.columns([1, 1], gap="large")
            
            with col_text:
                st.markdown("**Strategy**")
                st.write(campaign.get('campaign_description'))
                
                with st.expander("View Technical Prompt"):
                    st.code(campaign.get('image_prompt_structure', {}).get('final_constructed_prompt'), language="text")
            
            with col_img:
                img = campaign.get('generated_image')
                if img:
                    st.image(img, caption="AI Generated Mockup", use_column_width=True)
                else:
                    st.markdown(
                        "<div style='background:#f0f0f0; height:300px; display:flex; align-items:center; justify-content:center; color:#888;'>Image generation unavailable</div>", 
                        unsafe_allow_html=True
                    )
            
            st.divider()

    if st.button("Start Over"):
        st.session_state.clear()
        st.rerun()
