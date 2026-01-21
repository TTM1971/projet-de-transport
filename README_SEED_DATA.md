# Génération de Données de Test - Guide d'Utilisation

## Vue d'ensemble

Ce système génère automatiquement un jeu de données réaliste et cohérent sur 30 jours pour alimenter les dashboards avec des graphiques interactifs.

## Données générées

### Utilisateurs
- 1 Admin
- 10 Gestionnaires
- 25 Agents
- 15 Techniciens de Maintenance
- 120 Chauffeurs

### Transport
- 8 villes/destinations (Douala, Yaoundé, Bafoussam, Bamenda, Garoua, Maroua, Kribi, Limbe)
- 18 lignes de transport
- 60 bus (avec différents statuts : en_service, en_maintenance, hors_service)
- Départs programmés sur 30 jours avec affectations bus/chauffeur

### Tickets & Revenus
- Ventes quotidiennes variables (pics le weekend)
- Billets avec statuts (valide, utilise, annule, rembourse)
- Paiements (espece, carte, mobile)
- Chiffre d'affaires journalier en EUR (converti en CAD à l'affichage)

### Maintenance
- Incidents/pannes (freinage, pneus, moteur, électrique, etc.)
- Interventions avec gravité (mineure, moyenne, majeure, critique)
- Coûts et pièces remplacées

## Utilisation

### 1. Exécuter le script de génération

```bash
cd backend
python run_seed.py
```

Ou directement :

```bash
cd backend
python seed_data.py
```

### 2. Vérifier les données générées

Le script affichera un résumé de ce qui a été créé :
- Nombre d'utilisateurs par rôle
- Nombre de destinations, lignes, bus
- Nombre de départs et billets générés
- Nombre d'interventions de maintenance

### 3. Accéder aux dashboards

Connectez-vous en tant qu'admin et accédez au Dashboard Admin pour voir les graphiques interactifs avec les données générées.

## Filtres disponibles dans les endpoints Analytics

Les endpoints `/analytics/dashboard/historical` supportent les filtres suivants :

- `ligne_id` : Filtrer par ligne de transport
- `destination_id` : Filtrer par destination
- `bus_id` : Filtrer par bus spécifique
- `chauffeur_id` : Filtrer par chauffeur
- `start_date` & `end_date` : Plage de dates personnalisée (format: YYYY-MM-DD)
- `days` : Nombre de jours (par défaut: 30)

### Exemple d'utilisation

```
GET /analytics/dashboard/historical?days=30&ligne_id=5&destination_id=3
GET /analytics/dashboard/historical?start_date=2024-01-01&end_date=2024-01-31&bus_id=10
```

## Structure des données

### Cohérence des données
- Un bus ne peut pas être sur 2 voyages au même créneau
- Un chauffeur ne peut pas être sur 2 affectations qui se chevauchent
- Billets vendus ≤ capacité bus
- Si bus en maintenance, statut et indisponibilité respectés

### Logique de simulation
- Génération sur 30 jours à partir d'une date de départ
- Taux d'occupation plus élevé le weekend (50-95%) vs semaine (30-80%)
- Bus anciens (>7 ans) plus à risque de pannes
- Quelques annulations/remboursements (10% des billets)

## Notes importantes

- Les prix sont générés en EUR mais affichés en CAD dans l'interface
- Le script vérifie l'existence des données avant de créer pour éviter les doublons
- Les données sont générées de manière réaliste avec des variations quotidiennes
- La date de départ par défaut est : maintenant - 30 jours
