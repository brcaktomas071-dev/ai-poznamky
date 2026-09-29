import streamlit as st
import google.generativeai as genai
import json
import re
from PIL import Image

# 1. Nastavenie stránky
st.set_page_config(
    page_title="BrainBoost 🚀 | AI Študijný Parťák",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS pre moderný, profesionálny dark-mode vzhľad
st.markdown("""
    <style>
    /* Hlavný pozadie a písmo */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hero Header */
    .hero-title {
        font-size: 2.8rem !important;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }
    
    /* Karty pre sekcie */
    .custom-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .card-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Výcuc Box */
    .vycuc-box {
        background: rgba(15, 23, 42, 0.6);
        border-left: 4px solid #818cf8;
        border-radius: 8px;
        padding: 20px;
        color: #e2e8f0;
        font-size: 1.05rem;
        line-height: 1.7;
    }

    /* Badge */
    .status-badge {
        background: #0ea5e9;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar pre konfiguráciu
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/brain.png", width=70)
    st.title("BrainBoost Config")
    st.markdown("---")
    
    st.subheader("🔑 API Nastavenia")
    api_key = st.text_input(
        "Vlož Google Gemini API kľúč:",
        type="password",
        help="Kľúč získaš zadarmo na aistudio.google.com"
    )
    
    if api_key:
        st.success("API kľúč je vložený! 🟢")
    else:
        st.warning("Zadaj kľúč pre aktiváciu AI 🔴")
        
    st.markdown("---")
    st.markdown("### 💡 Ako na to?")
    st.markdown("1. Nahraj jasnú fotku poznámok.\n2. Zvoľ náročnosť kvízu.\n3. Klikni na **Spustiť BrainBoost**.")

# 4. Hlavný obsah
st.markdown("<div class='status-badge'>AI STUDY COMPANION v2.0</div>", unsafe_allow_html=True)
st.markdown("<h1 class='hero-title'>🧠 BrainBoost</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-subtitle'>Premeň rukou písané poznámky na super-zrozumiteľný výcuc a interaktívny kvíz.</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown("""
        <div class='card-title'>📸 1. Nahratie Poznámok</div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Vyber alebo presuň fotku zo zošita",
        type=["jpg", "png", "jpeg"],
        label_visibility="collapsed"
    )
    if uploaded_file:
        st.image(uploaded_file, caption="Nahrávaná fotka", use_container_width=True)

with col2:
    st.markdown("""
        <div class='card-title'>🎯 2. Výber Náročnosti Arény</div>
    """, unsafe_allow_html=True)
    uroven = st.radio(
        "Zvoľ si výzvu:",
        (
            "🟢 Lvl 1: Noob (80% ľahké, 20% stredné)",
            "🟡 Lvl 2: Hráč (30% ľahké, 60% stredné, 10% ťažké)",
            "🔴 Lvl 3: Boss (10% ľahké, 10% stredné, 80% ťažké)"
        ),
        index=1
    )
    
st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("🚀 Spustiť AI BrainBoost!", type="primary", use_container_width=True)

# 5. Bezpečná funkcia pre volanie Gemini modelov s fallbackom
def generuj_obsah_s_fallbackom(api_key, prompt, image):
    genai.configure(api_key=api_key)
    
    # Zoznam stabilných aktívnych modelov
    prioritne_modely = [
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash-exp"
    ]
    
    posledna_chyba = None
    for model_name in prioritne_modely:
        try:
            m_obj = genai.GenerativeModel(model_name)
            resp = m_obj.generate_content([prompt, image])
            if resp and resp.text:
                return resp.text
        except Exception as e:
            posledna_chyba = e
            continue
            
    raise Exception(f"Nepodarilo sa spojiť so žiadnym funkčným Gemini modelom. Detaily: {posledna_chyba}")

# 6. Logika generovania
if generate_btn:
    if not api_key:
        st.error("⚠️ Prosím, vlož svoj Google Gemini API kľúč v ľavom bočnom paneli!")
    elif not uploaded_file:
        st.error("📸 Nahraj prosím fotku poznámok!")
    else:
        with st.spinner("⚡ AI študuje tvoje poznámky a pripravuje výcuc a kvíz..."):
            try:
                image = Image.open(uploaded_file)
                prompt = f"""
                Si priateľský, vtipný a múdry študijný mentor.
                Prečítaj si obrázok s poznámkami a vytvor odpoveď STRICTNE v nasledujúcom JSON formáte.
                Nevracaj žiadny markdown obal okrem čistého JSON.

                Pravidlá pre "vycuc":
                - Vysvetli tému jednoducho a názorne s vtipnými prirovnaniami.
                - Použi prehľadné odrážky, tučné písmo a emoji.

                Pravidlá pre "test":
                - Vygeneruj presne 10 otázok pre úroveň: {uroven}.
                - Pre každú otázku uveď 3 možnosti a index správnej odpovede (0, 1 alebo 2).
                - Pridaj krátke naučné vysvetlenie.

                JSON FORMÁT:
                {{
                  "vycuc": "Text výcucu v markdown...",
                  "test": [
                    {{
                      "otazka": "Znenie otázky?",
                      "moznosti": ["Možnosť A", "Možnosť B", "Možnosť C"],
                      "spravna_odpoved_index": 0,
                      "vysvetlenie": "Vysvetlenie prečo..."
                    }}
                  ]
                }}
                """
                
                raw_text = generuj_obsah_s_fallbackom(api_key, prompt, image)
                
                # Vytiahnutie čistého JSONu
                match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if match:
                    json_data = json.loads(match.group(0))
                    st.session_state['data'] = json_data
                    st.session_state['test_vyhodnoteny'] = False
                    st.session_state['image'] = image
                    st.success("🎉 Výcuc a kvíz sú pripravené!")
                else:
                    st.error("AI vrátila neplatný formát dát. Skús to znova.")
            except Exception as e:
                st.error(f"❌ Došlo k chybe: {e}")

# 7. Zobrazenie výsledkov
if 'data' in st.session_state:
    st.markdown("---")
    tab1, tab2 = st.tabs(["📖 Interaktívny Výcuc", "🎮 Kvízová Aréna"])
    
    with tab1:
        st.markdown("<div class='vycuc-box'>", unsafe_allow_html=True)
        st.markdown(st.session_state['data']['vycuc'])
        st.markdown("</div>", unsafe_allow_html=True)
        
    with tab2:
        st.subheader("Otestuj sa!")
        with st.form("quiz_form"):
            answers = []
            for idx, q in enumerate(st.session_state['data']['test']):
                st.markdown(f"**{idx+1}. {q['otazka']}**")
                ans = st.radio("Vyber odpoveď:", q['moznosti'], key=f"q_{idx}", index=None)
                answers.append(ans)
                st.markdown("<br>", unsafe_allow_html=True)
                
            submitted = st.form_submit_button("🏆 Vyhodnotiť test", use_container_width=True)
            if submitted:
                if None in answers:
                    st.warning("Odpovedaj prosím na všetky otázky!")
                else:
                    st.session_state['test_vyhodnoteny'] = True
                    st.session_state['user_answers'] = answers

if st.session_state.get('test_vyhodnoteny'):
    st.markdown("### 📊 Výsledok Kvízu")
    score = 0
    questions = st.session_state['data']['test']
    user_ans = st.session_state['user_answers']
    
    for i, q in enumerate(questions):
        correct_text = q['moznosti'][q['spravna_odpoved_index']]
        if user_ans[i] == correct_text:
            score += 1
            st.success(f"**{i+1}. Správne!** {q['vysvetlenie']}")
        else:
            st.error(f"**{i+1}. Nesprávne.** Tvoja odpoveď: {user_ans[i]} | Správna: {correct_text}")
            st.info(f"💡 {q['vysvetlenie']}")
            
    pct = int((score / len(questions)) * 100)
    st.metric("Tvoje Skóre", f"{score} / {len(questions)} ({pct}%)")
    if pct >= 80:
        st.balloons()
