#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input


mkdir -p /var/data/media/comprobantes

chmod -R 777 /var/data
