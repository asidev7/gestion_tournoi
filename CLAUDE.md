# ADEIB U26 - Système de Gestion de Tournoi

## Vue d'ensemble
Application Django pour la gestion de tournois de football (ADEIB U26 Illara). Le système gère les équipes, joueurs, matchs, classements et pronostics.

## Architecture

### Stack Technique
- **Backend**: Django 5.x, Python 3.12
- **Database**: SQLite (développement)
- **Frontend**: Templates Django + Bootstrap 5
- **UI Admin**: Jazzmin (thème moderne pour Django Admin)
- **Formulaires**: Crispy Forms

### Structure des Apps
```
tournament/          # Cœur métier du tournoi
├── models.py        # Tournament, Team, Player, Match, Goal, Standing, KnockoutMatch
├── views.py         # Vues publiques + panel admin custom
├── admin.py         # Configuration Jazzmin
├── forms.py         # Formulaires CRUD
└── urls.py          # Routes de l'application

betting/             # Système de pronostics
├── models.py        # Prediction, PredictionLeaderboard
└── urls.py          # Routes API pronostics

config/              # Configuration Django
├── settings.py
├── urls.py
└── wsgi.py

static/              # CSS, JS, images
media/               # Uploads (logos, photos, QR codes)
templates/           # Templates HTML
```

## Modèles de Données

### Tournament
Tournoi principal (ex: ADEIB U26 Illara). Contient les métadonnées du tournoi.

### Group
Groupes de la phase de poules (A, B, C).

### Team
Équipe participante avec:
- Génération automatique de QR codes
- Association à un groupe
- Comptage des joueurs

### Player
Joueur avec position (GK/DEF/MID/FWD), numéro, photo, statut capitaine.

### Match
Match de phase de groupes avec:
- Statuts: SCHEDULED, LIVE, FINISHED, CANCELLED
- Score et calcul automatique du résultat
- Support des matchs en direct

### Goal
But marqué avec minute, type ( CSC, penalty).

### Standing
Classement calculé automatiquement depuis les matchs terminés. Méthode `update_from_matches()` pour recalculer.

### KnockoutMatch
Match éliminatoire (quarts, demies, finale, 3e place) avec support des tirs au but.

### TeamRegistration
Formulaire d'inscription publique pour les équipes (avec preuve de paiement).

## URLs Principales

| URL | Description |
|-----|-------------|
| `/` | Page d'accueil |
| `/teams/` | Liste des équipes |
| `/matches/` | Calendrier des matchs |
| `/standings/` | Classements par groupe |
| `/bracket/` | Tableau éliminatoire |
| `/statistics/` | Stats (buteurs, etc.) |
| `/inscription/` | Formulaire d'inscription équipe |
| `/admin-panel/` | Dashboard admin custom |
| `/pronostics/` | Système de pronostics |
| `/admin/` | Django Admin (Jazzmin) |

## Panel Admin Custom

Accessible à `/admin-panel/` avec interface dédiée pour:
- Configuration du tournoi
- Gestion des équipes et joueurs
- Gestion des matchs et scores
- Génération automatique des matchs de poules
- Génération des matchs éliminatoires
- Mise à jour des scores en direct

## Commandes Utiles

```bash
# Lancer le serveur de développement
python manage.py runserver

# Créer un superutilisateur
python manage.py createsuperuser

# Générer les QR codes pour toutes les équipes
python manage.py generate_qr_codes

# Migrations
python manage.py makemigrations
python manage.py migrate

# Collecter les fichiers statiques (prod)
python manage.py collectstatic
```

## Configuration Important

### Settings Clés (`config/settings.py`)
- `LANGUAGE_CODE = 'fr-fr'` - Interface en français
- `TIME_ZONE = 'Africa/Porto-Novo'` - Fuseau horaire Bénin
- `JAZZMIN_SETTINGS` - Personnalisation de l'admin

### Variables d'Environnement à Définir (Production)
```bash
DJANGO_SECRET_KEY=<clé-secrète>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=adeibu26.com
```

## Flux de Développement

1. **Créer un tournoi** via Django Admin
2. **Ajouter les groupes** (A, B, C)
3. **Créer les équipes** et les assigner aux groupes
4. **Ajouter les joueurs** à chaque équipe
5. **Générer les matchs** de poules via le panel admin
6. **Gérer les scores** en direct ou post-match
7. **Générer les phases éliminatoires** à la fin des poules

## Points d'Attention

- Les QR codes sont générés automatiquement à la création d'une équipe
- Le classement est recalculé via `Standing.update_from_matches()`
- Les matchs en direct ont un statut `LIVE` avec horodatage `live_started_at`
- Les inscriptions passent par une validation (PENDING → APPROVED)
- Les photos et logos sont stockés dans `/media/`
