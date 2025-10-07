# tikidata

## Proposition d'application : tableau de bord d'analyse de match de football

Cette proposition décrit une application web qui permet d'analyser un match de football en se basant sur des données récupérées automatiquement sur le web. L'objectif est d'offrir aux utilisateurs (analystes, entraîneurs, supporters) un tableau de bord complet avec des indicateurs clés de performance (KPI) pour les équipes et les joueurs impliqués.

### Fonctionnalités principales

1. **Sélection du match**  
   - Entrées : championnat, saison et noms des deux clubs.  
   - Autocomplétion sur les champs pour limiter les erreurs de saisie et accélérer la sélection.  
   - Possibilité d'enregistrer des combinaisons « championnat / saison / équipes » favorites.

2. **Collecte des données**  
   - Scraping automatisé des sites de statistiques football (par exemple FBref, Understat) lorsque l'utilisateur valide sa sélection.  
   - Mise en cache des résultats pour éviter des requêtes répétées et améliorer les performances.  
   - Gestion des erreurs (match indisponible, changement de format du site) avec messages clairs à l'utilisateur.

3. **Tableau de bord des équipes**  
   - Vue globale présentant les KPI offensifs, défensifs et de possession pour chaque équipe : tirs (total / cadrés / expected goals), passes (réussies / clés), duels gagnés, interventions défensives, zones d'attaque, etc.  
   - Visualisations interactives (graphiques radar, heatmaps, timelines de momentum) pour comparer les performances des deux clubs.  
   - Section « Temps forts » listant les événements importants (buts, cartons, changements) avec liens vers des extraits vidéo si disponibles.

4. **Analyse individuelle des joueurs**  
   - Liste des joueurs alignés avec leurs positions et temps de jeu.  
   - Possibilité de sélectionner un ou plusieurs joueurs pour afficher leurs statistiques détaillées : xG, passes progressives, tacles réussis, cartes reçues, pressing, etc.  
   - Comparaison joueur vs. moyenne de l'équipe ou de la ligue.  
   - Heatmap de positionnement sur le terrain et graphiques d'évolution au fil du match.

5. **Export et partage**  
   - Export des rapports en PDF ou CSV.  
   - Génération de liens partageables vers une vue en lecture seule du tableau de bord.  
   - Intégration possible avec des outils collaboratifs (Notion, Slack) via webhooks.

### Architecture technique proposée

- **Frontend** : application Streamlit ou React pour construire rapidement des interfaces interactives. Streamlit permet de prototyper efficacement tout en offrant des composants prêts à l'emploi (sélecteurs, graphiques).  
- **Backend** : API Python (FastAPI) chargée de piloter le scraping, d'orchestrer les appels aux sources de données et de servir les données nettoyées au frontend.  
- **Scraping & données** : utilisation de bibliothèques comme `requests`, `BeautifulSoup`, `Selenium` (si nécessaire), et `pandas` pour manipuler les tableaux statistiques.  
- **Stockage** : base de données légère (SQLite ou PostgreSQL) pour conserver l'historique des matchs et les caches.  
- **Observabilité** : journaux structurés (loggers Python) et monitoring basique (ex. Prometheus + Grafana) pour suivre les erreurs de scraping et les performances.

### Parcours utilisateur type

1. L'utilisateur sélectionne le championnat (ex. Ligue 1), la saison (ex. 2023/2024) et les deux clubs (ex. PSG vs. OM).  
2. L'application lance le scraping pour récupérer les statistiques du match ciblé.  
3. Les données sont agrégées et normalisées avant d'être présentées dans le tableau de bord principal.  
4. L'utilisateur explore les KPI d'équipe, puis sélectionne un ou plusieurs joueurs pour obtenir leur analyse détaillée.  
5. Il exporte un rapport PDF et partage un lien avec son staff.

### Évolutions futures

- Ajout de modèles de machine learning pour détecter des schémas tactiques ou prédire des performances futures.  
- Intégration de flux vidéo pour synchroniser les statistiques avec les actions en temps réel.  
- Application mobile ou PWA pour consultation rapide sur le terrain.  
- Système d'alertes personnalisées (ex. notifications en cas d'anomalie ou de performance notable).

Cette application offrirait une plateforme complète pour analyser un match de football à partir de données disponibles publiquement, avec un accent sur la visualisation claire des KPI et la flexibilité d'explorer les performances individuelles des joueurs.

## Lancer le tableau de bord Streamlit

1. Installez les dépendances Python (de préférence dans un environnement virtuel):
   ```bash
   pip install -r requirements.txt
   ```
2. Démarrez l'application Streamlit:
   ```bash
   streamlit run streamlit_app.py
   ```
3. Dans l'interface, choisissez le championnat, la saison et les clubs à analyser, puis cliquez sur **Analyser le match** pour lancer le scraping et explorer les KPI détaillés.
