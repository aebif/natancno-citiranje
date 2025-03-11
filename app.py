# app.py - Preprost Streamlit uporabniški vmesnik
# Za zagon: pip install streamlit, nato streamlit run app.py

import streamlit as st
import PyPDF2
import nltk
from nltk.tokenize import sent_tokenize
import pandas as pd
import tempfile
import os

# Prenesi potrebne NLTK vire (samo enkrat)
nltk.download('punkt', quiet=True)

st.set_page_config(page_title="Aplikacija za natančno citiranje", layout="wide")
st.title("Aplikacija za natančno citiranje")

# Sidebar za nastavitve
st.sidebar.header("Nastavitve")
min_dolžina_citata = st.sidebar.slider("Minimalna dolžina citata", 20, 100, 50)
max_dolžina_citata = st.sidebar.slider("Maksimalna dolžina citata", 100, 500, 300)
število_citatov = st.sidebar.slider("Število uporabljenih citatov", 1, 10, 5)

# Glavna funkcija za obdelavo PDF datotek
def obdelaj_pdf(uploaded_file, min_dolžina=50, max_dolžina=300):
    # Shranimo naloženo datoteko v začasno datoteko
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    # Preberemo PDF
    reader = PyPDF2.PdfReader(tmp_path)
    število_strani = len(reader.pages)
    
    celotno_besedilo = ""
    besedilo_po_straneh = {}
    
    for št_strani in range(število_strani):
        stran = reader.pages[št_strani]
        besedilo_strani = stran.extract_text()
        
        # Shranimo besedilo te strani
        besedilo_po_straneh[št_strani + 1] = besedilo_strani
        
        # Dodamo besedilo k celotnem besedilu
        celotno_besedilo += besedilo_strani + " "
    
    # Počistimo začasno datoteko
    os.unlink(tmp_path)
    
    return celotno_besedilo, besedilo_po_straneh, število_strani

def najdi_potencialne_citate(besedilo, min_dolžina=50, max_dolžina=300):
    """Identificira potencialne citate iz besedila"""
    
    # Razdelimo besedilo na stavke
    stavki = sent_tokenize(besedilo)
    
    potencialni_citati = []
    trenutni_citat = ""
    
    for stavek in stavki:
        stavek = stavek.strip()
        
        # Preskočimo prazne stavke
        if not stavek:
            continue
        
        # Če je trenutni citat + novi stavek še vedno dovolj kratek
        if len(trenutni_citat + " " + stavek) <= max_dolžina:
            if trenutni_citat:
                trenutni_citat += " " + stavek
            else:
                trenutni_citat = stavek
        else:
            # Shranimo trenutni citat, če je dovolj dolg
            if len(trenutni_citat) >= min_dolžina:
                potencialni_citati.append(trenutni_citat)
            
            # Začnemo nov citat
            trenutni_citat = stavek
    
    # Dodamo zadnji citat, če obstaja in je dovolj dolg
    if trenutni_citat and len(trenutni_citat) >= min_dolžina:
        potencialni_citati.append(trenutni_citat)
    
    return potencialni_citati

def najdi_stran_citata(citat, besedilo_po_straneh):
    """Najde stran, na kateri se nahaja citat"""
    
    for številka_strani, besedilo_strani in besedilo_po_straneh.items():
        if citat in besedilo_strani:
            return številka_strani
    
    # Če ne najdemo natančnega ujemanja, poskusimo s prvimi besedami citata
    prve_besede = " ".join(citat.split()[:10])  # Prvih 10 besed
    
    for številka_strani, besedilo_strani in besedilo_po_straneh.items():
        if prve_besede in besedilo_strani:
            return številka_strani
    
    return None  # Če ne najdemo citata

# Glavna aplikacija
st.subheader("Korak 1: Naloži PDF dokument")

uploaded_file = st.file_uploader("Izberi PDF datoteko", type="pdf")

if uploaded_file is not None:
    # Prikažemo informacije o datoteki
    file_details = {"Ime datoteke": uploaded_file.name, "Velikost": f"{uploaded_file.size} bajtov"}
    st.write(file_details)
    
    with st.spinner("Obdelujem PDF..."):
        celotno_besedilo, besedilo_po_straneh, število_strani = obdelaj_pdf(
            uploaded_file, min_dolžina_citata, max_dolžina_citata
        )
    
    st.success(f"PDF uspešno obdelan. Število strani: {število_strani}")
    
    st.subheader("Korak 2: Išči potencialne citate")
    
    if st.button("Najdi citate"):
        with st.spinner("Iščem citate..."):
            potencialni_citati = najdi_potencialne_citate(
                celotno_besedilo, min_dolžina_citata, max_dolžina_citata
            )
        
        st.success(f"Najdenih {len(potencialni_citati)} potencialnih citatov.")
        
        # Prikažemo izbrane citate
        st.subheader("Korak 3: Preglej in izberi citate")
        
        # Najdemo strani za vsakega od prvih N citatov
        citati_s_stranmi = []
        
        for i, citat in enumerate(potencialni_citati[:20]):  # Prikažemo prvih 20
            stran = najdi_stran_citata(citat, besedilo_po_straneh)
            citati_s_stranmi.append({
                "ID": i+1,
                "Citat": citat,
                "Stran": stran,
                "Izbran": i < število_citatov  # Prvih N citatov je izbranih privzeto
            })
        
        # Ustvarimo DataFrame za prikaz
        df = pd.DataFrame(citati_s_stranmi)
        
        # Prikažemo izbrane citate v preglednici
        st.dataframe(
            df[["ID", "Citat", "Stran", "Izbran"]],
            column_config={
                "ID": st.column_config.NumberColumn("ID"),
                "Citat": st.column_config.TextColumn("Citat"),
                "Stran": st.column_config.NumberColumn("Stran"),
                "Izbran": st.column_config.CheckboxColumn("Izberi")
            },
            hide_index=True
        )
        
        # Korak 4: Generiranje besedila
        st.subheader("Korak 4: Generiraj besedilo")
        
        # Vnosna polja za parametre besedila
        naslov = st.text_input("Naslov besedila", "Raziskovalno delo na izbrano temo")
        ključne_besede = st.text_input("Ključne besede (ločene z vejico)", "znanost, raziskava, analiza")
        
        if st.button("Generiraj besedilo"):
            st.info("V pravi aplikaciji bi tukaj uporabili API za UI model.")
            
            # Prikažemo demonstracijsko besedilo
            st.subheader("Generirano besedilo")
            
            izbrani_citati = [
                (row["Citat"], row["Stran"]) 
                for _, row in df.iterrows() 
                if row["Izbran"] and row["Stran"] is not None
            ][:število_citatov]
            
            # Demonstracijsko besedilo
            uvod = f"# {naslov}\n\n"
            uvod += "## Uvod\n\n"
            uvod += "V tem besedilu bomo raziskali pomembne vidike teme na podlagi relevantne literature.\n\n"
            
            jedro = "## Analiza\n\n"
            
            # Uporabimo citate v besedilu
            for i, (citat, stran) in enumerate(izbrani_citati):
                if i < len(izbrani_citati) - 1:
                    jedro += f"Kot navaja literatura: \"{citat[:100]}...\" (str. {stran}). "
                    jedro += "To je pomemben vidik, ki ga je potrebno upoštevati.\n\n"
                else:
                    jedro += f"Zaključimo lahko z ugotovitvijo: \"{citat[:100]}...\" (str. {stran}).\n\n"
            
            zaključek = "## Zaključek\n\n"
            zaključek += "Na podlagi pregledane literature lahko zaključimo, da tema predstavlja pomembno področje raziskovanja z več različnimi vidiki."
            
            generirano_besedilo = uvod + jedro + zaključek
            st.markdown(generirano_besedilo)
            
            # Gumb za prenos
            st.download_button(
                label="Prenesi besedilo",
                data=generirano_besedilo,
                file_name=f"{naslov.lower().replace(' ', '_')}.md",
                mime="text/markdown"
            )
else:
    st.info("Prosimo, naloži PDF dokument za začetek.")

# Dodatne informacije
st.sidebar.markdown("---")
st.sidebar.subheader("O aplikaciji")
st.sidebar.info(
    """
    Ta aplikacija omogoča natančno citiranje iz PDF dokumentov za ustvarjanje 
    akademskih besedil s pomočjo umetne inteligence.
    
    **Funkcionalnosti:**
    - Ekstrakcija besedila iz PDF
    - Identifikacija potencialnih citatov
    - Lociranje citatov na straneh
    - Generiranje besedila s točnimi citati
    """
)
