#!/bin/bash -e

FLASK_ENV=development flask db upgrade
FLASK_ENV=development python wm_what/app.py "$@"
