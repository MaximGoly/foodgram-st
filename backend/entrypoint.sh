#!/bin/bash

echo "Waiting for database..."
sleep 10

python foodgram/manage.py makemigrations users
python foodgram/manage.py makemigrations recipes
python foodgram/manage.py migrate

# Prepare fonts for PDF generation
python foodgram/prepare_fonts.py

python foodgram/manage.py collectstatic --noinput

echo "Создание суперпользователя"
python foodgram/manage.py createsuperuser --noinput --username "admin" --email "admin@example.com" --first_name "admin" --last_name "admin"


if [ -f "data/ingredients.json" ]; then
    python foodgram/manage.py import_ingredients data/ingredients.json
fi

cd foodgram
gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000