# Prototip aplikacije za natančno citiranje
# Ta koda prikazuje osnovni koncept, kako bi aplikacija delovala

# Najprej namestimo potrebne knjižnice
# !pip install PyPDF2 nltk transformers

import PyPDF2
import re
import nltk
from nltk.tokenize import sent_tokenize
from google.colab import files
import pandas as pd

# Prenesi potrebne NLTK vire (samo prvič)
nltk.download('punkt')

def naloži_pdf():
    """Funkcija za nalaganje PDF datoteke v Colab"""
    uploaded = files.upload()
    filename = list(uploaded.keys())[0]
    return filename

def preberi_pdf(filename):
    """Prebere PDF datoteko in vrne besedilo ter slovar strani"""
    
    reader = PyPDF2.PdfReader(filename)
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
    
    return celotno_besedilo, besedilo_po_straneh

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

def generiraj_besedilo_s_citati(naslov, citati_s_stranmi, ključne_besede=None):
    """
    Demonstrira, kako bi lahko generirali besedilo s citati.
    V pravi aplikaciji bi tukaj uporabili API za UI model.
    """
    
    # To je samo demonstracija, v pravi aplikaciji bi uporabili UI model
    uvod = f"# {naslov}\n\n"
    uvod += "## Uvod\n\n"
    uvod += "V tem besedilu bomo raziskali pomembne vidike teme na podlagi relevantne literature.\n\n"
    
    jedro = "## Analiza\n\n"
    
    # Uporabimo citate v besedilu
    for i, (citat, stran) in enumerate(citati_s_stranmi):
        if i < len(citati_s_stranmi) - 1:
            jedro += f"Kot navaja literatura: \"{citat}\" (str. {stran}). "
            jedro += "To je pomemben vidik, ki ga je potrebno upoštevati. "
        else:
            jedro += f"Zaključimo lahko z ugotovitvijo: \"{citat}\" (str. {stran}).\n\n"
    
    zaključek = "## Zaključek\n\n"
    zaključek += "Na podlagi pregledane literature lahko zaključimo, da tema predstavlja pomembno področje raziskovanja z več različnimi vidiki."
    
    return uvod + jedro + zaključek

def glavna_funkcija():
    """Glavna funkcija, ki izvaja celoten proces"""
    
    print("Dobrodošli v prototipu aplikacije za natančno citiranje!")
    print("Najprej naloži PDF dokument...")
    
    filename = naloži_pdf()
    
    print(f"Naložena datoteka: {filename}")
    print("Obdelujem PDF dokument...")
    
    celotno_besedilo, besedilo_po_straneh = preberi_pdf(filename)
    
    print(f"Ekstrakcija besedila končana. Skupno število strani: {len(besedilo_po_straneh)}")
    print("Iščem potencialne citate...")
    
    potencialni_citati = najdi_potencialne_citate(celotno_besedilo)
    
    print(f"Najdenih {len(potencialni_citati)} potencialnih citatov.")
    
    # Najdemo strani za vsakega od prvih 5 citatov
    citati_s_stranmi = []
    
    for i, citat in enumerate(potencialni_citati[:5]):  # Omejimo na prvih 5 za demonstracijo
        stran = najdi_stran_citata(citat, besedilo_po_straneh)
        citati_s_stranmi.append((citat, stran))
        
        print(f"\nCitat {i+1}:")
        print(f"Besedilo: \"{citat[:100]}...\"")
        print(f"Stran: {stran}")
    
    # Demonstriramo generiranje besedila s citati
    print("\nDemonstracija generiranja besedila s citati:")
    naslov = "Raziskovalno delo na izbrano temo"
    generirano_besedilo = generiraj_besedilo_s_citati(naslov, citati_s_stranmi)
    
    print("\n" + "="*50 + "\n")
    print(generirano_besedilo)
    print("\n" + "="*50 + "\n")
    
    # Prikažemo rezultate v preglednici
    podatki = []
    for citat, stran in citati_s_stranmi:
        podatki.append({
            "Citat": citat[:100] + "...",
            "Stran": stran
        })
    
    df = pd.DataFrame(podatki)
    print("\nPreglednica citatov:")
    print(df)
    
    return celotno_besedilo, besedilo_po_straneh, citati_s_stranmi

# Poženemo funkcijo, če je datoteka zagnana direktno
if __name__ == "__main__":
    glavna_funkcija()
