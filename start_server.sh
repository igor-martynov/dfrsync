#!/bin/sh

# clean log
echo "" > ./django_debug.log

python3 manage.py runserver --noreload
