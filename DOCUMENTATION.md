# Documentation Technique — ADEIB U26 Illara

> Système de gestion de tournoi de football développé avec Django.
> Gestion des équipes, joueurs, matchs, classements, phases éliminatoires, billetterie et pronostics.

---

## Table des matières

1. [Présentation du projet](#1-présentation-du-projet)
2. [Stack technique](#2-stack-technique)
3. [Architecture du projet](#3-architecture-du-projet)
4. [Installation et démarrage](#4-installation-et-démarrage)
5. [Modèles de données](#5-modèles-de-données)
6. [Routes (URLs)](#6-routes-urls)
7. [Panel d'administration](#7-panel-dadministration)
8. [Système de billetterie](#8-système-de-billetterie)
9. [Système de pronostics](#9-système-de-pronostics)
10. [Configuration](#10-configuration)
11. [Déploiement en production](#11-déploiement-en-production)
12. [Commandes utiles](#12-commandes-utiles)

---

## 1. Présentation du projet

**ADEIB U26 Illara** est une application web Django destinée à organiser et gérer
un tournoi de football. Elle couvre l'ensemble du cycle de vie d'un tournoi :

- Inscription publique des équipes (avec preuve de paiement)
- Gestion des équipes, joueurs et groupes
- Génération automatique des matchs de poules
- Suivi des scores en direct et des buteurs
- Calcul automatique des classements
- Génération des phases éliminatoires (quarts, demies, 3e place, finale)
- Génération et impression de tickets d'entrée (PDF)
- Pronostics des utilisateurs avec classement

Le projet comprend **deux applications Django** : `tournament` (cœur métier) et
`betting` (pronostics).

---

## 2. Stack technique

| Composant | Technologie |
|-----------|-------------|
| Langage | Python 3.12 |
| Framework | Django ≥ 5.0, < 5.2 |
| Base de données | SQLite (développement) |
| Interface admin | Django Admin + [Jazzmin](https://django-jazzmin.readthedocs.io/) ≥ 3.0 |
| Formulaires | django-crispy-forms ≥ 2.0 + crispy-bootstrap5 |
| Frontend | Templates Django + Bootstrap 5 |
| Images | Pillow ≥ 10.0 |
| QR codes | qrcode ≥ 7.0 |
| Génération PDF | reportlab ≥ 4.0 |
| Langue / Fuseau | `fr-fr` / `Africa/Porto-Novo` |

Dépendances complètes : voir [`requirements.txt`](requirements.txt).

---

## 3. Architecture du projet

```
sport_adeib/
├── config/                  # Configuration Django
│   ├── settings.py          # Paramètres (apps, BDD, sécurité, Jazzmin)
│   ├── urls.py              # Routage racine
│   ├── wsgi.py / asgi.py    # Points d'entrée serveur
│
├── tournament/              # Application principale (cœur métier)
│   ├── models.py            # Tournament, Group, Team, Player, Match, Goal,
│   │                        #   Standing, KnockoutMatch, TeamRegistration,
│   │                        #   TicketConfig, Ticket
│   ├── views.py             # Vues publiques + panel admin custom
│   ├── admin.py             # Configuration de l'admin Jazzmin
│   ├── forms.py             # Formulaires CRUD
│   ├── urls.py              # Routes de l'application
│   ├── pdf_generator.py     # Génération PDF des tickets (reportlab)
│   ├── ticket_designer.py   # Designer de tickets « cool »
│   ├── context_processors.py# `active_tournament` injecté dans les templates
│   ├── templatetags/        # Filtres de template personnalisés (math_filters)
│   └── management/commands/ # Commandes manage.py (seed, etc.)
│
├── betting/                 # Application de pronostics
│   ├── models.py            # Prediction, PredictionLeaderboard
│   ├── views.py             # Vues de pronostics
│   └── urls.py              # Routes des pronostics
│
├── templates/               # Templates HTML (Bootstrap 5)
├── static/                  # CSS, JS, images
├── media/                   # Uploads : logos, photos, QR codes, tickets
├── db.sqlite3               # Base de données SQLite (dev)
├── manage.py                # Utilitaire Django
└── requirements.txt         # Dépendances Python
```

### Applications installées (`INSTALLED_APPS`)

```python
jazzmin, django.contrib.admin, auth, contenttypes, sessions,
messages, staticfiles, crispy_forms, crispy_bootstrap5,
tournament, betting
```

---

## 4. Installation et démarrage

### Prérequis
- Python 3.12
- pip

### Étapes

```bash
# 1. Cloner le projet et entrer dans le dossier
cd sport_adeib

# 2. Créer et activer un environnement virtuel
python3 -m venv env
source env/bin/activate          # Linux / macOS
# env\Scripts\activate           # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Appliquer les migrations
python manage.py migrate

# 5. Créer un superutilisateur (accès admin)
python manage.py createsuperuser

# 6. Lancer le serveur de développement
python manage.py runserver
```

L'application est ensuite accessible sur **http://127.0.0.1:8000/**.

---

## 5. Modèles de données

### Application `tournament`

#### Tournament
Tournoi principal et ses métadonnées.

| Champ | Type | Description |
|-------|------|-------------|
| `name` | CharField | Nom (défaut : *ADEIB U26 Illara*) |
| `edition` | CharField | Édition |
| `start_date` / `end_date` | DateField | Dates de début / fin |
| `location` | CharField | Lieu |
| `description` | TextField | Description |
| `logo` | ImageField | Logo (`tournament/`) |
| `is_active` | BooleanField | Tournoi actif (défaut : `True`) |

#### Group
Groupes de la phase de poules. Choix : **A**, **B**, **C**. Lié à un `Tournament`.

#### Team
Équipe participante.

| Champ | Type | Description |
|-------|------|-------------|
| `tournament` | FK Tournament | Tournoi de rattachement |
| `name` | CharField | Nom de l'équipe |
| `logo` | ImageField | Logo (`teams/`) |
| `group` | FK Group | Groupe (nullable) |
| `qr_code` | ImageField | QR code généré (`qrcodes/`) |

- **`generate_qr_code()`** : génère un QR code contenant le nom de l'équipe et du tournoi.
- **`player_count`** *(property)* : nombre de joueurs de l'équipe.

#### Player
Joueur d'une équipe.

| Champ | Type | Description |
|-------|------|-------------|
| `team` | FK Team | Équipe |
| `first_name` / `last_name` | CharField | Prénom / Nom |
| `age` | PositiveInteger | Âge |
| `position` | Choices | `GK` (Gardien), `DEF`, `MID`, `FWD` |
| `jersey_number` | PositiveInteger | Numéro de maillot |
| `photo` | ImageField | Photo (`players/`) |
| `is_captain` | BooleanField | Capitaine |

- **`full_name`** / **`goals_count`** *(properties)*.

#### Match
Match (phase de groupes ou éliminatoire).

| Champ | Type | Description |
|-------|------|-------------|
| `phase` | Choices | `GROUP`, `QF`, `SF`, `3RD`, `FINAL` |
| `group` | FK Group | Groupe (si phase de poules) |
| `home_team` / `away_team` | FK Team | Équipes |
| `match_date` | DateTime | Date et heure |
| `venue` | CharField | Lieu (défaut : *Terrain ADEIB, Illara*) |
| `home_score` / `away_score` | PositiveInteger | Scores |
| `status` | Choices | `SCHEDULED`, `LIVE`, `FINISHED`, `CANCELLED` |
| `matchday` | PositiveInteger | Journée |
| `live_started_at` | DateTime | Horodatage du coup d'envoi (live) |

- **`result`** *(property)* : `HOME` / `AWAY` / `DRAW` (si terminé).
- **`score_display`** *(property)* : affichage du score ou « vs ».

#### Goal
But marqué.

| Champ | Description |
|-------|-------------|
| `match`, `player`, `team` | Match, buteur, équipe |
| `minute` | Minute du but |
| `is_own_goal` | But contre son camp (CSC) |
| `is_penalty` | Sur penalty |

#### Standing
Classement d'un groupe, **recalculé automatiquement** depuis les matchs terminés.

| Champ | Description |
|-------|-------------|
| `played, won, drawn, lost` | Joués / Gagnés / Nuls / Perdus |
| `goals_for, goals_against` | Buts pour / contre |
| `points` | Points (victoire = 3, nul = 1) |

- **`goal_difference`** *(property)* : différence de buts.
- **`update_from_matches()`** : recalcule toutes les statistiques de l'équipe
  à partir des matchs `FINISHED` du groupe. Tri : `-points`, `-goals_for`.

#### KnockoutMatch
Match de phase éliminatoire avec gestion des tirs au but.

| Champ | Description |
|-------|-------------|
| `round` | `QF`, `SF`, `3RD`, `FINAL` |
| `match_number` | Numéro du match |
| `home_team` / `away_team` | Équipes (nullable → « TBD ») |
| `home_score` / `away_score` | Scores |
| `home_penalties` / `away_penalties` | Tirs au but |
| `status` | `SCHEDULED`, `LIVE`, `FINISHED` |
| `winner` | Vainqueur |

- **`determine_winner()`** : détermine le vainqueur (score, puis tirs au but).

#### TeamRegistration
Inscription publique d'une équipe.

| Champ | Description |
|-------|-------------|
| `team_name`, `captain_name`, `phone`, `email` | Coordonnées |
| `neighborhood` | Quartier / Village |
| `player_count` | Nombre de joueurs (défaut : 11) |
| `payment_proof` | Preuve de paiement (image) |
| `notes` | Remarques |
| `status` | `PENDING` → `APPROVED` / `REJECTED` |

#### TicketConfig
Configuration de génération de tickets pour un match (relation 1-1 avec `Match`).

| Champ | Description |
|-------|-------------|
| `price` / `currency` | Prix / Devise (`NGN` ₦, `XOF` CFA) |
| `ticket_size` | `small` (10/page), `medium` (6), `large` (4), `premium` (2 A4) |
| `quantity` | Nombre de tickets à générer |
| `gate_opens` / `gate_closes` | Heures d'ouverture / fermeture |

- **`currency_symbol`** / **`price_display`** *(properties)*.

#### Ticket
Ticket individuel généré.

| Champ | Description |
|-------|-------------|
| `ticket_number` | Numéro unique |
| `seat_number` | Place |
| `status` | `AVAILABLE`, `SOLD`, `USED`, `CANCELLED` |
| `buyer_name` / `buyer_phone` | Acheteur |

### Application `betting`

#### Prediction
Pronostic d'un utilisateur sur un match (unique par `user` + `match`).

| Champ | Description |
|-------|-------------|
| `prediction` | `1`, `X`, `2`, `1X`, `X2`, `12` |
| `odds` | Cote |
| `is_correct` | Évalué après le match |

- **`check_prediction()`** : compare le pronostic au résultat du match terminé
  et met à jour `is_correct`.

#### PredictionLeaderboard
Classement des pronostiqueurs (relation 1-1 avec `User`).

- **`success_rate`** *(property)* : taux de réussite en %.
- **`update()`** : recalcule total, bons pronostics et points (10 pts / bon pronostic).

---

## 6. Routes (URLs)

### Pages publiques (`tournament`)

| URL | Vue | Description |
|-----|-----|-------------|
| `/` | `home` | Page d'accueil |
| `/teams/` | `teams_list` | Liste des équipes |
| `/teams/<pk>/` | `team_detail` | Détail d'une équipe |
| `/matches/` | `matches_list` | Calendrier des matchs |
| `/matches/<pk>/` | `match_detail` | Détail d'un match |
| `/standings/` | `standings_view` | Classements par groupe |
| `/statistics/` | `statistics_view` | Statistiques (buteurs…) |
| `/bracket/` | `bracket_view` | Tableau éliminatoire |
| `/inscription/` | `register_team` | Formulaire d'inscription |
| `/inscription/merci/` | `register_team_success` | Confirmation d'inscription |

### API (AJAX)

| URL | Description |
|-----|-------------|
| `/api/live-scores/` | Scores en direct |
| `/api/matches/<pk>/goals/` | Buts d'un match |

### Pronostics (`betting`, préfixe `/pronostics/`)

| URL | Vue | Description |
|-----|-----|-------------|
| `/pronostics/` | `predictions_list` | Liste des matchs à pronostiquer |
| `/pronostics/match/<match_pk>/` | `make_prediction` | Faire un pronostic |
| `/pronostics/mes-pronostics/` | `my_predictions` | Mes pronostics |

### Admin Django

| URL | Description |
|-----|-------------|
| `/admin/` | Django Admin (thème Jazzmin) |

---

## 7. Panel d'administration

Un **panel admin personnalisé** est disponible à `/admin-panel/`, distinct de
l'admin Django. Il regroupe la gestion opérationnelle du tournoi.

| URL | Fonction |
|-----|----------|
| `/admin-panel/` | Tableau de bord |
| `/admin-panel/tournament/` | Configuration du tournoi |
| `/admin-panel/teams/` | Gestion des équipes (liste, ajout, édition, suppression) |
| `/admin-panel/teams/<pk>/players/add/` | Ajout de joueurs |
| `/admin-panel/matches/` | Gestion des matchs et scores |
| `/admin-panel/matches/generate/` | Génération automatique des matchs de poules |
| `/admin-panel/matches/<pk>/score/` | Mise à jour des scores |
| `/admin-panel/matches/<pk>/goals/add/` | Ajout de buts |
| `/admin-panel/knockout/generate/` | Génération des phases éliminatoires |
| `/admin-panel/knockout/<pk>/score/` | Score d'un match éliminatoire |
| `/admin-panel/tickets/` | Gestion de la billetterie |
| `/admin-panel/ticket-designer/` | Designer de tickets personnalisés |

> Accès protégé : `LOGIN_URL = /admin/login/`, redirection après connexion vers
> `/admin-panel/`.

---

## 8. Système de billetterie

Le module de billetterie permet de configurer, générer et imprimer des tickets
d'entrée au format PDF (via **reportlab**).

**Flux :**
1. Configurer les tickets d'un match : `/admin-panel/matches/<match_pk>/tickets/config/`
   (prix, devise, format, quantité, horaires).
2. Générer les tickets : `/admin-panel/tickets/<config_pk>/generate/`.
3. Prévisualiser : `/admin-panel/tickets/<config_pk>/preview/`.
4. Télécharger le PDF : `/admin-panel/tickets/<config_pk>/download/`.

**Formats disponibles** : petit (10/page), moyen (6/page), grand (4/page),
premium A4 paysage (2/page).

Un **designer de tickets « cool »** offre des tickets au design unique :
- Aperçu : `/admin-panel/matches/<match_pk>/tickets/cool/preview/`
- Génération : `/admin-panel/matches/<match_pk>/tickets/cool/generate/`

Fichiers concernés : `tournament/pdf_generator.py`, `tournament/ticket_designer.py`.

---

## 9. Système de pronostics

Application `betting`. Les utilisateurs authentifiés peuvent pronostiquer
le résultat des matchs (1, X, 2 et doubles chances).

- Un pronostic est **unique** par utilisateur et par match.
- Après la fin d'un match, `Prediction.check_prediction()` valide le pronostic.
- `PredictionLeaderboard.update()` recalcule les points (**10 points par bon
  pronostic**) et alimente le classement.

---

## 10. Configuration

Fichier : [`config/settings.py`](config/settings.py).

### Paramètres clés

| Paramètre | Valeur |
|-----------|--------|
| `LANGUAGE_CODE` | `fr-fr` |
| `TIME_ZONE` | `Africa/Porto-Novo` |
| `USE_TZ` | `True` |
| Base de données | SQLite (`db.sqlite3`) |
| `STATIC_URL` / `STATIC_ROOT` | `/static/` / `staticfiles/` |
| `MEDIA_URL` / `MEDIA_ROOT` | `/media/` / `media/` |
| `LOGIN_URL` | `/admin/login/` |
| `LOGIN_REDIRECT_URL` | `/admin-panel/` |

### Sécurité

- En **production** (`DEBUG=False`) : activation de `SECURE_SSL_REDIRECT`,
  HSTS, cookies sécurisés (session + CSRF).
- En **développement / runserver** : redirections SSL désactivées.

### Context processor

`tournament.context_processors.active_tournament` injecte le tournoi actif
dans tous les templates.

---

## 11. Déploiement en production

### Variables d'environnement à définir

```bash
DJANGO_SECRET_KEY=<clé-secrète-forte>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=adeibu26.com,www.adeibu26.com

# Optionnelles (sécurité, valeurs par défaut sensées)
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
DJANGO_SECURE_SSL_REDIRECT=True
```

> ⚠️ La `SECRET_KEY` par défaut présente dans le code ne doit **jamais** être
> utilisée en production. Définissez toujours `DJANGO_SECRET_KEY`.

### Étapes

```bash
export DJANGO_DEBUG=False
export DJANGO_SECRET_KEY="..."
export DJANGO_ALLOWED_HOSTS="adeibu26.com"

python manage.py migrate
python manage.py collectstatic --noinput
# Lancer via gunicorn / uwsgi derrière nginx
```

> Pour la production, envisagez de migrer SQLite vers PostgreSQL et de servir
> les fichiers `media/` et `static/` via un serveur web ou un stockage objet.

---

## 12. Commandes utiles

```bash
# Serveur de développement
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Superutilisateur
python manage.py createsuperuser

# Données de démonstration (seed)
python manage.py seed

# Collecte des fichiers statiques (production)
python manage.py collectstatic

# Tests
python manage.py test
```

---

## Flux de mise en place d'un tournoi

1. **Créer un tournoi** (`/admin-panel/tournament/` ou Django Admin).
2. **Ajouter les groupes** A, B, C.
3. **Créer les équipes** et les assigner aux groupes.
4. **Ajouter les joueurs** de chaque équipe.
5. **Générer les matchs de poules** (`/admin-panel/matches/generate/`).
6. **Gérer les scores** en direct ou après match ; ajouter les buts.
7. Les **classements** se recalculent automatiquement (`Standing.update_from_matches()`).
8. **Générer les phases éliminatoires** à la fin des poules
   (`/admin-panel/knockout/generate/`).
9. **Configurer et imprimer la billetterie** par match.

---

*Documentation générée à partir du code source (Django 5.x). Pour toute
modification du modèle de données, pensez à regénérer les migrations.*
