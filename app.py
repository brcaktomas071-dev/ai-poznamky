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

# ==========================================
# 2. CUSTOM CSS - 3D KNIHA ZHORA & NEÓNOVÉ EFEKTY
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&display=swap');

    .stApp {
        background: radial-gradient(circle at center, #130a2a 0%, #05030a 100%);
        font-family: 'Outfit', sans-serif;
        color: #f1f5f9;
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
        text-shadow: 0 0 10px #7c3aed, 0 0 20px #7c3aed, 0 0 40px #a855f7;
        transition: all 0.4s ease-in-out;
        cursor: pointer;
        display: inline-block;
    }

    .glow-title:hover {
        text-shadow: 0 0 20px #a855f7, 0 0 40px #c084fc, 0 0 80px #38bdf8, 0 0 120px #38bdf8;
        transform: scale(1.05);
        color: #ffffff;
    }

    /* 3D Kniha pri pohľade zhora */
    .book-container {
        max-width: 900px;
        margin: 0 auto;
        background: rgba(20, 15, 38, 0.85);
        border: 2px solid #a855f7;
        border-radius: 28px;
        padding: 40px;
        box-shadow: 0 0 35px rgba(168, 85, 247, 0.35), inset 0 0 15px rgba(255, 255, 255, 0.05);
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
        background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
        color: #ffffff;
        border-color: #c084fc;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.6);
    }

    /* Radio buttony na obtiažnosť na 2. strane */
    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: row !important;
        gap: 15px !important;
        justify-content: space-between !important;
    }

    div[data-testid="stRadio"] > div > label {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 2px solid rgba(168, 85, 247, 0.3) !important;
        border-radius: 18px !important;
        padding: 20px 10px !important;
        flex: 1 !important;
        text-align: center !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }

    div[data-testid="stRadio"] > div > label:hover {
        border-color: #c084fc !important;
        box-shadow: 0 0 20px rgba(192, 132, 252, 0.4) !important;
        transform: translateY(-3px) !important;
    }

    div[data-testid="stRadio"] > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        border-color: #ffffff !important;
        box-shadow: 0 0 25px rgba(168, 85, 247, 0.8) !important;
    }

    div[data-testid="stRadio"] input[type="radio"] { display: none !important; }

    div[data-testid="stRadio"] label p {
        font-size: 1.3rem !important;
        font-weight: 900 !important;
        color: #ffffff !important;
    }

    /* Obrovské Žiarivé Tlačidlo */
    .stButton>button {
        background: linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        padding: 22px 30px !important;
        border-radius: 50px !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        box-shadow: 0 0 30px rgba(236, 72, 153, 0.6), 0 0 50px rgba(168, 85, 247, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin-top: 20px !important;
    }

    .stButton>button:hover {
        transform: scale(1.02) translateY(-2px) !important;
        box-shadow: 0 0 50px rgba(236, 72, 153, 0.9), 0 0 80px rgba(168, 85, 247, 0.7) !important;
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
# 4. POSTRANNÝ PANEL
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Nastavenia")
    api_key = st.text_input("Vlož Gemini API kľúč:", type="password")

# ==========================================
# 5. HLAVNÝ INTERAKTÍVNY NADPIS
# ==========================================
st.markdown("""
    <div class="glow-title-container">
        <div class="glow-title">OTESTUJ SA!</div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 6. STRANICHOVANIE KNIHY (3 STRANY ZHORA)
# ==========================================
p1_active = "active" if st.session_state['page'] == 1 else ""
p2_active = "active" if st.session_state['page'] == 2 else ""
p3_active = "active" if st.session_state['page'] == 3 else ""

st.markdown(f"""
    <div class="book-tabs">
        <div class="tab-item {p1_active}">1. Odfoť poznámky</div>
        <div class="tab-item {p2_active}">2. Obtiažnosť</div>
        <div class="tab-item {p3_active}">3. Test & Výsledky</div>
    </div>
""", unsafe_allow_html=True)

# KNIHA CONTAINER
with st.container():
    st.markdown('<div class="book-container">', unsafe_allow_html=True)

    # ------------------------------------
    # STRANA 1: ODFOŤ / NAHRAJ POZNÁMKY
    # ------------------------------------
    if st.session_state['page'] == 1:
        st.markdown("<h2 style='text-align: center;'>📸 STRANA 1: Odfoť foto poznámok</h2>", unsafe_allow_html=True)
        st.write(" ")
        
        uploaded_file = st.file_uploader("Nahraj fotku zošita alebo poznámok:", type=["jpg", "png", "jpeg"])
        
        if uploaded_file:
            st.session_state['uploaded_file'] = uploaded_file
            st.image(uploaded_file, caption="Nahranný obrázok", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("ĎALEJ NA VÝBER OBTIAŽNOSTI ➔"):
                st.session_state['page'] = 2
                st.rerun()

    # ------------------------------------
    # STRANA 2: OBTIAŽNOSŤ & VEĽKÉ TLAČIDLO
    # ------------------------------------
    elif st.session_state['page'] == 2:
        st.markdown("<h2 style='text-align: center;'>🎯 STRANA 2: Vyber si obtiažnosť</h2>", unsafe_allow_html=True)
        st.write(" ")
        
        uroven = st.radio(
            "",
            ("🟢 NOOB", "🟡 HRÁČ", "🔴 BOSS"),
            index=1,
            horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state['uroven'] = uroven

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Obrovské Žiarivé Tlačidlo
        if st.button("🔥 VYGENEROVAŤ TEST 🔥", use_container_width=True):
            if not api_key:
                st.error("⚠️ Zadaj najprv Gemini API kľúč v ľavom paneli!")
            elif 'uploaded_file' not in st.session_state or not st.session_state['uploaded_file']:
                st.error("⚠️ Vráť sa na 1. stranu a nahraj obrázok!")
            else:
                with st.spinner("✨ Kniha sa otvára na 3. strane... Generating test..."):
                    try:
                        image = Image.open(st.session_state['uploaded_file'])
                        prompt = f"""
                        Prečítaj si obrázok s poznámkami a vytvor kvíz.
                        Obtiažnosť: {uroven}
                        Odpovedaj VÝHRADNE v JSON formáte:
                        {{
                          "vycuc": "Krátky prehľad učiva v Markdown...",
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
                        raw_text = generuj_obsah_dynamicky(api_key, prompt, image)
                        st.session_state['data'] = parsuj_json_odpoved(raw_text)
                        st.session_state['page'] = 3
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Chyba pri generovaní: {e}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ Späť na 1. stranu"):
            st.session_state['page'] = 1
            st.rerun()

    # ------------------------------------
    # STRANA 3: SAMOTNÝ TEST A VÝSLEDKY
    # ------------------------------------
    elif st.session_state['page'] == 3:
        st.markdown("<h2 style='text-align: center;'>🎮 STRANA 3: Test & Vyhodnotenie</h2>", unsafe_allow_html=True)
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
                        st.warning("⚠️ Odpovedz na všetky otázky!")
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

                st.balloons()
                st.metric("Skóre", f"{score} z {len(questions)}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Začať odznova (1. strana)"):
            st.session_state['page'] = 1
            st.session_state['data'] = None
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
