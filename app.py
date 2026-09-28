import streamlit as st
import google.generativeai as genai
from PIL import Image

# Nastavenie stránky
st.set_page_config(page_title="AI Výcuc a Test", layout="wide")

st.title("📚 Z poznámok do hlavy: Výcuc a Test")

# Bočný panel pre API kľúč
st.sidebar.header("Nastavenia")
api_key = st.sidebar.text_input("Vlož svoj Google Gemini API kľúč:", type="password")
st.sidebar.markdown("[Kde získam API kľúč zadarmo?](https://aistudio.google.com/app/apikey)")

# Nahrávanie fotky
uploaded_file = st.file_uploader("Nahraj fotku svojich poznámok (JPG, PNG)", type=["jpg", "png", "jpeg"])

# Výber obtiažnosti
uroven = st.radio(
    "Vyber si úroveň testu:",
    ("1. Úroveň: Ešte som si to nepozrel (80% ľahké, 20% stredné)", 
     "2. Úroveň: Niečo už viem (30% ľahké, 60% stredné, 10% ťažké)", 
     "3. Úroveň: Som pripravený (10% ľahké, 10% stredné, 80% ťažké)")
)

if st.button("Vytvoriť výcuc a test"):
    if not api_key:
        st.error("Najskôr vlož svoj API kľúč do bočného panelu vľavo.")
    elif not uploaded_file:
        st.error("Prosím, nahraj fotku poznámok.")
    else:
        try:
            # Prepojenie s AI
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Načítanie fotky
            image = Image.open(uploaded_file)
            st.image(image, caption="Tvoje nahraté poznámky", use_column_width=True)
            
            st.info("AI práve číta tvoje poznámky a tvorí výcuc. Bude to trvať pár sekúnd...")
            
            # Nastavenie požiadavky na výcuc
            zaklad = "Prečítaj si text na tomto obrázku. Vytvor kompletný, ale mimoriadne jednoduchý výcuc. Vysvetli to tak, aby to pochopil aj úplný začiatočník, použi prirovnania z bežného života a rozdeľ text do logických odsekov s odrážkami."
            
            # Pridanie testu podľa úrovne
            if "1. Úroveň" in uroven:
                test = "Následne pod výcuc vytvor test s 10 otázkami. Žiak si to ešte nepozrel, chce zistiť, čo intuitívne vie. Daj 80% veľmi ľahkých a 20% stredných otázok. Ku každej daj možnosti A, B, C. Správne odpovede napíš na úplný koniec."
            elif "2. Úroveň" in uroven:
                test = "Následne pod výcuc vytvor test s 10 otázkami. Žiak už látku videl. Daj 30% ľahkých, 60% stredných a 10% ťažkých otázok. Ku každej daj možnosti A, B, C. Správne odpovede napíš na úplný koniec."
            else:
                test = "Následne pod výcuc vytvor test s 10 otázkami. Žiak látku ovláda, otestuj detaily. Daj 10% ľahkých, 10% stredných a 80% ťažkých otázok (chytáky). Ku každej daj možnosti A, B, C. Správne odpovede napíš na úplný koniec."
            
            finalny_prompt = f"{zaklad}\n\n{test}"
            
            # Generovanie výsledku
            odpoved = model.generate_content([finalny_prompt, image])
            
            st.success("Hotovo! Tu je tvoj materiál:")
            st.markdown(odpoved.text)
            
        except Exception as e:
            st.error(f"Niečo sa pokazilo: {e}")
