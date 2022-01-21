#!/usr/bin/env python3

from setuptools import find_packages, setup  # type: ignore

URL = "http://github.com/david-caro/wm-what"
BUGTRACKER_URL = "http://github.com/david-caro/wm-what/issues"


if __name__ == "__main__":
    setup(
        author="David Caro",
        author_email="me@dcaro.es",
        description="Wikimedia jargon helper",
        setup_requires=["autosemver"],
        install_requires=[
            "apispec",
            "apispec-webframeworks",
            "autosemver",
            "flasgger",
            "flask",
            "flask-alembic",
            "flask-login",
            "flask-markdown",
            "flask-marshmallow",
            "flask-migrate",
            "flask-restful",
            "flask-script",
            "flask-sqlalchemy",
            "marshmallow-sqlalchemy",
            "requests",
            "social-auth-app-flask",
            "social-auth-app-flask-sqlalchemy",
            "werkzeug",
        ],
        extras_require={
            "test": [
                "black",
                "flake8",
                "isort",
                "mypy",
                "types-flask",
                "types-pyyaml",
                "types-requests",
            ]
        },
        license="GPLv3",
        name="wm_what",
        package_data={"": ["CHANGELOG", "AUTHORS"]},
        packages=find_packages(),
        url=URL,
        autosemver={
            "bugtracker_url": BUGTRACKER_URL,
        },
    )
