#!/bin/bash -e

FLASK_ENV=development python wm_what/app.py "$@"
