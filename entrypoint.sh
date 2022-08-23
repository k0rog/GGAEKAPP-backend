#!/bin/bash

python manage.py migrate --no-input

python manage.py create_groups
python manage.py create_headmaster

exec daphne config.asgi:application --port $PORT --bind 0.0.0.0 -v2