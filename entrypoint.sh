#!/bin/sh
set -e

export PYTHONPATH=/app/cust_journey:$PYTHONPATH

uv run python cust_journey/manage.py migrate --noinput
uv run python cust_journey/manage.py collectstatic --noinput

exec uv run gunicorn cust_journey.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --access-logfile - \
    --error-logfile -
