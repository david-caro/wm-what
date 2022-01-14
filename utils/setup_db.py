#!/usr/bin/env python3
from wm_what.app import app, db
from wm_what.models import Definition, Term

# Data to initialize database with
TERMS = {
    "wmcs": {
        "definitions": [
            {
                "content": "Wikimedia Cloud Services",
                "author": "dcaro",
            }
        ],
    },
    "wm_what": {
        "definitions": [
            {
                "content": "Wikimedia WHAT? tool, for lingo disambiguation (:",
                "author": "dcaro",
            }
        ],
    },
}

with app.app_context():
    print(f"Initializing DB at {app.config['SQLALCHEMY_DATABASE_URI']}")
    db.drop_all()
    db.create_all()

    for term_name, term in TERMS.items():
        myterm = Term(name=term_name)
        db.session.add(myterm)
        mydefs = [Definition(term_name=term_name, **def_obj) for def_obj in term["definitions"]]
        myterm.definitions = mydefs
        db.session.add(myterm)
        for def_instance in mydefs:
            db.session.add(def_instance)

    db.session.commit()
