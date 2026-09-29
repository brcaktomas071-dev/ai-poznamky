import streamlit as st
import google.generativeai as genai
import json
import re
from PIL import Image

# ==========================================
# 1. NASTAVENIE STRÁNKY
# ==========================================
st.set_page_config(
    page_title="BrainBoost | AI Študijný Parťák",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. CUSTOM CSS (Astra AI moderný štýl)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

    .stApp {
        background: radial-gradient(circle at center, #1a1a2e 0%, #0f0f1a 100%);
        font-family: 'Outfit', sans-serif;
        color: #e2e8f0;
    }
    
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Hero Section */
    .hero-container {
        text-align: center;
        padding-top: 2vh;
        padding-bottom: 3vh;
    }
    .hero-title {
        font-size: 3.8rem !important;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 15px;
        color: white;
    }
    .pixel-text {
        font-family: 'Courier New', Courier, monospace;
        font-weight: 900;
        text-shadow: 2px 2px 0px rgba(255,255,255,0.2);
    }
    .hero-subtitle {
        font-size: 1.25rem;
        color: #94a3b8;
        font-weight: 300;
        margin-bottom: 25px;
    }

    /* Styling pre Streamlit kontajnery (Glassmorphism obdĺžniky zabalené okolo obsahu) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 24px !important;
        padding: 24px !important;
        backdrop-filter: blur(16px) !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4) !important;
    }

    .card-heading {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin-bottom: 15px !important;
    }

    /* Tlačidlá pre obtiažnosť NOOB - HRÁČ - BOSS (Veľké, horizontálne zľava doprava) */
    div[data-testid="stRadio"] {
        width: 100%;
    }

    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: row !important;
        gap: 12px !important;
        justify-content: space-between !important;
        width: 100% !important;
    }

    div[data-testid="stRadio"] > div > label {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
        padding: 18px 10px !important;
        flex: 1 !important;
        text-align: center !important;
        cursor: pointer !important;
        transition: all 0.25s ease !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    div[data-testid="stRadio"] > div > label:hover {
        background: rgba(124, 58, 237, 0.25) !important;
        border-color: #8b5cf6 !important;
        transform: translateY(-2px) !important;
    }

    div[data-testid="stRadio"] > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        border-color: #a855f7 !important;
        box-shadow: 0 8px 20px rgba(124, 58, 237, 0.5) !important;
    }

    /* Skrytie krúžku v radio buttonoch pre čistý tlačidlový vzhľad */
    div[data-testid="stRadio"] input[type="radio"] {
        display: none !important;
    }

    div[data-testid="stRadio"] label p {
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        margin: 0 !important;
    }

    /* Hlavné akčné tlačidlo */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        padding: 18px 32px !important;
        border-radius: 50px !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        box-shadow: 0 10px 30px rgba(124, 58, 237, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin-top: 15px !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 35px rgba(124, 58, 237, 0.6) !important;
    }

    /* Výsledkový Box pre Výcuc */
    .result-box {
        background: rgba(15, 23, 42, 0.8);
        border-left: 5px solid #7c3aed;
        border-radius: 16px;
        padding: 25px;
        color: #f1f5f9;
        font-size: 1.1rem;
        line-height: 1.8;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNKCIE (JSON & AI Volanie)
# ==========================================
def parsuj_json_odpoved(raw_text):
    """Bezpečne vytiahne a preloží JSON z odpovede AI."""
    if not raw_text:
        raise ValueError("AI vrátila prázdnu odpoveď.")
    
    cleaned = raw_text.strip()
    cleaned = re.sub(r'^```json\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'```$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start_idx = cleaned.find('{')
    end_idx = cleaned.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_candidate = cleaned[start_idx:end_idx + 1]
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            json_fixed = re.sub(r',\s*([}\]])', r'\1', json_candidate)
            return json.loads(json_fixed)
            
    raise ValueError("Nepodarilo sa spracovať JSON od AI. Skús to prosím znova.")

def generuj_obsah_dynamicky(api_key, prompt, image):
    """Vyskúša dostupné modely a vygeneruje čistý JSON."""
    genai.configure(api_key=api_key)
    
    dostupne_modely = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                name = m.name.replace("models/", "")
                dostupne_modely.append(name)
    except Exception as e:
        raise Exception(f"Chyba pri overovaní API kľúča: {e}")

    if not dostupne_modely:
         raise Exception("Tvoj API kľúč nemá prístup k žiadnym modelom Gemini.")

    preferovane = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash', 'gemini-1.5-flash-latest']
    zoradene_modely = [m for m in preferovane if m in dostupne_modely]
    for m in dostupne_modely:
        if m not in zoradene_modely:
            zoradene_modely.append(m)

    posledna_chyba = None
    for model_name in zoradene_modely:
        try:
            m_obj = genai.GenerativeModel(model_name)
            try:
                # Zapnutie striktného JSON režimu
                resp = m_obj.generate_content(
                    [prompt, image],
                    generation_config={"response_mime_type": "application/json"}
                )
            except Exception:
                resp = m_obj.generate_content([prompt, image])
                
            if resp and resp.text:
                return resp.text
        except Exception as e:
            posledna_chyba = e
            continue
            
    raise Exception(f"Nepodarilo sa spojiť so žiadnym modelom. Posledná chyba: {posledna_chyba}")

# ==========================================
# 4. UŽÍVATEĽSKÉ ROZHRANIE
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Nastavenia")
    api_key = st.text_input(
        "Vlož svoj Gemini API kľúč:",
        type="password",
        help="Získaš ho na aistudio.google.com"
    )
    if not api_key:
        st.warning("👈 Najprv tu vlož API kľúč!")
    else:
        st.success("API kľúč aktívny ✓")

# Hero Nadpis
st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">Priprav sa na <span class="pixel-text">skúšky</span><br>2x rýchlejšie s AI</h1>
        <p class="hero-subtitle">Vyfoť si poznámky zo zošita a AI ťa z nich okamžite vyskúša.</p>
    </div>
""", unsafe_allow_html=True)

# Dva hlavné obdĺžniky umiestnené presne okolo obsahu
col1, col2 = st.columns(2, gap="medium")

with col1:
    with st.container(border=True):
        st.markdown("<div class='card-heading'>📸 1. Nahraj poznámky</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
        if uploaded_file:
            st.image(uploaded_file, caption="Pripravené na analýzu", use_container_width=True)

with col2:
    with st.container(border=True):
        st.markdown("<div class='card-heading'>🎯 2. Nastav obtiažnosť</div>", unsafe_allow_html=True)
        uroven = st.radio(
            "",
            ("🟢 NOOB", "🟡 HRÁČ", "🔴 BOSS"),
            index=1,
            horizontal=True,
            label_visibility="collapsed"
        )

st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("Začni zadarmo (Spustiť BrainBoost)", use_container_width=True)

# ==========================================
# 5. GENERAVANIE A VYHODNOTENIE
# ==========================================
if generate_btn:
    if not api_key:
        st.error("⚠️ Zabudol si zadať API kľúč v ľavom paneli!")
    elif not uploaded_file:
        st.error("📸 Najprv nahraj fotku poznámok!")
    else:
        with st.spinner("✨ Kúzlim... AI číta tvoje poznámky a pripravuje výcuc aj kvíz..."):
            try:
                image = Image.open(uploaded_file)
                prompt = f"""
                Si super inteligentný a priateľský študijný mentor.
                Prečítaj si obrázok s poznámkami a vytvor odpoveď VÝHRADNE v JSON formáte.

                Obtiažnosť kvízu: {uroven}

                VYŽADOVANÝ JSON FORMÁT (presne dodrž názvy kľúčov):
                {{
                  "vycuc": "Sem daj svoj prehľadný výcuc učiva v markdown formáte...",
                  "test": [
                    {{
                      "otazka": "Znenie otázky?",
                      "moznosti": ["Možnosť 1", "Možnosť 2", "Možnosť 3"],
                      "spravna_odpoved_index": 0,
                      "vysvetlenie": "Stručné vtipné vysvetlenie prečo je to tak"
                    }}
                  ]
                }}
                """
                
                raw_text = generuj_obsah_dynamicky(api_key, prompt, image)
                json_data = parsuj_json_odpoved(raw_text)
                
                st.session_state['data'] = json_data
                st.session_state['test_vyhodnoteny'] = False
                st.success("🎉 Výcuc a kvíz sú hotové!")

            except Exception as e:
                st.error(f"❌ Došlo k chybe: {e}")

# Zobrazenie výsledkov
if 'data' in st.session_state:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📖 Rýchly Výcuc Látky", "🎮 Otestuj svoje vedomosti"])
    
    with tab1:
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown(st.session_state['data']['vycuc'])
        st.markdown("</div>", unsafe_allow_html=True)
        
    with tab2:
        with st.container(border=True):
            st.markdown("### 🔥 Aréna je pripravená")
            with st.form("quiz_form"):
                answers = []
                for idx, q in enumerate(st.session_state['data']['test']):
                    st.markdown(f"**{idx+1}. {q['otazka']}**")
                    ans = st.radio("Vyber si:", q['moznosti'], key=f"q_{idx}", index=None, label_visibility="collapsed")
                    answers.append(ans)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                submitted = st.form_submit_button("🏆 Vyhodnotiť moje odpovede", use_container_width=True)
                if submitted:
                    if None in answers:
                        st.warning("⚠️ Neulievaj sa! Odpovedz na všetky otázky pred vyhodnotením.")
                    else:
                        st.session_state['test_vyhodnoteny'] = True
                        st.session_state['user_answers'] = answers

if st.session_state.get('test_vyhodnoteny'):
    with st.container(border=True):
        st.markdown("## 📊 Tvoj Finálny Report")
        score = 0
        questions = st.session_state['data']['test']
        user_ans = st.session_state['user_answers']
        
        for i, q in enumerate(questions):
            correct_text = q['moznosti'][q['spravna_odpoved_index']]
            if user_ans[i] == correct_text:
                score += 1
                st.success(f"**{i+1}. Správne!** {q['vysvetlenie']}")
            else:
                st.error(f"**{i+1}. Zle!** Tvoja odpoveď: '{user_ans[i]}', Správna: '{correct_text}'")
                st.info(f"💡 Dôvod: {q['vysvetlenie']}")
                
        pct = int((score / len(questions)) * 100)
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("Skóre", f"{score} z {len(questions)}")
        with col_res2:
            st.metric("Úspešnosť", f"{pct}%")
            
        if pct >= 80:
            st.balloons()
