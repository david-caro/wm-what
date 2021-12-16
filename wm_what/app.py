#!/usr/bin/env python3
"""
Entry point file for the application.
"""
import os
import random
import string
from logging.config import dictConfig
from pathlib import Path
from urllib.parse import quote_plus

import flask
import flask_login
import requests
import yaml
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flasgger import APISpec, Swagger  # type: ignore
from flask import Flask, render_template  # type: ignore
from flask_login import LoginManager, current_user, login_manager
from flask_login.utils import login_required, login_user

from wm_what import lib
from wm_what.api import apiv1
from wm_what.models import DefinitionSchema, TermSchema, User, db, ma
from wm_what.utils import logged_in

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": ("[%(asctime)s] %(levelname)s in %(module)s: %(message)s"),
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["wsgi"]},
    }
)


THIS_FILE_FOLDER = Path(__file__).resolve().absolute().parent
REPO_FOLDER = THIS_FILE_FOLDER.parent

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.register_blueprint(apiv1, url_prefix="/api/v1")

spec = APISpec(
    title="Wikimedia What api",
    version="0.0.1",
    openapi_version="2.0",
    plugins=[
        FlaskPlugin(),
        MarshmallowPlugin(),
    ],
)
template = spec.to_flasgger(app, definitions=[DefinitionSchema, TermSchema])
swagger = Swagger(app, template=template)


if app.config["ENV"] == "production":
    config_file = "prod-config.yaml"

elif app.config["ENV"] == "development":
    config_file = "dev-config.yaml"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////" + str(REPO_FOLDER / "dev.db")
    app.config["SECRET_KEY"] = "".join(random.choice(string.ascii_letters) for _ in range(32))


app.config.update(yaml.safe_load((REPO_FOLDER / config_file).open()))
app.secret_key = app.config["SECRET_KEY"]
db.init_app(app)
ma.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User(username=user_id)


@app.route("/")
def splash():
    example_terms = lib.get_terms(limit=25)
    return render_template("splash.html", example_terms=example_terms, user=current_user.get_id())


@app.route("/search")
def search():
    term_name = flask.request.args.get("term_name")
    terms = lib.get_terms(name_filter=term_name)
    if not terms:
        example_terms = lib.get_terms(limit=25)
    else:
        example_terms = None

    if len(terms) == 1:
        return flask.redirect(flask.url_for("get_term", term_name=term_name))

    return render_template(
        "search_results.html",
        terms=terms,
        search_value=term_name or "",
        example_terms=example_terms,
        user=current_user.get_id(),
        exact_match=any(term["name"] == term_name for term in terms),
    )


@app.route("/term/<term_name>")
def get_term(term_name):
    term = lib.get_term(name=term_name)
    if not term:
        return (f"Term with name '{term_name}' not found.", 404)

    has_definition = any(definition["author"] == flask.session.get("username") for definition in term["definitions"])
    return render_template("term.html", term=term, has_definition=has_definition, user=current_user.get_id())


@app.route("/login")
def login():
    """Initiate an OAuth login.

    Call the MediaWiki server to get request secrets and then redirect the
    user to the MediaWiki server to sign the request.
    """
    if app.config["ENV"] == "development" and not app.config.get("FORCE_OAUTH_LOGIN"):
        return flask.redirect(flask.url_for("oauth_callback"))

    base_url = app.config["WIKIMEDIA_OAUTH2_URL"]
    authorization_url = base_url + "/oauth2/authorize"
    state = "".join(random.choice(string.ascii_letters) for _ in range(16))

    params = {
        "response_type": "code",
        "client_id": app.config["WIKIMEDIA_OAUTH2_TOKEN"],
        "redirect_uri": flask.url_for("oauth_callback", _external=True),
        "state": state,
    }
    flask.session["oauth2_state"] = state

    params_str = "&".join(f"{name}={quote_plus(value)}" for name, value in params.items())
    final_url = authorization_url + "?" + params_str
    print(final_url)

    return flask.redirect(final_url)


@app.route("/oauth_callback")
def oauth_callback():
    """OAuth handshake callback."""
    if app.config["ENV"] == "development" and not app.config.get("FORCE_OAUTH_LOGIN"):
        flask.session["username"] = "devuser"
        return flask.redirect(flask.url_for("splash"))

    if flask.session.get("oauth2_state") != flask.request.args.get("state"):
        return ("Invalid state received in oauth2 callback", 401)

    code = flask.request.args.get("code")
    if not code:
        flask.flash("OAuth callback failed. No code received.")
        return flask.redirect(flask.url_for("splash"))

    base_url = app.config["WIKIMEDIA_OAUTH2_URL"]

    params = {
        "grant_type": "authorization_code",
        "client_id": app.config["WIKIMEDIA_OAUTH2_TOKEN"],
        "client_secret": app.config["WIKIMEDIA_OAUTH2_SECRET"],
        "redirect_uri": flask.url_for("oauth_callback", _external=True),
        "code": code,
    }
    # the server does not like the redirect_uri in %-encoded format
    params_str = "&".join(f"{name}={value}" for name, value in params.items())
    # params_str = "&".join(f"{name}={quote_plus(value)}" for name, value in params.items())
    access_token_url = base_url + "/oauth2/access_token"

    try:
        token_response = requests.post(
            url=access_token_url, data=params_str, headers={"Content-type": "application/x-www-form-urlencoded"}
        )
        token_response.raise_for_status()
    except Exception as error:
        app.logger.exception(f"OAuth token request failed: {error}")
        raise

    flask.session["access_token"] = token_response.json()["access_token"]
    flask.session["refresh_token"] = token_response.json()["refresh_token"]

    identity_url = base_url + "/oauth2/resource/profile"
    try:
        identity_response = requests.get(
            url=identity_url, headers={"Authorization": f"Bearer {flask.session['access_token']}"}
        )
        identity_response.raise_for_status()
    except Exception as error:
        app.logger.exception(f"OAuth identity request failed: {error}")
        raise

    if identity_response.json()["blocked"]:
        app.logger.exception("User is blocked")
        return (f"Unauthorized, your user is blocked in wikimedia.", 401)

    flask.session["username"] = identity_response.json()["username"]
    app.logger.info(f"OAuth identity confirmed: {flask.session['username']}")
    login_user(User(username=flask.session["username"]))
    return flask.redirect(flask.url_for("splash"))


@app.route("/logout")
def logout():
    """Log the user out by clearing their session."""
    flask_login.logout_user()
    flask.session.clear()
    return flask.redirect(flask.url_for("splash"))


@app.route("/definition/<definition_id>", methods=["POST"])
@login_required
def update_definition(definition_id: int):
    term_name = flask.request.form.get("term_name")
    content = flask.request.form.get("content")
    if not term_name:
        return ("Bad request, missing term_name in post payload", 403)

    if not content:
        return ("Bad request, missing content in post payload", 403)

    try:
        lib.update_definition_for_term(
            term_name=term_name,
            definition_id=definition_id,
            content=content,
            author=current_user.username,
        )

    except lib.NotFound as error:
        return (f"{error}", 404)

    except lib.Unauthorized as error:
        return (f"{error}", 401)

    return flask.redirect(flask.url_for("get_term", term_name=term_name))


@app.route("/term", methods=["POST"])
@login_required
def create_term():
    term_name = flask.request.form.get("term_name")
    content = flask.request.form.get("content")
    if not term_name:
        return ("Bad request, missing term_name in post payload", 403)
    if not content:
        return ("Bad request, missing content in post payload", 403)
    try:
        lib.add_term(term_name=term_name)
        lib.add_definition_to_term(
            term_name=term_name,
            content=content,
            author=current_user.username,
        )
    except lib.NotFound as error:
        return (f"{error}", 404)

    return flask.redirect(flask.url_for("get_term", term_name=term_name))


@app.route("/definition", methods=["POST"])
@login_required
def create_definition():
    term_name = flask.request.form.get("term_name")
    content = flask.request.form.get("content")
    if not term_name:
        return ("Bad request, missing term_name in post payload", 403)
    if not content:
        return ("Bad request, missing content in post payload", 403)
    try:
        lib.add_definition_to_term(
            term_name=term_name,
            content=content,
            author=current_user.username,
        )
    except lib.NotFound as error:
        return (f"{error}", 404)

    return flask.redirect(flask.url_for("get_term", term_name=term_name))


@app.route("/definition", methods=["DELETE"])
@login_required
def delete_definition():
    def_id = flask.request.args.get("id")
    if not def_id:
        return ("Bad request, missing id in payload", 403)

    try:
        definition = lib.get_definition(id=def_id)
    except lib.NotFound as error:
        return (f"{error}", 404)

    if definition.author != current_user.username:
        return (f"Unauthorized, you are not the user that created this definition.", 401)

    lib.delete_definition(id=def_id)
    return ("Definition deleted", 200)


@app.route("/favicon.ico")
def favicon():
    return flask.send_from_directory(
        os.path.join(app.root_path, "static"), "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )


if __name__ == "__main__":
    with app.app_context():
        app.run(port=5000)
