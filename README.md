# wm-what

# Setup development enviroment

You can do this however you prefer, this is my personal process.

Install [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/), for example for fedora:

> sudo apt install python3-virtualenvwrapper

Make sure that it's applied to your bash session (for example start a new shell session, or source the `/etc/profile.d/virtualenvwrapper.sh` file that the package above installed).

Create a new venv for the project:

> mkvirtualenv wm_what

Activate it

> workon wm_what

Install the current package with the test extra dependencies:

> pip install -e `.[test]`

# Running locally

There's a wrapper script to run wm-what on your local machine in development mode, will create the DB if it does not exist and upgrade it if it does.

> utils/start_dev.sh

# DB management

For database upgrade management wm-what uses alembic, through the flask-migrate extension, some common actions are:

## Create a new migration

> FLASK_ENV=development flask db migrate --autogenerate

Then you'll have to edit the newly created python file under `$GIT_REPO/migrations/versions` and make sure it does what you want.

## Check what migrations you have applied

> FLASK_ENV=development flask db current.

## Apply any new migrations

> FLASK_ENV=development flask db upgrade.

## Downgrade to a specific migration

> FLASK_ENV=development flask db downgrade 664a462d4ef6

Where `664a462d4ef6` is the revision you want to downgrade to.

## Move to a specific migration without actually applying the migrations

This is useful if you have already applied the changes, and just want to reflect that in the alembic registry.

> FLASK_ENV=development flask db stamp 664a462d4ef6

Where `664a462d4ef6` is the revision you want to stamp to.
