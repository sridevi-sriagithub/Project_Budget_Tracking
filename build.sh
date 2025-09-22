#!/usr/bin/env bash
set -o errexit   # exit on error

# install dependencies
pip install -r requirements.txt

# collect static files for WhiteNoise
python manage.py collectstatic --no-input

# run migrations
python manage.py migrate --no-input
