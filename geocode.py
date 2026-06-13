"""
geocode.py - Etape 3 du pipeline
Transforme les adresses textuelles en coordonnees GPS (latitude/longitude).

Strategie :
1. On essaie l'API BAN (Base Adresse Nationale, data.gouv.fr) -> tres precise pour la France.
2. Si indisponible, on bascule sur Nominatim (OpenStreetMap).
3. Un cache local (COORDS_CACHE) garantit un resultat reproductible meme hors-ligne
   (utile pour le rendu : les coordonnees restent stables si les API sont injoignables).

Le geocodage ne doit etre lance qu'une seule fois : il produit data/coworkings_final.xlsx.
"""

import os
import time
import requests
import pandas as pd

INPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "coworkings_idf.xlsx")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "coworkings_final.xlsx")

USER_AGENT = "CoworkingProjet/1.0 (projet etudiant)"

# Cache des coordonnees deja resolues (adresse -> [lat, lon]).
# Permet un rendu reproductible meme si les API sont injoignables.
COORDS_CACHE = {
    "54 rue Greneta, 75002 Paris": [
        48.86563,
        2.34936
    ],
    "210 rue Saint-Martin, 75003 Paris": [
        48.86434,
        2.3529
    ],
    "41 Rue Réaumur, 75003 Paris": [
        48.86627,
        2.35185
    ],
    "19 rue Claude Bernard, 75 005 Paris": [
        48.84137,
        2.3496
    ],
    "41 Rue de la Chaussée d’Antin, 75009 Paris": [
        48.8734,
        2.3336
    ],
    "18 Rue du Faubourg du Temple, 75011 Paris": [
        48.8681,
        2.3676
    ],
    "30-34 rue du Chemin Vert 75011, Paris": [
        48.8596,
        2.3764
    ],
    "28 rue du Chemin Vert, 75 011 Paris": [
        48.8598,
        2.3751
    ],
    "22 bis rue des Taillandiers, 75011 Paris": [
        48.8542,
        2.3764
    ],
    "88 rue Saint-Maur, 75011 Paris": [
        48.8643,
        2.3784
    ],
    "30 rue des 3 Bornes, 75011 Paris": [
        48.8668,
        2.3729
    ],
    "61 rue Traversière, 75 012 Paris": [
        48.8466,
        2.3731
    ],
    "51 rue Claude Decaen 75012 Paris": [
        48.8376,
        2.3962
    ],
    "13 rue Vandrezanne, 75 013 Paris": [
        48.8282,
        2.3514
    ],
    "9 rue Guyton de Morveau, 75 013 Paris": [
        48.825,
        2.3614
    ],
    "29 Rue Brézin, 75014 Paris": [
        48.832,
        2.327
    ],
    "40 rue Castagnary, 75015 Paris": [
        48.8326,
        2.3009
    ],
    "10 rue Pergolèse, 75016 paris": [
        48.8733,
        2.2835
    ],
    "47 avenue de Wagram, 75017, PARIS": [
        48.8813,
        2.3004
    ],
    "10 rue des Renaudes, 75017 Paris": [
        48.8818,
        2.2976
    ],
    "111 Rue Cardinet, 75017 Paris": [
        48.886,
        2.3128
    ],
    "3 rue Stephenson, 75 018 Paris": [
        48.8893,
        2.3569
    ],
    "6 rue Arthur Rozier, 75019 Paris": [
        48.879,
        2.3847
    ],
    "29 rue de Meaux, 75019 Paris": [
        48.8818,
        2.3712
    ],
    "15 bis rue Léon Giraud, 75019 Paris": [
        48.8886,
        2.3833
    ],
    "24 Rue de l’Est, 75020 Paris": [
        48.8709,
        2.3923
    ]
}


def geocode_ban(address):
    """Geocodage via l'API Base Adresse Nationale (France)."""
    try:
        r = requests.get(
            "https://api-adresse.data.gouv.fr/search/",
            params={"q": address, "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        r.raise_for_status()
        feats = r.json().get("features", [])
        if feats:
            lon, lat = feats[0]["geometry"]["coordinates"]
            return float(lat), float(lon)
    except Exception as e:
        print(f"  [BAN] echec pour '{address}': {e}")
    return None, None


def geocode_nominatim(address):
    """Geocodage via Nominatim (OpenStreetMap)."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1, "countrycodes": "fr"},
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"  [Nominatim] echec pour '{address}': {e}")
    return None, None


def geocode(address):
    """Resout une adresse en (lat, lon) : API d'abord, puis cache local en secours."""
    if not isinstance(address, str) or not address.strip():
        return None, None
    address = address.strip()

    # 1. API BAN
    lat, lon = geocode_ban(address)
    if lat is not None:
        return lat, lon

    # 2. API Nominatim
    lat, lon = geocode_nominatim(address)
    if lat is not None:
        return lat, lon

    # 3. Cache local (secours hors-ligne)
    if address in COORDS_CACHE:
        return COORDS_CACHE[address]

    return None, None


def run_geocoding():
    if not os.path.exists(INPUT_PATH):
        print(f"Fichier introuvable : {INPUT_PATH}. Lancez d'abord scraping.py.")
        return

    print(f"Lecture de {INPUT_PATH} ...")
    df = pd.read_excel(INPUT_PATH, sheet_name="Détails Parisiens")

    lats, lons = [], []
    print(f"Geocodage de {len(df)} adresses ...")
    for _, row in df.iterrows():
        lat, lon = geocode(row.get("adresse"))
        statut = "OK " if lat is not None else "KO "
        print(f"  {statut} {row.get('adresse')}")
        lats.append(lat)
        lons.append(lon)
        time.sleep(1)  # respect des limites d'usage des API

    df["latitude"] = lats
    df["longitude"] = lons

    ok = df["latitude"].notna().sum()
    print(f"Geocodage termine. Succes : {ok}/{len(df)}")

    df.to_excel(OUTPUT_PATH, index=False)
    print(f"Fichier final ecrit : {OUTPUT_PATH}")


if __name__ == "__main__":
    run_geocoding()
