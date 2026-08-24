#!/usr/bin/env bash
set -e

cd frontend
npm install
npm run build

cd ../backend
pip install -r requirements.txt
pip install --force-reinstall "djangorestframework>=3.15"
python manage.py migrate --noinput
python manage.py sync_organizations
python manage.py collectstatic --noinput
