import streamlit as st
import requests
import json
import google.generativeai as genai
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Brand AI Generator", layout="wide", initial_sidebar_state="collapsed")

# Récupération des clés API depuis les secrets Streamlit
try:
    SCRAPINGBEE_API_KEY = st.secrets["SCRAPINGBEE_API_KEY"]
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Les clés API (SCRAPINGBEE_API_KEY et GOOGLE_API_KEY) ne sont pas configurées dans les secrets.")
    st.stop()

# Configuration Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# --- FONCTIONS BACKEND ---

def get_brand_data(url):
    """Appelle ScrapingBee avec les règles d'extraction définies dans ton JSON n8n."""
    
    # Nettoyage URL pour l'envoyer proprement
    target_url = url if url.startswith("http") else f"https://{url}"
    
    # Règles d'extraction (Copiées de ton workflow n8n)
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
        "wait": "2000", # Attente pour chargement JS
        "ai_extract_rules": json.dumps(extract_rules)
    }

    response = requests.get("https://app.scrapingbee.com/api/v1", params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erreur ScrapingBee: {response.text}")
        return None

def generate_campaign_strategy(brand_data):
    """Utilise Gemini 1.5 Flash pour générer les campagnes et les prompts d'images structurés."""
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Le prompt système force Gemini à sortir du JSON strict avec ta structure d'image spécifique
    prompt = f"""
    Tu es un expert en stratégie marketing et direction artistique de luxe.
    
    Voici les données de la marque (JSON scu):
    {json.dumps(brand_data)}

    TA MISSION :
    Génère 3 idées de campagnes marketing distinctes pour cette marque.
    Pour chaque campagne, tu dois aussi générer un prompt de génération d'image TRÈS DÉTAILLÉ pour créer un mockup de profil Instagram via une IA générative.

    Format de sortie attendu (JSON LIST) :
    [
      {{
        "campaign_name": "Nom de la campagne",
        "campaign_description": "Description stratégique courte",
        "image_prompt_structure": {{
             "subject_anchor": "A hyper-realistic macro shot...",
             "screen_ui_context": {{ "app": "Instagram Profile", "visual_identity": "Use colors {brand_data.get('colors', [])}..." }},
             "grid_content_simulation": {{ "description": "...", "specific_posts": ["Post 1...", "Post 2..."] }},
             "final_constructed_prompt": "Subject: A hyper-realistic shot of a smartphone displaying Instagram profile for [Brand Name]. UI Style: [Brand Aesthetic]. Grid Content: [Campaign Theme images]. Colors: [Brand Colors]. Tech Specs: 8k, octane render, photorealistic." 
        }}
      }}
    ]
    
    Assure-toi que le champ 'final_constructed_prompt' est un paragraphe complet prêt à être envoyé à un modèle de diffusion d'image (Imagen 3), décrivant une photo macro d'un téléphone affichant le profil Instagram de la marque, avec un style correspondant à l'esthétique de la marque analysée.
    """
    
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    return json.loads(response.text)

def generate_image_from_prompt(prompt_text):
    """Génère l'image via Imagen 3 (via Google GenAI)."""
    try:
        model = genai.GenerativeModel('imagen-3.0-generate-001')
        result = model.generate_images(
            prompt=prompt_text,
            number_of_images=1,
            aspect_ratio="9:16", # Format story/mobile
            safety_filter="block_only_high"
        )
        if result.images:
            return result.images[0].image
        return None
    except Exception as e:
        # Fallback si le modèle spécifique n'est pas dispo ou erreur quota
        st.warning(f"Erreur génération image: {e}")
        return None

# --- CSS PERSONNALISÉ ---
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .brand-header {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        font-size: 3rem;
        color: #111;
        margin-bottom: 0px;
    }
    .brand-tagline {
        font-style: italic;
        color: #555;
        font-size: 1.2rem;
        margin-bottom: 30px;
    }
    .card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .color-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border: 2px solid white;
    }
    /* Loading screen override */
    .stSpinner > div {
        border-top-color: #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- GESTION D'ÉTAT (SESSION STATE) ---
if 'step' not in st.session_state:
    st.session_state.step = 1 # 1: Input, 2: Brand DNA, 3: Campaigns
if 'brand_data' not in st.session_state:
    st.session_state.brand_data = {}
if 'campaigns' not in st.session_state:
    st.session_state.campaigns = []

# --- PAGE 1 : INPUT URL ---
if st.session_state.step == 1:
    st.markdown("<div style='text-align: center; margin-top: 100px;'><h1>🚀 Brand AI Analyzer</h1><p>Entrez l'URL de votre entreprise pour générer votre ADN et vos campagnes.</p></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        url_input = st.text_input("Website URL", placeholder="ex: www.tesla.com")
        analyze_btn = st.button("Analyser la marque ✨", use_container_width=True, type="primary")

    if analyze_btn and url_input:
        with st.spinner("🚀 ScrappingBee analyse le site web... Extraction des couleurs, fonts et identité..."):
            data = get_brand_data(url_input)
            if data:
                st.session_state.brand_data = data
                st.session_state.step = 2
                st.rerun()

# --- PAGE 2 : BRAND DNA (ADN DE MARQUE) ---
elif st.session_state.step == 2:
    data = st.session_state.brand_data
    
    # Header
    st.markdown(f"<div class='brand-header'>{data.get('projectName', 'Brand Name')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='brand-tagline'>{data.get('tagline', '')}</div>", unsafe_allow_html=True)
    
    # Layout Grille
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown("### 🧬 Concept & Industrie")
        st.info(f"**Industrie:** {data.get('industry', 'N/A')}\n\n**Concept:** {data.get('concept', 'N/A')}")
        
        st.markdown("### 🎨 Palette de Couleurs")
        colors_html = ""
        if data.get('colors'):
            for c in data['colors']:
                hex_val = c.get('hex_code', '#000')
                colors_html += f"<div class='color-circle' style='background-color: {hex_val};' title='{hex_val}'></div>"
        st.markdown(colors_html, unsafe_allow_html=True)

        st.markdown("### 🖋️ Typographie & Ton")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.caption("Fonts")
            if data.get('fonts'):
                for f in data['fonts']:
                    st.markdown(f"**{f.get('font_name')}** ({f.get('use')})")
        with f_col2:
            st.caption("Ton de voix")
            if data.get('tone'):
                tones = [t.get('keyword') for t in data['tone']]
                st.markdown(", ".join(tones))

    with c2:
        st.markdown("### 📸 Imagerie détectée")
        # Affichage grille simple des images scrappées
        if data.get('images'):
            # On prend max 4 images pour pas surcharger
            for img in data['images'][:4]:
                if img.get('src'):
                    st.image(img.get('src'), use_column_width=True)

    st.divider()
    
    # Bouton d'action
    gen_col1, gen_col2, gen_col3 = st.columns([1,2,1])
    with gen_col2:
        if st.button("✨ Générer Idées de Campagnes & Mockups IA", type="primary", use_container_width=True):
            st.session_state.step = 3 # Transition immédiate pour afficher le spinner
            st.rerun()

# --- PAGE 3 : CAMPAGNES & MOCKUPS ---
elif st.session_state.step == 3:
    
    # Logique de génération (si pas encore fait)
    if not st.session_state.campaigns:
        with st.status("🧠 Création des campagnes en cours...", expanded=True) as status:
            st.write("💡 Gemini analyse l'ADN de la marque pour trouver des concepts...")
            campaign_data = generate_campaign_strategy(st.session_state.brand_data)
            st.write("🎨 Création des prompts d'image ultra-détaillés...")
            
            # Génération des images (on itère sur les campagnes)
            final_campaigns = []
            for i, camp in enumerate(campaign_data):
                st.write(f"📸 Génération du mockup haute qualité pour : {camp['campaign_name']}...")
                prompt = camp['image_prompt_structure']['final_constructed_prompt']
                
                # Appel API Image (C'est ici que la magie opère)
                img_obj = generate_image_from_prompt(prompt)
                
                camp['generated_image'] = img_obj
                final_campaigns.append(camp)
            
            st.session_state.campaigns = final_campaigns
            status.update(label="Campagnes prêtes !", state="complete", expanded=False)
            time.sleep(1) # Petit temps pour voir le vert

    # Affichage des résultats
    st.markdown("## 🚀 Stratégies Marketing & Mockups IA")
    
    for campaign in st.session_state.campaigns:
        with st.container():
            st.markdown(f"### {campaign['campaign_name']}")
            
            c_text, c_img = st.columns([1, 1])
            
            with c_text:
                st.markdown(f"**Concept :** {campaign['campaign_description']}")
                with st.expander("Voir le prompt technique utilisé pour l'image"):
                    st.code(campaign['image_prompt_structure']['final_constructed_prompt'], language="text")
            
            with c_img:
                if campaign.get('generated_image'):
                    st.image(campaign['generated_image'], caption="Mockup Instagram généré par IA", use_column_width=True)
                else:
                    st.warning("L'image n'a pas pu être générée (Filtres de sécurité ou quota).")
            
            st.divider()

    if st.button("Recommencer"):
        st.session_state.clear()
        st.rerun()
