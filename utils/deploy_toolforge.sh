#!/bin/bash -e

if [[ "$1" == "in_pod" ]]; then
    source $HOME/www/python/venv/bin/activate
    pip install -e wm-what/.
else
    cd wm-what
    git fetch --all
    git reset --hard origin/main
    webservice --backend=kubernetes python3.9 shell -- bash ./deploy_toolforge.sh in_pod || true
    webservice --backend=kubernetes python3.9 restart
fi
