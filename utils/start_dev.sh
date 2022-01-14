#!/bin/bash -e

[[ -e dev.db ]] || FLASK_ENV=development python utils/setup_db.py

FLASK_ENV=development python wm_what/app.py "$@"
