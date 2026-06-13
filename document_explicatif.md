# Rapport de Projet : Annuaire des Coworkings d'Île-de-France

## 1. Présentation de l'application
L'application « Coworking Paris & IDF » est une plateforme interactive d'aide à la décision conçue pour aider les entrepreneurs et freelances à trouver un espace de travail adapté à leurs besoins. Au-delà d'un simple annuaire, elle reproduit l'expérience d'un service de cartographie moderne : l'utilisateur peut se localiser, filtrer, trier et obtenir un itinéraire en un clic vers les 26 espaces de coworking parisiens recensés.

## 2. Architecture et Pipeline de données
Le projet repose sur un pipeline de données en trois étapes clés :

*   **Scraping (scripts/scraping.py) :** extraction des données depuis l'annuaire du site *leportagesalarial.com* à l'aide de `pyquery` et `requests` (noms, URLs, titres, images, descriptions, adresses, contacts, balises meta).
*   **Géocodage (scripts/geocode.py) :** conversion des adresses en coordonnées GPS via l'API **Base Adresse Nationale** (data.gouv.fr) avec repli sur Nominatim (OpenStreetMap). Un cache local garantit un résultat reproductible même hors-ligne.
*   **Visualisation (app.py) :** interface utilisateur construite avec `Streamlit` et `Folium`.

## 3. Choix Techniques
*   **PyQuery :** syntaxe proche de jQuery, facilitant l'extraction ciblée dans le DOM.
*   **Base Adresse Nationale / Nominatim :** géocodage open-source, gratuit et précis sur le territoire français.
*   **Folium + MarkerCluster :** cartes Leaflet.js robustes, avec regroupement automatique des marqueurs.
*   **Streamlit :** déploiement rapide d'une interface web interactive.
*   **streamlit-geolocation :** récupération de la position réelle de l'utilisateur via le navigateur.

## 4. Expérience utilisateur (UX)
L'application est pensée du point de vue d'un utilisateur non technique cherchant un coworking :

*   **Recherche sans résultat gérée intelligemment :** au lieu d'un simple message d'erreur, l'application affiche un message explicatif et propose automatiquement les alternatives les plus proches (« Aucun coworking ne correspond exactement à votre recherche. Voici les alternatives les plus proches. »).
*   **Parcours guidé :** indicateurs clés en haut de page (nombre de résultats, arrondissements couverts, distance du plus proche).
*   **Actions en un clic :** itinéraire, site officiel et Google Maps accessibles depuis la carte et depuis chaque fiche.

## 5. Géolocalisation
*   Récupération de la position de l'utilisateur via le navigateur (avec autorisation), **ou** saisie manuelle d'un point de départ en secours.
*   Calcul de la distance (formule de haversine) entre l'utilisateur et chaque coworking, affichée en kilomètres.
*   Filtre « Autour de moi » avec distance maximale réglable et visualisation du rayon sur la carte.

## 6. Interface (UI)
*   Mise en page claire en deux colonnes : carte à gauche, fiches de résultats à droite.
*   Cartes de résultats modernes (coins arrondis, ombre portée, effet au survol), badges colorés (arrondissement, distance), boutons d'action hiérarchisés.
*   Sidebar organisée par sections : position, filtres, tri.
*   Icônes cohérentes et fond de carte épuré (CartoDB Positron) pour la lisibilité.

## 7. Filtres et tri avancés
*   **Filtres :** recherche par nom, arrondissement, distance maximale, « Autour de moi », et critères de présence (site web, téléphone, transport).
*   **Architecture extensible :** les filtres de critères sont pilotés par une configuration ; un nouveau filtre (wifi, parking, salle de réunion…) s'active automatiquement dès que la colonne correspondante est ajoutée au jeu de données, sans modifier le code.
*   **Tri :** pertinence, distance, ordre alphabétique, arrondissement.

## 8. Accessibilité
*   Contrastes de couleurs élevés (texte foncé sur fond clair) pour la lisibilité.
*   Tailles de texte et hiérarchie visuelle explicites.
*   Messages d'interface rédigés en langage clair, orientés action.
*   Données manquantes affichées explicitement comme « non renseigné » plutôt que masquées, pour ne pas induire l'utilisateur en erreur.

## 9. Objectifs Atteints
*   **Visualisation :** carte interactive avec 26 marqueurs géolocalisés, regroupés, et popups détaillés.
*   **Interactivité :** filtres en temps réel, tri multi-critères, géolocalisation, calcul de distance.
*   **Accessibilité :** interface claire, lisible et utilisable sans compétence technique.
*   **Aide à la décision :** l'utilisateur est guidé jusqu'à l'itinéraire, y compris quand sa recherche ne donne aucun résultat exact.

## 10. Améliorations apportées (par rapport à la première version)
*   Passage d'un annuaire statique à une application d'aide à la décision.
*   Ajout de la géolocalisation (navigateur + saisie manuelle) et du calcul de distance.
*   Ajout du tri avancé et des filtres de critères extensibles.
*   Refonte visuelle complète (cartes, badges, boutons, fond de carte).
*   Regroupement de marqueurs et zoom intelligent sur la carte.
*   Liens itinéraire / Google Maps / site officiel dans la popup et les fiches.
*   Gestion des recherches sans résultat avec alternatives.

## 11. Déploiement
L'application est prête à être déployée sur **Streamlit Community Cloud**.

**Étapes de déploiement :**
1.  Héberger le dossier du projet sur un dépôt **GitHub** public.
2.  Se connecter sur [share.streamlit.io](https://share.streamlit.io/).
3.  Cliquer sur « New app » et sélectionner le dépôt, la branche et le fichier `app.py`.
4.  L'URL publique sera générée automatiquement (ex : `https://coworking-idf.streamlit.app`).

> **Remarque :** pensez à remplacer l'URL d'exemple par l'URL réelle une fois le déploiement effectué.

---
*Projet réalisé dans le cadre de l'automatisation data et web.*
