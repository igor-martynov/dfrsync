#!/bin/sh

# clean log
echo "" > ./django_debug.log

# launch without reload - reload hangs when we use multithreading
python3 manage.py runserver --noreload 0.0.0.0:8000

