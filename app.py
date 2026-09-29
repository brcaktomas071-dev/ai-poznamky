import streamlit as st
import google.generativeai as genai
import json
import re
from PIL import Image

# 1. Základné nastavenie
st.set_page_config(page_title="BrainBoost 🚀", page_icon="🧠", layout="centered")

st.markdown("""
    <style>
    .big-font { font-size:22px !important; font-weight: bold; color: #4A90E2;}
    .vycuc-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

st.title("🧠 BrainBoost: Z fotky do hlavy za minútu")
st.markdown("Vyfoť poznámky, AI ti to vysvetlí ľudskou rečou a hneď ťa otestuje ako v hre. 🎮")

with st.expander("⚙️ Nastavenia (Klikni pre zadanie API kľúča)", expanded=True):
    api_key = st.text_input("Vlož svoj Google Gemini API kľúč:", type="password")

col1, col2 = st.columns([1, 1])
with col1:
    uploaded_file = st.file_uploader("📸 Nahraj fotku poznámok", type=["jpg", "png", "jpeg"])
with col2:
    st.markdown("<p class='big-font'>Zvoľ si svoju Arénu:</p>", unsafe_allow_html=True)
    uroven = st.radio(
        "Aký ťažký test zvládneš?",
        ("🟢 Lvl 1: Noob (Len to zistím - 80% ľahké, 20% stredné)", 
         "🟡 Lvl 2: Hráč (Už niečo viem - 30% ľahké, 60% stredné, 10% ťažké)", 
         "🔴 Lvl 3: Boss (Poď do mňa - 10% ľahké, 10% stredné, 80% ťažké)"),
        label_visibility="collapsed"
    )

if st.button("🚀 Vygenerovať Výcuc a Hru!", use_container_width=True):
    if not api_key:
        st.error("Zabudol si na API kľúč v nastaveniach! 😅")
    elif not uploaded_file:
        st.error("Kde je fotka? Nemám čo čítať! 📸")
    else:
        with st.spinner("AI mozog šrotuje... Tvorím legendárny výcuc a chystám pasce do kvízu! ⏳"):
            try:
                genai.configure(api_key=api_key)
                
                # AUTO-DISCOVERY MODELU (Hľadá najlepší dostupný model pre tvoj kľúč)
                najlepsi_model = 'gemini-1.5-flash' # Základná voľba
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            if '1.5-flash' in m.name:
                                najlepsi_model = m.name
                                break
                            elif '1.5-pro' in m.name:
                                najlepsi_model = m.name
                except:
                    pass # Ak kontrola zlyhá, pokračujeme so základom
                    
                model = genai.GenerativeModel(najlepsi_model)
                image = Image.open(uploaded_file)
                
                prompt = f"""
                Si super-inteligentný, ale mimoriadne vtipný a chápavý študijný parťák.
                Tvojou úlohou je prečítať poznámky z obrázka a vytvoriť odpoveď PRESNE v tomto JSON formáte.
                Nevypisuj absolútne žiadny iný text okolo, len čistý JSON.
                
                Pravidlá pre "vycuc":
                - Vysvetli látku ako pre úplného začiatočníka.
                - Používaj vtipné prirovnania z bežného života (hry, jedlo, popkultúra).
                - Používaj emoji. Daj to do krátkych, úderných odstavcov a odrážok.
                
                Pravidlá pre "test":
                - Vygeneruj presne 10 otázok podľa tejto obtiažnosti: {uroven}.
                - Ku každej otázke daj 3 možnosti.
                - Vymysli vtipné, ale náučné vysvetlenie správnej odpovede.
                
                VYŽADOVANÝ JSON FORMÁT:
                {{
                  "vycuc": "Tu bude tvoj úžasný, markdownom formátovaný výcuc s emoji...",
                  "test": [
                    {{
                      "otazka": "Znenie otázky?",
                      "moznosti": ["Odpoveď A", "Odpoveď B", "Odpoveď C"],
                      "spravna_odpoved_index": 0,
                      "vysvetlenie": "Prečo je to tak (vtipne vysvetlené)."
                    }}
                  ]
                }}
                """
                
                response = model.generate_content([prompt, image])
                
                # BEZPEČNÉ PARSOVANIE JSONU (Odolné voči chybám)
                text_odpovede = response.text
                match = re.search(r'\{.*\}', text_odpovede, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    data = json.loads(json_str)
                    st.session_state['data'] = data
                    st.session_state['test_vyhodnoteny'] = False
                    st.session_state['image'] = image
                    st.rerun() # Obnoví stránku pre zobrazenie
                else:
                    st.error("AI sa trochu poplietla a nevrátila dáta v čitateľnom formáte. Skús stlačiť tlačidlo ešte raz.")
                    
            except Exception as e:
                st.error(f"Došlo k chybe pri spojení s AI: {e}")

# Vykreslenie, ak sú dáta pripravené
if 'data' in st.session_state:
    st.divider()
    with st.expander("Pozrieť pôvodnú fotku"):
        st.image(st.session_state['image'], use_column_width=True)
    
    tab_vycuc, tab_kviz = st.tabs(["📖 Nadupaný Výcuc", "🎮 Otestuj sa!"])
    
    with tab_vycuc:
        st.markdown("<div class='vycuc-box'>", unsafe_allow_html=True)
        st.markdown(st.session_state['data']['vycuc'])
        st.markdown("</div>", unsafe_allow_html=True)
        st.success("Keď toto pochopíš, preklikni hore na záložku '🎮 Otestuj sa!'")
        
    with tab_kviz:
        st.markdown("### Aréna pripravená. Poď na to!")
        with st.form("quiz_form"):
            user_answers = []
            for i, q in enumerate(st.session_state['data']['test']):
                st.markdown(f"**{i+1}. {q['otazka']}**")
                ans = st.radio("Vyber si:", q['moznosti'], key=f"q_{i}", index=None)
                user_answers.append(ans)
                st.write("---")
                
            submitted = st.form_submit_button("🏆 Vyhodnotiť moje vedomosti", type="primary", use_container_width=True)
            
            if submitted:
                if None in user_answers:
                    st.warning("Ešte si neodpovedal na všetky otázky! Zisti, čo ti chýba.")
                else:
                    st.session_state['test_vyhodnoteny'] = True
                    st.session_state['user_answers'] = user_answers
                    st.rerun()

# Vyhodnotenie
if st.session_state.get('test_vyhodnoteny'):
    st.markdown("## 📊 Tvoje skóre")
    skore = 0
    otazky = st.session_state['data']['test']
    odpovede = st.session_state['user_answers']
    
    for i, q in enumerate(otazky):
        spravny_text = q['moznosti'][q['spravna_odpoved_index']]
        if odpovede[i] == spravny_text:
            skore += 1
            st.success(f"**{i+1}. Správne!** {q['vysvetlenie']}")
        else:
            st.error(f"**{i+1}. Vedľa!** Tvoja odpoveď: {odpovede[i]} | Správne: {spravny_text}")
            st.info(f"💡 Dôvod: {q['vysvetlenie']}")
            
    percenta = (skore / len(otazky)) * 100
    st.metric(label="Úspešnosť", value=f"{skore}/{len(otazky)} ({percenta}%)")
    
    if percenta == 100:
        st.balloons()
        st.success("SI ABSOLÚTNY BOH! 👑")
    elif percenta >= 80:
        st.balloons()
        st.success("Výborne! Si pripravený na písomku. 🚀")
    elif percenta >= 50:
        st.warning("Celkom fajn, ale ešte by to chcelo prebehnúť si výcuc raz. 📖")
    else:
        st.error("Nevadí! Presne na to sme tu. Prečítaj si výcuc znova, chyby ťa naučia najviac! 💪")
