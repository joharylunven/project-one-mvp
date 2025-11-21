import streamlit as st
import requests
import json
import urllib.parse
import google.generativeai as genai

# --- CONFIGURATION DES CLÉS ---
# À mettre dans .streamlit/secrets.toml ou dans les secrets du Cloud
SCRAPINGBEE_API_KEY = st.secrets.get("SCRAPINGBEE_API_KEY", "TA_CLE_SCRAPINGBEE")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "TA_CLE_GOOGLE_GEMINI")

# Config Google Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# --- CSS (STYLE LUXE / DARK) ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Playfair+Display:wght@400;700&display=swap');
    :root { --primary: #F5F0E9; --bg: #1c1c1c; --card-bg: #1A1A1A; --accent: #A18B56; --border: #2a2a2a; }
    .stApp { background-color: var(--bg); color: var(--primary); font-family: 'Lato', sans-serif; }
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: var(--primary) !important; }
    .css-card { background-color: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-bottom: 20px; }
    div.stButton > button { background-color: var(--accent); color: #1A1A1A; border-radius: 30px; border: none; font-weight: bold; padding: 10px 25px; }
    div.stButton > button:hover { background-color: #F5F0E9; color: #1A1A1A; border: none; }
    .tag-pill { background-color: #2a2a2a; border: 1px solid #444; border-radius: 20px; padding: 5px 12px; font-size: 0.85rem; margin-right: 5px; display: inline-block; color: #F5F0E9; }
    .color-circle { width: 40px; height: 40px; border-radius: 50%; display: inline-block; margin-right: 10px; vertical-align: middle; border: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. FONCTION SCRAPINGBEE (AVEC TON JSON RULES) ---
def get_brand_dna_scrapingbee(url):
    """Appelle ScrapingBee avec les règles d'extraction IA définies dans ton n8n."""
    
    # Tes règles exactes copié-collées de ton n8n
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
            "output": {"font_name": "the name of the font", "use": "its main purpose"}
        },
        "aesthetic": {
            "description": "list of 3-5 keywords describing the brand aesthetic",
            "type": "list",
            "output": {"keyword": "a single keyword"}
        },
        "values": {
            "description": "a list of 3-5 brand values mentioned on the site",
            "type": "list",
            "output": {"value": "a single brand value"}
        },
        "tone": {
            "description": "a list of 3-5 keywords for the brand's tone of voice",
            "type": "list",
            "output": {"keyword": "a single tone keyword"}
        },
        "images": {
            "description": "list of the 6 most relevant brand or product images",
            "type": "list",
            "output": {"src": "the full absolute URL of the image", "alt": "the alt text"}
        }
    }

    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': url, 
        'render_js': 'true', # Souvent nécessaire pour que l'IA "voie" tout le site
        'block_resources': 'false',
        'wait': '2000', # Attendre un peu le chargement
        'ai_extract_rules': json.dumps(extract_rules) # On envoie le JSON stringifié
    }

    try:
        response = requests.get('https://app.scrapingbee.com/api/v1/', params=params)
        if response.status_code == 200:
            # ScrapingBee renvoie directement le JSON extrait grâce à l'option AI
            return response.json()
        else:
            st.error(f"Erreur ScrapingBee: {response.text}")
            return None
    except Exception as e:
        st.error(f"Erreur Connection: {e}")
        return None

# --- 2. FONCTION MARKETING (VERSION MISE À JOUR GEMINI 2.5) ---
def generate_marketing_gemini(dna_json):
    prompt = f"""
    Act as a marketing expert. Analyze this JSON: {json.dumps(dna_json)}
    Create 3 Instagram campaigns.
    Return ONLY valid JSON.
    Structure: {{ "campaigns": [ {{ "title": "...", "caption": "...", "image_prompt": "..." }} ] }}
    """

    # MISE À JOUR ICI : On utilise le modèle présent dans ta liste
    # 'gemini-2.5-flash' est stable et rapide
    model_name = 'gemini-2.5-flash'
    
    try:
        if not GOOGLE_API_KEY:
            st.error("La clé API Google est vide.")
            return []

        # On instancie le modèle spécifique
        model = genai.GenerativeModel(model_name)
        
        # Appel API
        response = model.generate_content(prompt)
        
        # Nettoyage de la réponse (au cas où il y a du markdown)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)['campaigns']

    except Exception as e:
        st.error(f"ERREUR : {e}")
        # Fallback : Si le 2.5 échoue, on tente le 'latest' générique
        try:
            st.warning("Tentative avec le modèle générique...")
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)['campaigns']
        except:
            return []

# --- 3. FONCTION IMAGE (Astuce MVP Gratuit) ---
def get_mvp_image_url(prompt):
    """
    Génère une URL d'image basée sur le prompt via Pollinations (Gratuit/Rapide).
    C'est parfait pour un MVP car Google Gemini API standard ne rend pas d'images facilement.
    """
    encoded_prompt = urllib.parse.quote(prompt)
    # On ajoute des paramètres pour forcer le réalisme
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&seed=42"

# --- INTERFACE STREAMLIT ---

st.set_page_config(page_title="Project One", layout="wide", initial_sidebar_state="collapsed")
local_css()

# Gestion de l'état
if 'step' not in st.session_state: st.session_state.step = 1
if 'dna' not in st.session_state: st.session_state.dna = None
if 'campaigns' not in st.session_state: st.session_state.campaigns = None

# PAGE 1 : URL INPUT
if st.session_state.step == 1:
    st.markdown("<div style='text-align:center; margin-top: 80px;'>", unsafe_allow_html=True)
    st.markdown("# Project One")
    st.markdown("### Enter your website")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        url_input = st.text_input("Website URL", placeholder="www.wheeltheworld.com", label_visibility="collapsed")
        if st.button("Start Analysis"):
            if url_input:
                if not url_input.startswith('http'): url_input = 'https://' + url_input
                st.session_state.url = url_input
                st.session_state.step = 1.5
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# PAGE LOADING
elif st.session_state.step == 1.5:
    st.markdown("<div style='text-align:center; margin-top: 80px;'>", unsafe_allow_html=True)
    st.markdown("## Generating your Business DNA")
    st.markdown(f"<p style='color:#B0B4B8;'>Analyzing {st.session_state.url} with ScrapingBee AI...</p>", unsafe_allow_html=True)
    with st.spinner("Extracting colors, fonts, and values..."):
        dna_data = get_brand_dna_scrapingbee(st.session_state.url)
        if dna_data:
            st.session_state.dna = dna_data
            st.session_state.step = 2
            st.rerun()
        else:
            st.error("Analysis failed.")
            if st.button("Retry"): st.session_state.step = 1; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# PAGE 2 : DASHBOARD ADN
elif st.session_state.step == 2:
    dna = st.session_state.dna
    
    # Navigation
    if st.button("← Back"): st.session_state.step = 1; st.rerun()
    
    st.markdown(f"<h1 style='text-align:center;'>Your Business DNA</h1>", unsafe_allow_html=True)
    st.markdown("---")

    c1, c2, c3 = st.columns([1, 1, 1])

    # Colonne 1
    with c1:
        st.markdown(f"""<div class="css-card"><h2>{dna.get('projectName', 'Brand')}</h2><p>"{dna.get('tagline', '')}"</p></div>""", unsafe_allow_html=True)
        
        st.markdown('<div class="css-card"><h2>Colors</h2>', unsafe_allow_html=True)
        for color in dna.get('colors', [])[:5]:
            c_hex = color.get('hex_code', '#000')
            st.markdown(f"""<div style="display:flex; align-items:center; margin-bottom:5px;"><div class="color-circle" style="background-color:{c_hex};"></div><span>{c_hex}</span></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="css-card"><h2>Aesthetic</h2>', unsafe_allow_html=True)
        for item in dna.get('aesthetic', []): st.markdown(f'<span class="tag-pill">{item["keyword"]}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Colonne 2
    with c2:
        st.markdown('<div class="css-card"><h2>Fonts</h2>', unsafe_allow_html=True)
        for f in dna.get('fonts', []): st.markdown(f"**{f['font_name']}** - *{f['use']}*", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="css-card"><h2>Values</h2>', unsafe_allow_html=True)
        for item in dna.get('values', []): st.markdown(f'<span class="tag-pill">{item["value"]}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Colonne 3
    with c3:
        st.markdown('<div class="css-card"><h2>Images (Scraped)</h2>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, img in enumerate(dna.get('images', [])[:4]):
            try: cols[i%2].image(img['src'])
            except: pass
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(f"""<div class="css-card"><h2>Concept</h2><p>{dna.get('concept', '')}</p></div>""", unsafe_allow_html=True)

    if st.button("Generate Campaigns with Google Gemini →", type="primary", use_container_width=True):
        st.session_state.step = 3
        st.rerun()

# PAGE 3 : CAMPAGNES
elif st.session_state.step == 3:
    st.markdown(f"<h1 style='text-align:center;'>Marketing Campaigns</h1>", unsafe_allow_html=True)
    
    if not st.session_state.campaigns:
        with st.spinner("Google Gemini is brainstorming ideas..."):
            st.session_state.campaigns = generate_marketing_gemini(st.session_state.dna)
            st.rerun()
            
    else:
        # Affichage des résultats
        main_camp = st.session_state.campaigns[0]
        
        # On génère l'image à la volée pour l'affichage MVP
        image_url = get_mvp_image_url(main_camp['image_prompt'])
        
        col_img, col_txt = st.columns([1, 1])
        with col_img:
            st.image(image_url, caption="AI Generated Visual")
        
        with col_txt:
            st.markdown(f"""
            <div class="css-card">
                <h2>{main_camp['title']}</h2>
                <p style="white-space: pre-line;">{main_camp['caption']}</p>
                <hr style="border-color:#444;">
                <p style="color:#888; font-size:0.8em;">Prompt Image: {main_camp['image_prompt']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Autres idées
        st.subheader("Alternative Concepts")
        alt_cols = st.columns(2)
        for i, camp in enumerate(st.session_state.campaigns[1:3]):
            with alt_cols[i]:
                st.markdown(f"""<div class="css-card"><h3>{camp['title']}</h3><p>{camp['caption'][:150]}...</p></div>""", unsafe_allow_html=True)

        if st.button("Start Over"):
            st.session_state.clear()
            st.rerun()
