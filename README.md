# Projet Coworking IDF

Application d'aide à la décision pour trouver un espace de coworking à Paris.
Le projet recense, géocode et visualise les espaces de coworking parisiens sur
une carte interactive, avec géolocalisation, filtres avancés et fiches détaillées.

## Structure du projet

- `data/` : fichiers Excel générés (données brutes et géocodées).
- `scripts/` : scripts Python pour le scraping et le géocodage.
- `app.py` : application Streamlit pour la visualisation interactive.
- `document_explicatif.md` / `Rapport_Projet_Coworking.pdf` : rapport du projet.
- `requirements.txt` : liste des dépendances Python.

## Installation

1. Extrayez le ZIP dans un dossier normal (évitez le dossier temporaire de Windows).
2. Ouvrez ce dossier dans votre éditeur, puis installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

> Les données sont déjà fournies dans `data/coworkings_final.xlsx`.
> Vous pouvez donc lancer directement l'application (étape 3) sans relancer le scraping ni le géocodage.

### 1. Scraping des données (optionnel)
Récupère la liste des coworkings et leurs détails depuis la source.
```bash
python scripts/scraping.py
```

### 2. Géocodage (optionnel)
Génère les coordonnées GPS à partir des adresses récupérées.
```bash
python scripts/geocode.py
```

### 3. Lancement de l'application

**Important :** il faut être placé dans le dossier qui contient directement `app.py`
(celui qui contient aussi `data/` et `scripts/`). Sinon Streamlit affiche
« File does not exist: app.py ».

Le plus simple : dans VS Code, faites **Fichier → Ouvrir le dossier** et sélectionnez
le dossier `projet_coworking_final_13062026`, puis ouvrez un nouveau terminal
(**Terminal → Nouveau terminal**). Vous serez automatiquement au bon endroit.

Ensuite, lancez :
```bash
python -m streamlit run app.py
```

Si vous obtenez l'erreur « File does not exist: app.py », c'est que le terminal
n'est pas dans le bon dossier. Vérifiez avec `dir` (Windows) ou `ls` (Mac/Linux) :
vous devez voir `app.py` dans la liste. Si besoin, déplacez-vous avec :
```bash
cd projet_coworking_final_13062026
```

L'application s'ouvre dans le navigateur (généralement http://localhost:8501).

## Fonctionnalités

- Carte interactive (Folium) avec regroupement de marqueurs (MarkerCluster).
- Géolocalisation : bouton navigateur **ou** saisie manuelle d'un point de départ.
- Calcul de distance et filtre « Autour de moi ».
- Tri : pertinence, distance, ordre alphabétique, arrondissement.
- Fiches détaillées avec liens site officiel, Google Maps et itinéraire.
- Gestion des recherches sans résultat : propose automatiquement des alternatives.

## Déploiement (Streamlit Community Cloud)

1. Poussez le code sur un dépôt GitHub public.
2. Connectez votre compte GitHub à [share.streamlit.io](https://share.streamlit.io/).
3. Cliquez sur « New app », sélectionnez le dépôt, la branche et le fichier `app.py`.
4. Cliquez sur « Deploy ». L'URL publique est générée automatiquement.
