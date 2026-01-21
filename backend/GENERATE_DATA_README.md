# Guide de Génération de Données Complètes

## Description

Le script `generate_full_year_data.py` génère des données complètes et réalistes pour votre application de transport :

- **Année 2025 complète** (janvier à décembre) : données historiques pour votre algorithme
- **Départs futurs 2026** : fin janvier (15-31) et tout le mois de février 2026 pour les ventes de billets

## Fonctionnalités

### Données générées pour 2025 :
- ✅ **Départs** : Départs quotidiens avec heures entre 4h et 22h
- ✅ **Billets** : Ventes de billets avec taux d'occupation réaliste (30-95%)
- ✅ **Interventions de maintenance** : Interventions aléatoires tout au long de l'année
- ✅ **Variations réalistes** : Plus de trafic le weekend, fluctuations saisonnières

### Données générées pour 2026 :
- ✅ **Départs programmés** : Départs pour fin janvier et février 2026
- ✅ **Statut "programme"** : Départs prêts pour la vente de billets par les agents
- ✅ **Pas de billets** : Les billets seront créés lors de la vente réelle

## Prérequis

1. **Données de base requises** : Vous devez d'abord exécuter `seed_data.py` pour créer :
   - Les bus
   - Les chauffeurs
   - Les lignes
   - Les destinations
   - Les agents
   - Les techniciens de maintenance

2. **Base de données active** : PostgreSQL doit être démarré

## Utilisation

### Option 1 : Depuis Docker

```bash
docker-compose exec backend python generate_full_year_data.py
```

### Option 2 : Depuis le répertoire backend

```bash
cd backend
python generate_full_year_data.py
```

### Option 3 : Avec Python directement

```bash
python backend/generate_full_year_data.py
```

## Caractéristiques des données

### Heures de départ
- **Plage horaire** : 4h à 22h (comme demandé)
- **Distribution** : Heures variées tout au long de la journée

### Départs quotidiens
- **Semaine** : 5-12 départs par jour
- **Weekend** : 8-15 départs par jour (trafic plus intense)

### Billets (2025 uniquement)
- **Taux d'occupation** : 
  - Semaine : 30-85%
  - Weekend : 40-95%
- **Modes de paiement** : Espèce, Carte, Mobile Money
- **Statuts** : Valide (70%), Utilisé (25%), Annulé (3%), Remboursé (2%)

### Maintenance
- **Probabilité** : ~15% de chance d'intervention par jour
- **Durée selon gravité** :
  - Mineure : 1-2 jours
  - Moyenne : 2-5 jours
  - Majeure : 5-10 jours
  - Critique : 10-20 jours

## Structure des données

### Départs 2025
- Statuts : `programme`, `en_cours`, `termine` (selon la date)
- Chaque départ assigne automatiquement :
  - Un bus disponible
  - Un chauffeur jour (4h-15h) ou nuit (16h-22h)
  - Une ligne et une destination
  - Un prix basé sur la destination

### Départs 2026
- Statut : `programme` (tous)
- Prêts pour la vente de billets
- Assignations automatiques comme pour 2025

## Notes importantes

⚠️ **Attention** : Ce script peut prendre plusieurs minutes à s'exécuter selon la puissance de votre machine.

⚠️ **Données existantes** : Le script ajoute des données sans supprimer les existantes. Pour recommencer, vous devrez nettoyer votre base de données.

⚠️ **Performance** : Le script commit régulièrement pour éviter les problèmes de mémoire.

## Résultat attendu

Après exécution, vous devriez voir :

```
GÉNÉRATION DE DONNÉES COMPLÈTES
Année 2025 (janvier-décembre) + Départs 2026 (fin jan-fév)
============================================================

1. Vérification des données de base...
   ✓ X bus disponibles
   ✓ X chauffeurs actifs
   ✓ X lignes actives
   ✓ X destinations
   ✓ X agents
   ✓ X techniciens

=== Génération des départs pour 2025 ===
  Départs créés: 50, Billets: 1500
  ...
✓ 2025: 3650 départs créés, 45000 billets créés

=== Génération des interventions de maintenance ===
✓ 55 interventions créées

=== Génération des départs pour 2026 (fin jan-fév) ===
  ...
✓ 2026 (fin jan-fév): 450 départs créés, 0 billets créés

RÉSUMÉ DE LA GÉNÉRATION
============================================================
✓ Année 2025:
  - 3650 départs créés
  - 45000 billets créés
  - 55 interventions de maintenance

✓ 2026 (fin janvier - février):
  - 450 départs créés
  - 0 billets créés (simulés)

✅ Génération terminée avec succès!
```

## Support

En cas de problème, vérifiez :
1. Que toutes les données de base existent (bus, chauffeurs, lignes, destinations)
2. Que la base de données est accessible
3. Que vous avez les permissions nécessaires
