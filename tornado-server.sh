#!/bin/sh
cd $(dirname $(realpath -s $0))
export PYTHONPATH=.
python manage.py collectstatic --noinput
python tornado/tornado-main.py
