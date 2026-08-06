#!/usr/bin/env bash
set -e

cd frontend
npm install
npm run build

cd ../backend
pip install --no-cache-dir --upgrade -r requirements.txt
pip install --no-cache-dir --force-reinstall "djangorestframework>=3.15"
python manage.py migrate --noinput
python manage.py sync_organizations
python manage.py collectstatic --noinput
