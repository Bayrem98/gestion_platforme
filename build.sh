#!/usr/bin/env bash
# Sortie en cas d'erreur
set -o errexit

# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances système nécessaires pour Pillow
apt-get update && apt-get install -y \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev

# Installer les dépendances Python
pip install -r requirements.txt

# Collecter les fichiers statiques
python manage.py collectstatic --no-input

# Appliquer les migrations
python manage.py migrate