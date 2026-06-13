"""
app.py - Application Streamlit "Coworking Paris & IDF"
======================================================
Application d'aide a la decision pour trouver un espace de coworking a Paris.

Fonctionnalites principales :
- Carte interactive Folium avec regroupement de marqueurs (MarkerCluster)
- Geolocalisation de l'utilisateur (bouton navigateur OU saisie manuelle)
- Calcul de distance et filtre "Autour de moi"
- Tri avance (pertinence, distance, alphabetique, arrondissement)
- Fiches detaillees modernes (style annuaire pro / Google Maps)
- Liens utiles : site officiel, Google Maps, itineraire
- Gestion intelligente des recherches sans resultat (propose des alternatives)
- Systeme de filtres pilote par configuration : un filtre n'apparait que si la
  colonne correspondante existe dans les donnees -> architecture prete a accueillir
  de nouvelles donnees (wifi, parking, horaires...) sans modifier le code.

Lancement : python -m streamlit run app.py
"""

import os
import re
import math
import urllib.parse

import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# Composant de geolocalisation navigateur (optionnel : l'app fonctionne sans).
try:
    from streamlit_geolocation import streamlit_geolocation
    GEOLOC_AVAILABLE = True
except Exception:
    GEOLOC_AVAILABLE = False


# =============================================================================
# CONFIGURATION DE LA PAGE
# =============================================================================
st.set_page_config(
    page_title="Coworking Paris & IDF",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Centre de Paris (utilise pour centrer la carte et comme repli de geolocalisation).
PARIS_CENTER = (48.8566, 2.3522)


# =============================================================================
# STYLE (CSS) - identite visuelle "annuaire moderne"
# =============================================================================
st.markdown(
    """
    <style>
    .cowork-card {
        background: #ffffff;
        border: 1px solid #e6e8eb;
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(16,24,40,0.06);
        transition: box-shadow .15s ease, transform .15s ease;
    }
    .cowork-card:hover {
        box-shadow: 0 6px 18px rgba(16,24,40,0.12);
        transform: translateY(-1px);
    }
    .cowork-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1a3c5e;
        margin: 0 0 2px 0;
    }
    .cowork-arr {
        display: inline-block;
        background: #eaf2fb;
        color: #2a6496;
        font-size: .72rem;
        font-weight: 600;
        padding: 2px 9px;
        border-radius: 999px;
        margin-left: 6px;
        vertical-align: middle;
    }
    .cowork-line { color: #475467; font-size: .9rem; margin: 4px 0; }
    .cowork-dist {
        display: inline-block;
        background: #e7f6ec;
        color: #1e7e44;
        font-size: .78rem;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 999px;
    }
    .badge-muted {
        display: inline-block;
        background: #f2f4f7;
        color: #98a2b3;
        font-size: .72rem;
        padding: 2px 9px;
        border-radius: 999px;
        margin: 2px 4px 2px 0;
    }
    .link-btn {
        display: inline-block;
        text-decoration: none;
        font-size: .85rem;
        font-weight: 600;
        padding: 7px 14px;
        border-radius: 9px;
        margin: 8px 8px 0 0;
    }
    .link-primary { background: #2a6496; color: #fff !important; }
    .link-secondary { background: #f2f4f7; color: #344054 !important; border: 1px solid #e6e8eb; }
    .section-hint { color: #667085; font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# CHARGEMENT DES DONNEES
# =============================================================================
@st.cache_data
def load_data():
    """Charge le fichier geocode. Cherche le chemin que l'on soit a la racine
    du projet ou ailleurs (robustesse au lancement)."""
    candidates = [
        "data/coworkings_final.xlsx",
        os.path.join(os.path.dirname(__file__), "data", "coworkings_final.xlsx"),
        "projet_coworking/data/coworkings_final.xlsx",
    ]
    for path in candidates:
        if os.path.exists(path):
            return pd.read_excel(path)
    return pd.DataFrame()


def get_arrondissement(nom):
    """Extrait le code postal complet (ex '75011') depuis '... (75011)'."""
    m = re.search(r"(75\d{3})", str(nom))
    return m.group(1) if m else "75???"


def haversine_km(lat1, lon1, lat2, lon2):
    """Distance en km entre deux points GPS (formule de haversine)."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def has_value(v):
    """True si la cellule contient une vraie valeur exploitable."""
    if v is None:
        return False
    s = str(v).strip().lower()
    return s not in ("", "nan", "none", "n/a")


# -----------------------------------------------------------------------------
# Configuration des FILTRES "presence d'attribut".
# Chaque entree : (cle_colonne, libelle). Le filtre n'est propose QUE si la
# colonne existe dans le dataset -> architecture extensible. Pour ajouter
# "wifi" ou "parking" plus tard, il suffit d'ajouter la colonne dans l'Excel
# et une ligne ici. Rien d'autre a coder.
# -----------------------------------------------------------------------------
OPTIONAL_FILTERS = [
    ("site_web", "A un site web"),
    ("telephone", "A un téléphone"),
    ("acces", "Accessible en transport"),
    # Prets a l'emploi si les colonnes apparaissent un jour :
    ("wifi", "Wifi"),
    ("parking", "Parking"),
    ("salle_reunion", "Salle de réunion"),
    ("domiciliation", "Domiciliation"),
    ("gratuit", "Gratuit"),
]

# Champs de fiche detaillee : (cle_colonne, libelle, icone).
# Affiches meme si absents -> "non renseigné" (transparence demandee).
DETAIL_FIELDS = [
    ("adresse", "Adresse", "📍"),
    ("telephone", "Téléphone", "📞"),
    ("acces", "Transports à proximité", "🚇"),
    ("horaires", "Horaires", "🕒"),
    ("services", "Services disponibles", "🛎️"),
]


# =============================================================================
# EN-TETE
# =============================================================================
st.title("🧭 Coworking Paris & IDF")
st.markdown(
    "<p class='section-hint'>Trouvez l'espace de coworking parisien qui vous "
    "correspond. Filtrez, triez, localisez-vous, et obtenez l'itinéraire en un clic.</p>",
    unsafe_allow_html=True,
)

df = load_data()

if df.empty:
    st.error(
        "Données introuvables. Vérifiez que le fichier `data/coworkings_final.xlsx` "
        "est présent, puis relancez l'application. Si besoin, exécutez d'abord "
        "`python scripts/scraping.py` puis `python scripts/geocode.py`."
    )
    st.stop()

# Pre-traitements communs
df = df.copy()
df["arrondissement"] = df["nom"].apply(get_arrondissement)
df["nom_court"] = df["nom"].apply(lambda n: str(n).split(":")[0].strip())


# =============================================================================
# BARRE LATERALE : localisation + filtres + tri
# =============================================================================
st.sidebar.header("📍 Votre position")

user_lat, user_lon = None, None

# 1) Geolocalisation navigateur (si le composant est dispo)
if GEOLOC_AVAILABLE:
    st.sidebar.caption("Cliquez pour vous localiser (le navigateur demandera l'autorisation).")
    loc = streamlit_geolocation()
    if loc and loc.get("latitude") and loc.get("longitude"):
        user_lat, user_lon = loc["latitude"], loc["longitude"]
        st.sidebar.success("Position détectée ✔")
else:
    st.sidebar.info("Géolocalisation auto indisponible — utilisez la saisie manuelle ci-dessous.")

# 2) Saisie manuelle (toujours disponible, en secours)
with st.sidebar.expander("Ou saisir un point de départ", expanded=(user_lat is None)):
    manual = st.text_input(
        "Coordonnées (lat, lon)",
        placeholder="ex : 48.8566, 2.3522",
        help="Saisissez des coordonnées GPS séparées par une virgule.",
    )
    if manual.strip():
        try:
            parts = [float(x) for x in manual.replace(" ", "").split(",")]
            if len(parts) == 2:
                user_lat, user_lon = parts[0], parts[1]
                st.success("Point de départ enregistré ✔")
        except ValueError:
            st.warning("Format attendu : deux nombres séparés par une virgule, ex « 48.8566, 2.3522 ».")

has_user_pos = user_lat is not None and user_lon is not None

# Calcul des distances si position connue
if has_user_pos:
    df["distance_km"] = df.apply(
        lambda r: haversine_km(user_lat, user_lon, r["latitude"], r["longitude"]), axis=1
    )
else:
    df["distance_km"] = None

st.sidebar.divider()
st.sidebar.header("🔎 Filtres")

# Recherche par nom
search_name = st.sidebar.text_input("Rechercher par nom", "")

# Filtre arrondissement
arr_list = sorted(a for a in df["arrondissement"].unique() if a != "75???")
selected_arr = st.sidebar.multiselect(
    "Arrondissement", options=arr_list, default=arr_list,
    help="Quartiers parisiens (75xxx).",
)

# Filtre distance (seulement si position connue)
max_dist = None
around_me = False
if has_user_pos:
    around_me = st.sidebar.checkbox("Autour de moi", value=False)
    max_dist = st.sidebar.slider("Distance maximale (km)", 0.5, 15.0, 5.0, 0.5)

# Filtres optionnels "presence d'attribut" — uniquement ceux dont la colonne existe
st.sidebar.caption("Critères")
active_optional = []
for col, label in OPTIONAL_FILTERS:
    if col in df.columns:
        if st.sidebar.checkbox(label, value=False, key=f"opt_{col}"):
            active_optional.append(col)

st.sidebar.divider()

# Tri
sort_options = ["Pertinence", "Ordre alphabétique", "Arrondissement"]
if has_user_pos:
    sort_options.insert(1, "Distance")
sort_choice = st.sidebar.selectbox("Trier par", sort_options)


# =============================================================================
# APPLICATION DES FILTRES
# =============================================================================
filtered = df.copy()

if search_name.strip():
    filtered = filtered[filtered["nom"].str.contains(search_name, case=False, na=False)]

if selected_arr:
    filtered = filtered[filtered["arrondissement"].isin(selected_arr)]

for col in active_optional:
    filtered = filtered[filtered[col].apply(has_value)]

if has_user_pos and around_me and max_dist is not None:
    filtered = filtered[filtered["distance_km"] <= max_dist]

# Tri
if sort_choice == "Ordre alphabétique":
    filtered = filtered.sort_values("nom_court", key=lambda s: s.str.lower())
elif sort_choice == "Arrondissement":
    filtered = filtered.sort_values("arrondissement")
elif sort_choice == "Distance" and has_user_pos:
    filtered = filtered.sort_values("distance_km")
# "Pertinence" = ordre d'origine (laisse tel quel)


# =============================================================================
# GESTION DES RECHERCHES SANS RESULTAT (propose des alternatives)
# =============================================================================
display_df = filtered

if filtered.empty:
    st.warning(
        "Aucun coworking ne correspond exactement à votre recherche. "
        "Voici les alternatives les plus proches."
    )
    # Alternatives : on relache les filtres mais on garde la logique de proximite.
    alt = df.copy()
    if search_name.strip():
        loose = alt[alt["nom_court"].str.contains(search_name.strip()[:3], case=False, na=False)]
        alt = loose if not loose.empty else alt
    if has_user_pos:
        alt = alt.sort_values("distance_km")
    display_df = alt.head(5)


# =============================================================================
# DISPOSITION PRINCIPALE : indicateurs + carte + resultats
# =============================================================================
count = len(display_df)
c1, c2, c3 = st.columns(3)
c1.metric("Coworkings affichés", count)
c2.metric("Arrondissements", display_df["arrondissement"].nunique())
if has_user_pos and count and display_df["distance_km"].notna().any():
    c3.metric("Le plus proche", f"{display_df['distance_km'].min():.1f} km")

st.divider()

col_map, col_list = st.columns([3, 2], gap="large")

# ---- Carte ----
with col_map:
    st.subheader("Carte interactive")

    if has_user_pos:
        center = (user_lat, user_lon)
        zoom = 13
    elif count:
        center = (display_df["latitude"].mean(), display_df["longitude"].mean())
        zoom = 12
    else:
        center, zoom = PARIS_CENTER, 12

    m = folium.Map(location=center, zoom_start=zoom, tiles="cartodbpositron")

    # Marqueur position utilisateur + rayon "autour de moi"
    if has_user_pos:
        folium.Marker(
            [user_lat, user_lon],
            tooltip="Vous êtes ici",
            icon=folium.Icon(color="red", icon="user", prefix="fa"),
        ).add_to(m)
        if around_me and max_dist:
            folium.Circle(
                [user_lat, user_lon], radius=max_dist * 1000,
                color="#2a6496", fill=True, fill_opacity=0.06, weight=1,
            ).add_to(m)

    # Regroupement de marqueurs
    cluster = MarkerCluster().add_to(m)
    for _, row in display_df.iterrows():
        if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
            maps_q = urllib.parse.quote(f"{row['nom_court']} {row.get('adresse','')}")
            gmaps = f"https://www.google.com/maps/search/?api=1&query={maps_q}"
            itineraire = f"https://www.google.com/maps/dir/?api=1&destination={maps_q}"
            dist_txt = (
                f"<br>📏 {row['distance_km']:.1f} km"
                if has_user_pos and pd.notna(row["distance_km"]) else ""
            )
            site = row.get("site_web", "")
            site_link = (
                f"<br><a href='{site}' target='_blank'>🌐 Site officiel</a>"
                if has_value(site) else ""
            )
            popup_html = f"""
            <div style='width:230px;font-family:sans-serif'>
                <b style='color:#1a3c5e'>{row['nom_court']}</b>
                <span style='color:#2a6496'> · {row['arrondissement']}</span>
                <p style='margin:6px 0;color:#475467'>{row.get('adresse','')}</p>
                {dist_txt}{site_link}
                <br><a href='{itineraire}' target='_blank'>🧭 Voir l'itinéraire</a>
                <br><a href='{gmaps}' target='_blank'>🗺️ Ouvrir dans Google Maps</a>
            </div>
            """
            folium.Marker(
                [row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=row["nom_court"],
                icon=folium.Icon(color="blue", icon="briefcase", prefix="fa"),
            ).add_to(cluster)

    st_folium(m, use_container_width=True, height=560, returned_objects=[])

# ---- Liste de fiches detaillees ----
with col_list:
    st.subheader("Résultats")
    if count == 0:
        st.info("Aucun résultat. Essayez d'élargir vos filtres dans la barre latérale.")
    for _, row in display_df.iterrows():
        nom = row["nom_court"]
        arr = row['arrondissement']
        maps_q = urllib.parse.quote(f"{nom} {row.get('adresse','')}")
        gmaps = f"https://www.google.com/maps/search/?api=1&query={maps_q}"
        itineraire = f"https://www.google.com/maps/dir/?api=1&destination={maps_q}"

        dist_badge = ""
        if has_user_pos and pd.notna(row.get("distance_km")):
            dist_badge = f"<span class='cowork-dist'>📏 {row['distance_km']:.1f} km</span>"

        # Lignes de detail (valeur reelle ou "non renseigné")
        detail_lines = ""
        for col, label, icon in DETAIL_FIELDS:
            val = row.get(col, None)
            if has_value(val):
                detail_lines += f"<div class='cowork-line'>{icon} {val}</div>"
            else:
                detail_lines += (
                    f"<div class='cowork-line'>{icon} {label} : "
                    f"<span class='badge-muted'>non renseigné</span></div>"
                )

        site = row.get("site_web", "")
        site_btn = (
            f"<a class='link-btn link-secondary' href='{site}' target='_blank'>🌐 Site web</a>"
            if has_value(site) else ""
        )

        card_html = f"""
        <div class='cowork-card'>
            <div class='cowork-title'>{nom}<span class='cowork-arr'>{arr}</span></div>
            <div style='margin:6px 0'>{dist_badge}</div>
            {detail_lines}
            <div>
                <a class='link-btn link-primary' href='{itineraire}' target='_blank'>🧭 Itinéraire</a>
                {site_btn}
                <a class='link-btn link-secondary' href='{gmaps}' target='_blank'>🗺️ Google Maps</a>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        img = row.get("image_principale", "")
        if has_value(img):
            try:
                st.image(img, use_container_width=True)
            except Exception:
                pass


# =============================================================================
# PIED DE PAGE
# =============================================================================
st.divider()
st.caption(
    "Données extraites de leportagesalarial.com · Géocodage Base Adresse Nationale / "
    "OpenStreetMap · Projet Coworking IDF. Les champs « non renseigné » seront remplis "
    "automatiquement dès que les colonnes correspondantes seront ajoutées au jeu de données."
)
