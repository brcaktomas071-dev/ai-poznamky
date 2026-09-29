import streamlit as st
import google.generativeai as genai
import json
import re
from PIL import Image

# ==========================================
# 1. NASTAVENIE STRÁNKY A TÉMY
# ==========================================
st.set_page_config(
    page_title="BrainBoost | AI Študijný Parťák",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed" # Začneme so zbaleným sidebarom pre čistejší look
)

# Custom CSS inšpirované moderným dizajnom (Astra AI style)
st.markdown("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

    /* Hlavné pozadie - Tmavý "vesmírny" vzhľad */
    .stApp {
        background: radial-gradient(circle at center, #1a1a2e 0%, #0f0f1a 100%);
        font-family: 'Outfit', sans-serif;
        color: #e2e8f0;
    }
    
    /* Skrytie predvolených prvkov Streamlitu (čistejší look) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Hlavný Nadpis (Hero Section) */
    .hero-container {
        text-align: center;
        padding-top: 5vh;
        padding-bottom: 5vh;
    }
    .hero-title {
        font-size: 4.5rem !important;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 20px;
        color: white;
    }
    .pixel-text {
        font-family: 'Courier New', Courier, monospace; /* Pixelovaný feel pre slovo "skúšky" */
        font-weight: 900;
        text-shadow: 2px 2px 0px rgba(255,255,255,0.2);
    }
    .hero-subtitle {
        font-size: 1.5rem;
        color: #94a3b8;
        font-weight: 300;
        margin-bottom: 40px;
    }

    /* "Glassmorphism" Karty pre interakciu */
    .action-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 24px;
        padding: 30px;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        margin-bottom: 20px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .action-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 30px 50px rgba(0,0,0,0.5);
    }
    .card-heading {
        font-size: 1.3rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 20px;
        text-align: center;
    }

    /* Moderné Hlavné Tlačidlo */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        padding: 16px 32px !important;
        border-radius: 50px !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        box-shadow: 0 10px 25px rgba(124, 58, 237, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin-top: 20px !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 35px rgba(124, 58, 237, 0.6) !important;
        background: linear-gradient(135deg, #5b52f6 0%, #8b5cf6 100%) !important;
    }

    /* Výsledkový Box (Výcuc) */
    .result-box {
        background: rgba(15, 23, 42, 0.8);
        border-left: 5px solid #7c3aed;
        border-radius: 12px;
        padding: 30px;
        color: #f1f5f9;
        font-size: 1.15rem;
        line-height: 1.8;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.2);
    }

    /* Vlastné Radio buttons (Pokus o čistejší look) */
    .stRadio > label {
        font-weight: 600;
        color: #cbd5e1;
    }
    
    /* Vylepšenie file uploaderu */
    [data-testid="stFileUploadDropzone"] {
        background-color: rgba(255,255,255,0.02) !important;
        border: 2px dashed rgba(255,255,255,0.2) !important;
        border-radius: 16px !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #7c3aed !important;
        background-color: rgba(124, 58, 237, 0.05) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BEZPEČNÉ VOLANIE MODELU (Dynamické zistenie)
# ==========================================
def generuj_obsah_dynamicky(api_key, prompt, image):
    """Zistí dostupné modely a vyskúša ich, čím eliminuje chyby 404."""
    genai.configure(api_key=api_key)
    
    dostupne_modely = []
    try:
        # Dynamicky stiahne zoznam všetkých modelov dostupných pre tvoj kľúč
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # Očistíme názov (odstránime 'models/' ak tam je)
                name = m.name.replace("models/", "")
                dostupne_modely.append(name)
    except Exception as e:
        raise Exception(f"Chyba pri overovaní API kľúča (Zadal si ho správne?): {e}")

    if not dostupne_modely:
         raise Exception("Tvoj API kľúč nemá prístup k žiadnym modelom na generovanie obsahu.")

    # Uprednostníme známe rýchle modely, ak sú v dostupnom zozname
    preferovane = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash']
    zoradene_modely = []
    
    # Najprv pridáme preferované, ktoré účet podporuje
    for p in preferovane:
        if p in dostupne_modely:
            zoradene_modely.append(p)
    # Potom pridáme ostatné
    for m in dostupne_modely:
        if m not in zoradene_modely:
            zoradene_modely.append(m)

    posledna_chyba = None
    # Skúšame jeden model po druhom, kým sa nepodarí
    for model_name in zoradene_modely:
        try:
            m_obj = genai.GenerativeModel(model_name)
            resp = m_obj.generate_content([prompt, image])
            if resp and resp.text:
                return resp.text
        except Exception as e:
            posledna_chyba = e
            continue # Ak tento model zlyhá (napr. na 404), ideme na ďalší
            
    raise Exception(f"Nepodarilo sa vygenerovať odpoveď zo žiadneho dostupného modelu. Posledná chyba: {posledna_chyba}")

# ==========================================
# 3. ROZHRANIE (UI)
# ==========================================

# -- Sidebar (Nastavenia schované naboku) --
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

# -- Hero Section (Hlavná vizuálna dominanta) --
st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">Priprav sa na <span class="pixel-text">skúšky</span><br>2x rýchlejšie s AI</h1>
        <p class="hero-subtitle">Vyfoť si poznámky zo zošita a AI ťa z nich okamžite vyskúša.</p>
    </div>
""", unsafe_allow_html=True)

# -- Interaktívne Karty (Upload a Nastavenie) --
col1, col_space, col2 = st.columns([1, 0.1, 1])

with col1:
    st.markdown("<div class='action-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-heading'>📸 1. Nahraj poznámky</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if uploaded_file:
         st.image(uploaded_file, caption="Pripravené na analýzu", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='action-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-heading'>🎯 2. Nastav obtiažnosť</div>", unsafe_allow_html=True)
    uroven = st.radio(
        "",
        (
            "🟢 Noob (Chcem len pochopiť základy)",
            "🟡 Hráč (Už niečo viem, otestuj ma)",
            "🔴 Boss (Daj mi tie najťažšie chytáky)"
        ),
        index=1,
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# -- Hlavné Spúšťacie Tlačidlo --
generate_btn = st.button("Začni zadarmo (Spustiť BrainBoost)", use_container_width=True)

# ==========================================
# 4. LOGIKA A GENEROVANIE
# ==========================================
if generate_btn:
    if not api_key:
        st.error("⚠️ Hej! Zabudol si si nastaviť API kľúč v ľavom paneli (klikni na šípku vľavo hore).")
    elif not uploaded_file:
        st.error("📸 Najprv musíš nahrať nejakú fotku poznámok, inak nemám čo analyzovať.")
    else:
        with st.spinner("✨ Kúzlim... AI číta tvoje poznámky a vymýšľa otázky..."):
            try:
                image = Image.open(uploaded_file)
                prompt = f"""
                Si ten najlepší, moderný a vtipný študijný mentor.
                Prečítaj si poznámky z obrázka a vytvor odpoveď STRICTNE v nasledujúcom JSON formáte.
                Nevracaj absolútne žiadny iný text, len čistý JSON.

                Pravidlá pre "vycuc":
                - Vysvetli tému tak jednoducho, aby to pochopil aj mimozemšťan.
                - Použi prirovnania, krátke odrážky, tučné písmo na kľúčové slová a občas emoji.

                Pravidlá pre "test":
                - Vymysli presne 10 testových otázok. Obtiažnosť: {uroven}.
                - Každá otázka musí mať 3 možnosti odpovedí.
                - "spravna_odpoved_index" musí byť číslo 0, 1, alebo 2 (označuje správnu možnosť v poli "moznosti").
                - Pridaj "vysvetlenie" - krátky, vtipný dôvod, prečo je to tak.

                JSON FORMÁT:
                {{
                  "vycuc": "Sem daj svoj super vysvetľujúci text vo formáte Markdown...",
                  "test": [
                    {{
                      "otazka": "Tu bude otázka?",
                      "moznosti": ["Odpoveď 1", "Odpoveď 2", "Odpoveď 3"],
                      "spravna_odpoved_index": 0,
                      "vysvetlenie": "Pretože to jednoducho tak funguje!"
                    }}
                  ]
                }}
                """
                
                # Volanie novej "nepriestrelnej" funkcie
                raw_text = generuj_obsah_dynamicky(api_key, prompt, image)
                
                # Očistenie a parsovanie JSONu
                match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if match:
                    json_data = json.loads(match.group(0))
                    st.session_state['data'] = json_data
                    st.session_state['test_vyhodnoteny'] = False
                    st.success("Tadá! Všetko je pripravené. Zoscroľuj nižšie.")
                else:
                    st.error("Model vygeneroval odpoveď, ale v zlom formáte. Skús stlačiť tlačidlo ešte raz.")
            
            except Exception as e:
                st.error(f"❌ Nastala chyba: {e}")

# ==========================================
# 5. ZOBRAZENIE VÝSLEDKOV (Výcuc & Kvíz)
# ==========================================
if 'data' in st.session_state:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Moderné Taby
    tab1, tab2 = st.tabs(["📖 Rýchly Výcuc Látky", "🎮 Otestuj svoje vedomosti"])
    
    with tab1:
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown(st.session_state['data']['vycuc'])
        st.markdown("</div>", unsafe_allow_html=True)
        
    with tab2:
        st.markdown("<div class='action-card'>", unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)

# -- Vyhodnotenie --
if st.session_state.get('test_vyhodnoteny'):
    st.markdown("<div class='action-card'>", unsafe_allow_html=True)
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
            st.error(f"**{i+1}. Zle!** Dal si '{user_ans[i]}', ale správne je '{correct_text}'.")
            st.info(f"💡 Dôvod: {q['vysvetlenie']}")
            
    pct = int((score / len(questions)) * 100)
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("Skóre", f"{score} z {len(questions)}")
    with col_res2:
        st.metric("Úspešnosť", f"{pct}%")
        
    if pct >= 80:
        st.balloons()
    st.markdown("</div>", unsafe_allow_html=True)
