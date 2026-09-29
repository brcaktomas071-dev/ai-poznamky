import streamlit as st
import google.generativeai as genai
import json
import re
from PIL import Image

# ==========================================
# 1. NASTAVENIE STRÁNKY
# ==========================================
st.set_page_config(
    page_title="OTESTUJ SA! | AI Kniha",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicializácia stavov prehliadania knihy (Strana 1 až 3)
if 'page' not in st.session_state:
    st.session_state['page'] = 1
if 'data' not in st.session_state:
    st.session_state['data'] = None
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ""

# ==========================================
# 2. CUSTOM CSS - TECH MODRÁ & MOZGOVÝ SLIDER
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&display=swap');

    .stApp {
        /* Odstránená fialová/ružová, nahradená tmavou tech modrou/bridlicovou */
        background: radial-gradient(circle at center, #0f172a 0%, #020617 100%);
        font-family: 'Outfit', sans-serif;
        color: #f8fafc;
    }
    
    #MainMenu, header, footer {visibility: hidden;}

    /* Interaktívny žiarivý nadpis OTESTUJ SA! */
    .glow-title-container {
        text-align: center;
        margin-top: 10px;
        margin-bottom: 25px;
    }
    
    .glow-title {
        font-size: 4.5rem !important;
        font-weight: 900;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 3px;
        /* Modro-tyrkysové žiarenie miesto fialovej */
        text-shadow: 0 0 10px #0ea5e9, 0 0 20px #0ea5e9, 0 0 40px #3b82f6;
        transition: all 0.4s ease-in-out;
        cursor: pointer;
        display: inline-block;
    }

    .glow-title:hover {
        text-shadow: 0 0 20px #3b82f6, 0 0 40px #60a5fa, 0 0 80px #93c5fd, 0 0 120px #93c5fd;
        transform: scale(1.05);
        color: #ffffff;
    }

    /* 3D Kniha pri pohľade zhora - Modrý štýl */
    .book-container {
        max-width: 900px;
        margin: 0 auto;
        background: rgba(15, 23, 42, 0.85);
        border: 2px solid #3b82f6;
        border-radius: 28px;
        padding: 40px;
        box-shadow: 0 0 35px rgba(59, 130, 246, 0.35), inset 0 0 15px rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        position: relative;
    }

    /* Horné záložky (Paging Indicator) */
    .book-tabs {
        display: flex;
        justify-content: center;
        gap: 15px;
        margin-bottom: 30px;
    }

    .tab-item {
        padding: 8px 24px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.95rem;
        background: rgba(255, 255, 255, 0.05);
        color: #94a3b8;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .tab-item.active {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
        color: #ffffff;
        border-color: #60a5fa;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.6);
    }

    /* =========================================
       CUSTOM SLIDER - MOZOG + ZELENÁ-ŽLTÁ-ČERVENÁ ČIARA
       ========================================= */
    
    /* Obal slideru pre extra priestor hore/dole */
    .stSlider {
        padding-top: 30px !important;
        padding-bottom: 20px !important;
    }
    
    /* Samotná farebná čiara s gradientom */
    .stSlider [data-baseweb="slider"] {
        background: linear-gradient(to right, #22c55e 0%, #eab308 50%, #ef4444 100%) !important;
        height: 14px !important;
        border-radius: 10px !important;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.1);
    }
    
    /* Zneviditeľnenie pôvodného modrého "vyplnenia", aby bolo vidieť celý náš gradient */
    .stSlider [data-baseweb="slider"] > div {
        background: transparent !important;
    }
    
    /* Vlastný ukazovateľ (zrušíme pôvodný krúžok) */
    .stSlider [role="slider"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Vloženie 🧠 emoji namiesto guličky */
    .stSlider [role="slider"]::after {
        content: "🧠";
        font-size: 45px;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        filter: drop-shadow(0 5px 10px rgba(0,0,0,0.7));
        cursor: grab;
    }

    .stSlider [role="slider"]:active::after {
        cursor: grabbing;
        transform: translate(-50%, -50%) scale(1.1);
    }
    
    /* Skrytie čísiel na čiare slidera */
    div[data-testid="stThumbValue"] { display: none !important; }

    /* Obrovské Žiarivé Tlačidlo (Teraz Modro/Tyrkysové) */
    .stButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        padding: 22px 30px !important;
        border-radius: 50px !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        box-shadow: 0 0 30px rgba(14, 165, 233, 0.6), 0 0 50px rgba(37, 99, 235, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin-top: 30px !important;
    }

    .stButton>button:hover {
        transform: scale(1.02) translateY(-2px) !important;
        box-shadow: 0 0 50px rgba(14, 165, 233, 0.9), 0 0 80px rgba(37, 99, 235, 0.7) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNKCIE
# ==========================================
def parsuj_json_odpoved(raw_text):
    if not raw_text:
        raise ValueError("AI vrátila prázdnu odpoveď.")
    cleaned = raw_text.strip()
    cleaned = re.sub(r'^```json\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'```$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_candidate = cleaned[start_idx:end_idx + 1]
            return json.loads(re.sub(r',\s*([}\]])', r'\1', json_candidate))
    raise ValueError("Chyba spracovania dát od AI. Skús to znova.")

def generuj_obsah_dynamicky(api_key, prompt, image):
    genai.configure(api_key=api_key)
    m_obj = genai.GenerativeModel('gemini-1.5-flash')
    try:
        resp = m_obj.generate_content([prompt, image], generation_config={"response_mime_type": "application/json"})
    except Exception:
        resp = m_obj.generate_content([prompt, image])
    return resp.text


# ==========================================
# 4. HLAVNÝ INTERAKTÍVNY NADPIS
# ==========================================
st.markdown("""
    <div class="glow-title-container">
        <div class="glow-title">OTESTUJ SA!</div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 5. STRANICHOVANIE KNIHY (3 STRANY ZHORA)
# ==========================================
p1_active = "active" if st.session_state['page'] == 1 else ""
p2_active = "active" if st.session_state['page'] == 2 else ""
p3_active = "active" if st.session_state['page'] == 3 else ""

st.markdown(f"""
