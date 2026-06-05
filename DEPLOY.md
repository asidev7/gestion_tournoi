# Déploiement sur VPS — tournoi-adeib.site

Guide pas à pas pour déployer l'application ADEIB U26 sur un VPS **Ubuntu/Debian**,
avec **Nginx + Gunicorn + HTTPS (Let's Encrypt)**.

Domaine : `tournoi-adeib.site`
Repo : `https://github.com/asidev7/gestion_tournoi.git`
Chemin cible sur le VPS : `/var/www/tournoi-adeib`

---

## ⚡ Déploiement automatique (recommandé)

Un script automatise les étapes 1 à 8. Sur le VPS :

```bash
# 1. Cloner le repo (une seule fois)
sudo git clone https://github.com/asidev7/gestion_tournoi.git /var/www/tournoi-adeib

# 2. Lancer le script (installe paquets, venv, migrations, Gunicorn, Nginx)
sudo bash /var/www/tournoi-adeib/deploy/deploy.sh
```

Le script génère automatiquement une clé secrète, démarre en HTTP, puis
affiche les **3 commandes finales** pour activer le HTTPS (certbot).
Relancer `deploy.sh` après chaque `git push` met le site à jour.

Les sections ci-dessous décrivent les **mêmes étapes en manuel**, utiles
pour comprendre ou dépanner.

---

## Étape 0 — Pré-requis (à faire AVANT)

1. **DNS** : chez votre registrar, créez deux enregistrements A pointant vers l'IP de votre VPS :
   ```
   tournoi-adeib.site        A    <IP_DU_VPS>
   www.tournoi-adeib.site    A    <IP_DU_VPS>
   ```
   Attendez la propagation (vérifiez avec `dig +short tournoi-adeib.site` → doit renvoyer l'IP).
   Le HTTPS (certbot) **ne marchera pas** tant que le DNS ne pointe pas vers le VPS.

2. Connectez-vous au VPS en SSH : `ssh root@<IP_DU_VPS>` (ou votre utilisateur sudo).

---

## Étape 1 — Installer les paquets système

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git nginx
```

---

## Étape 2 — Cloner le repo

```bash
sudo mkdir -p /var/www
sudo git clone https://github.com/asidev7/gestion_tournoi.git /var/www/tournoi-adeib
cd /var/www/tournoi-adeib
```

> Le repo contient déjà `db.sqlite3` et les médias : vos données existantes
> (équipes, joueurs, matchs…) seront donc présentes dès le clonage.

---

## Étape 3 — Environnement virtuel + dépendances

```bash
cd /var/www/tournoi-adeib
sudo python3 -m venv venv
sudo venv/bin/pip install --upgrade pip
sudo venv/bin/pip install -r requirements.txt
```

---

## Étape 4 — Configurer les variables d'environnement (.env)

Générez une clé secrète :
```bash
venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Créez le fichier `.env` :
```bash
sudo cp deploy/.env.example .env
sudo nano .env
```
Collez la clé générée dans `DJANGO_SECRET_KEY` et enregistrez.

> ⚠️ Pour la **première mise en route en HTTP** (avant certbot), mettez
> temporairement `DJANGO_SECURE_SSL_REDIRECT=False` dans `.env`.
> Vous le repasserez à `True` après l'installation du certificat SSL.

---

## Étape 5 — Migrations + fichiers statiques

```bash
cd /var/www/tournoi-adeib
set -a; source .env; set +a
venv/bin/python manage.py migrate
venv/bin/python manage.py collectstatic --noinput
```

(Optionnel) Créer un compte admin si besoin :
```bash
venv/bin/python manage.py createsuperuser
```

---

## Étape 6 — Permissions (Nginx/Gunicorn tournent sous www-data)

```bash
sudo chown -R www-data:www-data /var/www/tournoi-adeib
sudo chmod 664 /var/www/tournoi-adeib/db.sqlite3
sudo chmod 775 /var/www/tournoi-adeib   # pour que SQLite puisse écrire le journal
```

---

## Étape 7 — Service Gunicorn (systemd)

```bash
sudo cp /var/www/tournoi-adeib/deploy/gunicorn.service /etc/systemd/system/gunicorn-tournoi.service
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-tournoi
sudo systemctl status gunicorn-tournoi --no-pager
```
Le statut doit être **active (running)**. En cas d'erreur :
`sudo journalctl -u gunicorn-tournoi -n 50 --no-pager`

---

## Étape 8 — Nginx

```bash
sudo cp /var/www/tournoi-adeib/deploy/nginx.conf /etc/nginx/sites-available/tournoi-adeib
sudo ln -sf /etc/nginx/sites-available/tournoi-adeib /etc/nginx/sites-enabled/tournoi-adeib
sudo rm -f /etc/nginx/sites-enabled/default   # désactive la page par défaut
sudo nginx -t                                 # teste la config
sudo systemctl restart nginx
```

Testez maintenant en HTTP : ouvrez `http://tournoi-adeib.site` dans un navigateur.
Le site doit s'afficher.

---

## Étape 9 — HTTPS avec Let's Encrypt (certbot)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tournoi-adeib.site -d www.tournoi-adeib.site
```
Répondez aux questions (email, conditions). Certbot modifie automatiquement
la config Nginx pour ajouter le HTTPS et la redirection HTTP→HTTPS.

Le renouvellement est automatique. Pour le vérifier :
```bash
sudo certbot renew --dry-run
```

---

## Étape 10 — Réactiver la redirection SSL côté Django

Une fois le HTTPS en place, rééditez `.env` :
```bash
sudo nano /var/www/tournoi-adeib/.env   # DJANGO_SECURE_SSL_REDIRECT=True
sudo systemctl restart gunicorn-tournoi
```

✅ Le site est en ligne sur **https://tournoi-adeib.site**

---

## Mettre à jour le site après un nouveau push GitHub

```bash
cd /var/www/tournoi-adeib
sudo -u www-data git pull
sudo venv/bin/pip install -r requirements.txt
set -a; source .env; set +a
sudo venv/bin/python manage.py migrate
sudo venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart gunicorn-tournoi
```

---

## Dépannage rapide

| Problème | Piste |
|----------|-------|
| **502 Bad Gateway** | Gunicorn est down → `sudo systemctl status gunicorn-tournoi` et les logs `journalctl -u gunicorn-tournoi` |
| **Boucle de redirection (ERR_TOO_MANY_REDIRECTS)** | Vérifiez que `SECURE_PROXY_SSL_HEADER` est bien dans settings (déjà ajouté) et que certbot a bien posé le bloc 443 |
| **403 / static manquants** | `collectstatic` non lancé, ou permissions → `chown -R www-data:www-data` |
| **CSRF verification failed** | `DJANGO_ALLOWED_HOSTS` doit contenir le domaine ; en Django 4+, `CSRF_TRUSTED_ORIGINS` peut être requis (voir note ci-dessous) |
| **DisallowedHost** | Ajoutez le domaine dans `DJANGO_ALLOWED_HOSTS` du `.env` |

> **Note CSRF (Django 4+)** : si après HTTPS un formulaire renvoie une erreur CSRF,
> ajoutez dans `.env` la variable et adaptez settings pour lire
> `CSRF_TRUSTED_ORIGINS=https://tournoi-adeib.site,https://www.tournoi-adeib.site`.
> Dites-le moi et je l'ajoute au code.
