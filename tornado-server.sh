#!/bin/sh
export PYTHONPATH=.
python manage.py collectstatic --noinput
python tornado/tornado-main.py
