#!/usr/bin/env python
import os
import sys
import django  # added for v1.7

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "derbysite.settings")
    # os.environ['DJANGO_SETTINGS_MODULE'] = 'derbysite.settings' # This might be more appropriate, but haven't tested yet (added Jan2014 while trying to get this to work with Django 1.7)

    django.setup()  # added for v1.7

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
