import requests
from pyquery import PyQuery as pq
import pandas as pd
import time
import os
import re

def get_coworking_list(url):
    print(f"Scraping list from {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        d = pq(response.text)
        
        # On cherche les liens dans la section IDF
        # D'après l'inspection, ils sont sous le titre "Coworking Paris – Île de France :"
        coworkings = []
        
        # On cherche tous les liens qui semblent être des fiches de coworking
        # Ils sont généralement dans des listes <ul> après le titre h3
        links = d('a[href*="/coworking/"]')
        
        for link in links.items():
            href = link.attr('href')
            text = link.text()
            # On filtre pour ne garder que les liens vers les fiches individuelles (pas la page parente)
            if href != url and "/coworking/" in href and len(text) > 5:
                # Vérifier si c'est en IDF (Paris ou codes postaux 77, 78, 91, 92, 93, 94, 95)
                # Le texte contient souvent la ville et le code postal
                coworkings.append({
                    'nom': text,
                    'url': href
                })
        
        df = pd.DataFrame(coworkings).drop_duplicates(subset=['url'])
        print(f"Found {len(df)} coworking spaces.")
        return df
    except Exception as e:
        print(f"Error scraping list: {e}")
        return pd.DataFrame()

def get_details(df_list):
    print("Scraping details for Paris-based coworking spaces...")
    details = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Filtrer uniquement les parisiens (75xxx)
    paris_df = df_list[df_list['nom'].str.contains(r'Paris \(75\d{3}\)', regex=True, na=False)].copy()
    print(f"Total Paris-based to scrape: {len(paris_df)}")
    
    for index, row in paris_df.iterrows():
        url = row['url']
        print(f"Scraping details for: {row['nom']} ({url})")
        try:
            time.sleep(1) # Respectful delay
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            d = pq(response.text)
            
            # Extraction des données
            title = d('h1').text()
            img_main = d('.entry-content img').eq(0).attr('src') or d('img.wp-post-image').eq(0).attr('src') or ""
            description = d('.entry-content p').eq(0).text() # Simplifié pour l'exemple
            
            # Infos de contact - souvent dans des listes ou des paragraphes spécifiques
            content_text = d('.entry-content').text()
            
            # Le bloc de contact se trouve generalement dans un <ul> situe
            # juste apres un titre H2 "Contacter ...". On cible ce <ul> en priorite.
            contact_lis = []
            for h2 in d('h2').items():
                if 'contacter' in (h2.text() or '').lower():
                    ul = h2.nextAll('ul').eq(0)
                    if ul:
                        contact_lis = list(ul('li').items())
                    break
            if not contact_lis:
                contact_lis = list(d('.entry-content li').items())

            def extract_info(label):
                # 1) Recherche dans les <li> du bloc contact ("Label : valeur")
                for li in contact_lis:
                    li_text = li.text() or ""
                    if label.lower() in li_text.lower() and ':' in li_text:
                        key, _, val = li_text.partition(':')
                        if label.lower() in key.lower():
                            return val.strip()
                # 2) Repli : regex sur le texte complet
                full_text = d('.entry-content').text()
                match = re.search(rf"{label}\s*[:\-]\s*(.*)", full_text, re.IGNORECASE)
                if match:
                    return match.group(1).strip().split('\n')[0].strip()
                return ""

            adresse = extract_info("Adresse")
            telephone = extract_info("Téléphone")
            acces = extract_info("Accès")
            
            # Find the official website link
            site_officiel = ""
            for a in d('.entry-content a').items():
                href = a.attr('href')
                if href and href.startswith('http') and "leportagesalarial.com" not in href:
                    site_officiel = href
                    break
            
            # Réseaux sociaux
            twitter = d('.entry-content a[href*="twitter.com"]').attr('href') or ""
            facebook = d('.entry-content a[href*="facebook.com"]').attr('href') or ""
            linkedin = d('.entry-content a[href*="linkedin.com"]').attr('href') or ""
            
            # Meta tags
            meta_title = d('title').text()
            meta_desc = d('meta[name="description"]').attr('content') or ""
            
            # Meta title length check
            meta_title_short = len(meta_title) < 150
            
            # Date de publication (soubliée dans le HTML, souvent dans une balise time ou meta)
            pub_date = d('meta[property="article:published_time"]').attr('content') or d('time.entry-date').attr('datetime') or ""

            details.append({
                'nom': row['nom'],
                'titre_h1': title,
                'image_principale': img_main,
                'description': description,
                'adresse': adresse,
                'telephone': telephone,
                'acces': acces,
                'site_web': site_officiel,
                'twitter': twitter,
                'facebook': facebook,
                'linkedin': linkedin,
                'meta_title': meta_title,
                'meta_description': meta_desc,
                'meta_title_short': meta_title_short,
                'date_publication': pub_date,
                'url_source': url
            })
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            
    return pd.DataFrame(details)

if __name__ == "__main__":
    source_url = "https://www.leportagesalarial.com/coworking/"
    
    # Etape 1
    df_idf = get_coworking_list(source_url)
    
    # Etape 2
    df_paris_details = get_details(df_idf)
    
    # Export Excel — chemin calcule par rapport a l'emplacement du script,
    # peu importe le dossier d'ou l'on lance la commande.
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)  # cree le dossier data/ s'il n'existe pas
    output_path = os.path.join(data_dir, "coworkings_idf.xlsx")
    with pd.ExcelWriter(output_path) as writer:
        df_idf.to_excel(writer, sheet_name='Liste IDF', index=False)
        df_paris_details.to_excel(writer, sheet_name='Détails Parisiens', index=False)
    
    print(f"Scraping completed. File saved at {output_path}")
