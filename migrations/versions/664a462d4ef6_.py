"""empty message

Revision ID: 664a462d4ef6
Revises:
Create Date: 2022-01-20 10:25:23.564605

"""
from typing import Optional

import sqlalchemy as sa
from alembic import op

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


# revision identifiers, used by Alembic.
revision = "664a462d4ef6"
down_revision: Optional[str] = None
branch_labels: Optional[str] = None
depends_on: Optional[str] = None


def upgrade():
    with app.app_context():
        print(f"Initializing DB at {app.config['SQLALCHEMY_DATABASE_URI']}")
        db.create_all()

        if app.config["ENV"] == "development":
            for term_name, term in TERMS.items():
                myterm = Term(name=term_name)
                db.session.add(myterm)
                mydefs = [
                    Definition(term_name=term_name, **def_obj)
                    for def_obj in term["definitions"]
                ]
                myterm.definitions = mydefs
                db.session.add(myterm)
                for def_instance in mydefs:
                    db.session.add(def_instance)

        db.session.commit()


def downgrade():
    print(f"Removing DB at {app.config['SQLALCHEMY_DATABASE_URI']}")
    response = input("Are you sure? [y/N]")
    if response == "y":
        db.drop_all()
    else:
        print("Aborting under user request.")
