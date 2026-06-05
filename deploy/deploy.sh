#!/usr/bin/env bash
#
# Script de déploiement / mise à jour pour tournoi-adeib.site
# À exécuter SUR LE VPS (Ubuntu/Debian) avec sudo.
#
#   Première installation :   sudo bash deploy/deploy.sh
#   Mise à jour (après push): sudo bash deploy/deploy.sh
#
# Le script est idempotent : on peut le relancer sans risque.
# Il N'INSTALLE PAS le certificat HTTPS (certbot) — c'est une étape manuelle
# unique, voir la fin du script et DEPLOY.md (étape 9).

set -euo pipefail

# --- Configuration ---------------------------------------------------------
APP_DIR="/var/www/tournoi-adeib"
REPO_URL="https://github.com/asidev7/gestion_tournoi.git"
DOMAIN="tournoi-adeib.site"
SERVICE="gunicorn-tournoi"
RUN_USER="www-data"
# ---------------------------------------------------------------------------

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
err() { printf '\n\033[1;31mERREUR: %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || err "Lancez ce script avec sudo (root)."

# --- 1. Paquets système ----------------------------------------------------
log "Installation des paquets système (python, git, nginx)…"
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git nginx

# --- 2. Clone ou mise à jour du repo ---------------------------------------
if [[ -d "$APP_DIR/.git" ]]; then
    log "Repo déjà présent — mise à jour (git pull)…"
    git -C "$APP_DIR" pull --ff-only
else
    log "Clonage du repo dans $APP_DIR…"
    mkdir -p "$(dirname "$APP_DIR")"
    git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

# --- 3. Environnement virtuel + dépendances --------------------------------
if [[ ! -d "$APP_DIR/venv" ]]; then
    log "Création de l'environnement virtuel…"
    python3 -m venv venv
fi
log "Installation des dépendances Python…"
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt -q

# --- 4. Fichier .env -------------------------------------------------------
if [[ ! -f "$APP_DIR/.env" ]]; then
    log "Création du fichier .env (à compléter !)…"
    cp deploy/.env.example .env
    SECRET="$(venv/bin/python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
    # Injecte une clé secrète générée et démarre en HTTP (avant certbot)
    sed -i "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=${SECRET}|" .env
    sed -i "s|^DJANGO_SECURE_SSL_REDIRECT=.*|DJANGO_SECURE_SSL_REDIRECT=False|" .env
    NEW_ENV=1
else
    log ".env déjà présent — conservé tel quel."
    NEW_ENV=0
fi

# --- 5. Migrations + statiques --------------------------------------------
set -a; source "$APP_DIR/.env"; set +a
log "Application des migrations…"
venv/bin/python manage.py migrate --noinput
log "Collecte des fichiers statiques…"
venv/bin/python manage.py collectstatic --noinput

# --- 6. Permissions --------------------------------------------------------
log "Réglage des permissions ($RUN_USER)…"
chown -R "$RUN_USER:$RUN_USER" "$APP_DIR"
chmod 775 "$APP_DIR"
[[ -f "$APP_DIR/db.sqlite3" ]] && chmod 664 "$APP_DIR/db.sqlite3"

# --- 7. Service systemd (Gunicorn) ----------------------------------------
log "Installation/maj du service systemd $SERVICE…"
cp "$APP_DIR/deploy/gunicorn.service" "/etc/systemd/system/${SERVICE}.service"
systemctl daemon-reload
systemctl enable "$SERVICE" >/dev/null 2>&1 || true
systemctl restart "$SERVICE"
sleep 1
systemctl is-active --quiet "$SERVICE" || err "Gunicorn n'a pas démarré. Voir: journalctl -u $SERVICE -n 50"

# --- 8. Nginx --------------------------------------------------------------
log "Configuration de Nginx…"
cp "$APP_DIR/deploy/nginx.conf" "/etc/nginx/sites-available/tournoi-adeib"
ln -sf "/etc/nginx/sites-available/tournoi-adeib" "/etc/nginx/sites-enabled/tournoi-adeib"
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# --- Fin -------------------------------------------------------------------
log "Déploiement terminé ✅"
echo
echo "  Le site doit être accessible en HTTP : http://${DOMAIN}"
echo

if [[ "$NEW_ENV" -eq 1 ]]; then
    cat <<EOF
  -------------------------------------------------------------------
  PROCHAINES ÉTAPES (première installation) :

  1) Vérifiez le DNS : dig +short ${DOMAIN}  (doit renvoyer l'IP du VPS)

  2) Activez le HTTPS (certificat gratuit Let's Encrypt) :
       sudo apt install -y certbot python3-certbot-nginx
       sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}

  3) Réactivez la redirection HTTPS côté Django :
       sudo sed -i 's/^DJANGO_SECURE_SSL_REDIRECT=.*/DJANGO_SECURE_SSL_REDIRECT=True/' ${APP_DIR}/.env
       sudo systemctl restart ${SERVICE}

  (Optionnel) Créer un compte admin :
       cd ${APP_DIR} && sudo -u ${RUN_USER} venv/bin/python manage.py createsuperuser
  -------------------------------------------------------------------
EOF
fi
