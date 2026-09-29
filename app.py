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

# Inicializácia stavov
if 'page' not in st.session_state:
    st.session_state['page'] = 1
if 'data' not in st.session_state:
    st.session_state['data'] = None
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ""

# ==========================================
# 2. CUSTOM CSS (Tech štýl, hrubý farebný slider, menší obrazok)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&display=swap');

    .stApp {
        background: radial-gradient(circle at center, #0f172a 0%, #020617 100%);
        font-family: 'Outfit', sans-serif;
        color: #f8fafc;
    }
    
    #MainMenu, header, footer {visibility: hidden;}

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
        text-shadow: 0 0 10px #0ea5e9, 0 0 20px #0ea5e9, 0 0 40px #3b82f6;
        transition: all 0.4s ease-in-out;
        cursor: pointer;
        display: inline-block;
    }

    .glow-title:hover {
        text-shadow: 0 0 20px #3b82f6, 0 0 40px #60a5fa, 0 0 80px #93c5fd;
        transform: scale(1.05);
    }

    .book-container {
        max-width: 850px;
        margin: 0 auto;
        background: rgba(15, 23, 42, 0.85);
        border: 2px solid #3b82f6;
        border-radius: 28px;
        padding: 40px;
        box-shadow: 0 0 35px rgba(59, 130, 246, 0.35), inset 0 0 15px rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        position: relative;
    }

    /* Klikateľné záložky hore na prepínanie stránok */
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
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .tab-item:hover {
        border-color: #0ea5e9;
        color: #ffffff;
    }

    .tab-item.active {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
        color: #ffffff;
        border-color: #60a5fa;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.6);
    }

    /* =========================================
       HRUBÁ A ŽIARIVÁ FAREBNÁ ČIARA (SLIDER)
       ========================================= */
    .stSlider {
        padding-top: 35px !important;
        padding-bottom: 25px !important;
    }
    
    .stSlider [data-baseweb="slider"] {
        background: linear-gradient(to right, #22c55e 0%, #eab308 50%, #ef4444 100%) !important;
        height: 18px !important;
        border-radius: 12px !important;
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.4), 0 0 20px rgba(239, 68, 68, 0.4);
    }
    
    .stSlider [data-baseweb="slider"] > div {
        background: transparent !important;
    }
    
    .stSlider [role="slider"] {
        background: #ffffff !important;
        border: 4px solid #0ea5e9 !important;
        width: 30px !important;
        height: 30px !important;
        border-radius: 50% !important;
        box-shadow: 0 0 15px rgba(14, 165, 233, 0.8) !important;
    }

    div[data-testid="stThumbValue"] { display: none !important; }

    /* Menší box pre náhľad nahratého obrázka */
    .image-preview-container {
        max-width: 320px;
        margin: 15px auto;
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }

    .stButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        padding: 20px 30px !important;
        border-radius: 50px !important;
        font-size: 1.3rem !important;
        font-weight: 900 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        box-shadow: 0 0 25px rgba(14, 165, 233, 0.5) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin-top: 20px !important;
    }

    .stButton>button:hover {
        transform: scale(1.02) translateY(-2px) !important;
        box-shadow: 0 0 40px rgba(14, 165, 233, 0.8) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNKCIE & DYNAMICKÉ AI MODELY
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
    
    # Zistenie dostupných modelov, aby nenaskočila 404 chyba
    dostupne_modely = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                name = m.name.replace("models/", "")
                dostupne_modely.append(name)
    except Exception:
        pass

    preferovane = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    zoradene = [m for m in preferovane if m in dostupne_modely]
    for m in dostupne_modely:
        if m not in zoradene:
            zoradene.append(m)
            
    if not zoradene:
        zoradene = ['gemini-2.5-flash', 'gemini-1.5-flash'] # fallback

    posledna_chyba = None
    for model_name in zoradene:
        try:
            m_obj = genai.GenerativeModel(model_name)
            try:
                resp = m_obj.generate_content([prompt, image], generation_config={"response_mime_type": "application/json"})
            except Exception:
                resp = m_obj.generate_content([prompt, image])
            if resp and resp.text:
                return resp.text
        except Exception as e:
            posledna_chyba = e
            continue
            
    raise Exception(f"Nepodarilo sa pripojiť k AI modelom: {posledna_chyba}")

# ==========================================
# 4. HLAVNÝ NADPIS
# ==========================================
st.markdown("""
    <div class="glow-title-container">
        <div class="glow-title">OTESTUJ SA!</div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 5. KLIKATEĽNÉ ZÁLOŽKY NA PREPÍNANIE STRÁN
# ==========================================
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("1. Kľúč & Poznámky", use_container_width=True):
        st.session_state['page'] = 1
        st.rerun()
with c2:
    if st.button("2. Náročnosť testu", use_container_width=True):
        st.session_state['page'] = 2
        st.rerun()
with c3:
    if st.button("3. Test & Výsledky", use_container_width=True):
        st.session_state['page'] = 3
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 6. OBSAH KNIHY (3 STRANY)
# ==========================================
with st.container():
    st.markdown('<div class="book-container">', unsafe_allow_html=True)

    # STRANA 1
    if st.session_state['page'] == 1:
        st.markdown("<h2 style='text-align: center; color:#38bdf8;'>📸 STRANA 1: Kľúč & Poznámky</h2>", unsafe_allow_html=True)
        st.write(" ")
        
        api_key_input = st.text_input("🔑 Vlož Gemini API kľúč:", value=st.session_state['api_key'], type="password")
        if api_key_input:
            st.session_state['api_key'] = api_key_input
            
        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("📸 Nahraj fotku zošita:", type=["jpg", "png", "jpeg"])
        
        if uploaded_file:
            st.session_state['uploaded_file'] = uploaded_file
            st.markdown('<div class="image-preview-container">', unsafe_allow_html=True)
            st.image(uploaded_file, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ĎALEJ NA VÝBER NÁROČNOSTI ➔"):
            if not st.session_state['api_key']:
                st.error("⚠️ Najprv vlož API kľúč!")
            elif 'uploaded_file' not in st.session_state or not st.session_state['uploaded_file']:
                st.error("⚠️ Najprv nahraj fotku poznámok!")
            else:
                st.session_state['page'] = 2
                st.rerun()

    # STRANA 2
    elif st.session_state['page'] == 2:
        st.markdown("<h2 style='text-align: center; color:#38bdf8;'>🎯 STRANA 2: Nastav náročnosť testu</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color:#94a3b8;'>Posúvaj posuvník po farebnej línii. Zelená = ľahké základy, Žltá = štandard, Červená = extrémne náročné.</p>", unsafe_allow_html=True)
        st.write(" ")
        
        slider_hodnota = st.slider("", 0, 100, 50, label_visibility="collapsed")
        
        if slider_hodnota <= 33:
            obtiaznost_text = "Úplné základy (najľahšia úroveň pre začiatočníkov)."
        elif slider_hodnota <= 66:
            obtiaznost_text = "Stredná úroveň (štandardné otázky, bežný test)."
        else:
            obtiaznost_text = "Najťažšia úroveň (chytáky, hlboké detaily a ťažké otázky)."

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔥 VYGENEROVAŤ TEST 🔥", use_container_width=True):
            if not st.session_state.get('api_key') or not st.session_state.get('uploaded_file'):
                st.error("⚠️ Najprv skontroluj, či máš zadaný API kľúč a nahraný obrázok na 1. strane!")
                st.session_state['page'] = 1
                st.rerun()
            else:
                with st.spinner("✨ AI číta poznámky a vytvára test..."):
                    try:
                        image = Image.open(st.session_state['uploaded_file'])
                        prompt = f"""
                        Prečítaj si obrázok s poznámkami a vytvor z nich kvíz.
                        Náročnosť otázok: {obtiaznost_text}
                        
                        Odpovedaj VÝHRADNE v JSON formáte:
                        {{
                          "vycuc": "Krátky prehľad učiva v Markdown formáte...",
                          "test": [
                            {{
                              "otazka": "Znenie otázky?",
                              "moznosti": ["Možnosť A", "Možnosť B", "Možnosť C"],
                              "spravna_odpoved_index": 0,
                              "vysvetlenie": "Prečo je to správne"
                            }}
                          ]
                        }}
                        """
                        raw_text = generuj_obsah_dynamicky(st.session_state['api_key'], prompt, image)
                        st.session_state['data'] = parsuj_json_odpoved(raw_text)
                        st.session_state['page'] = 3
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Chyba pri generovaní: {e}")

    # STRANA 3
    elif st.session_state['page'] == 3:
        st.markdown("<h2 style='text-align: center; color:#38bdf8;'>🎮 STRANA 3: Tvoj Test & Výsledky</h2>", unsafe_allow_html=True)
        st.write(" ")

        if st.session_state['data']:
            data = st.session_state['data']
            
            with st.expander("📖 Prečítať si rýchly výcuc poznámok"):
                st.markdown(data.get('vycuc', ''))

            st.markdown("---")
            
            with st.form("quiz_form_book"):
                user_answers = []
                for idx, q in enumerate(data['test']):
                    st.markdown(f"**{idx+1}. {q['otazka']}**")
                    ans = st.radio("Odpoveď:", q['moznosti'], key=f"book_q_{idx}", index=None, label_visibility="collapsed")
                    user_answers.append(ans)
                    st.markdown("<br>", unsafe_allow_html=True)

                submit_quiz = st.form_submit_button("🏆 VYHODNOTIŤ TEST", use_container_width=True)

                if submit_quiz:
                    if None in user_answers:
                        st.warning("⚠️ Odpovedz na všetky otázky pred vyhodnotením!")
                    else:
                        st.session_state['quiz_submitted'] = True
                        st.session_state['user_answers'] = user_answers

            if st.session_state.get('quiz_submitted'):
                st.markdown("### 📊 Výsledný Report")
                score = 0
                questions = data['test']
                u_ans = st.session_state['user_answers']

                for i, q in enumerate(questions):
                    correct_text = q['moznosti'][q['spravna_odpoved_index']]
                    if u_ans[i] == correct_text:
                        score += 1
                        st.success(f"**{i+1}. Správne!** {q['vysvetlenie']}")
                    else:
                        st.error(f"**{i+1}. Nesprávne!** Správna odpoveď bola: {correct_text}")
                        st.info(f"💡 Dôvod: {q['vysvetlenie']}")

                st.balloons()
                st.metric("Skóre", f"{score} z {len(questions)}")
        else:
            st.info("👈 Najprv prejdite 1. a 2. stranu a vygenerujte test.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Začať odznova"):
            st.session_state['page'] = 1
            st.session_state['data'] = None
            st.session_state['quiz_submitted'] = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
