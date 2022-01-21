from flask import Blueprint, request
from flask_login.utils import login_required

from wm_what import lib

apiv1 = Blueprint(name="apiv1", import_name=__name__)


@apiv1.route("/terms")
def get_terms():
    """Retrieve all the existing terms.
    ---
    parameters: []
    responses:
      200:
        description: The list of known terms
        schema:
          type: object
          properties:
            terms:
              type: array
              items:
                  type: Term
        examples:
    """
    terms = lib.get_terms()
    return {"terms": [term["name"] for term in terms]}


@apiv1.route("/terms/<term_name>")
def get_term(term_name: str):
    """Retrieve all the existing terms.
    ---
    parameters:
      - name: term_name
        in: path
        type: string
        required: true
    responses:
        200:
            description: The details of a given term
            schema:
                $ref: '#/definitions/Term'
        404:
            description: the given term was not found
            schema:
                type: string
    """
    try:
        term = lib.get_term(name=term_name)
    except lib.NotFoundError as error:
        return (f"{error}", 404)

    return term


@apiv1.route("/definition/<id>")
def get_definition(id: int):
    """Retrieve a given definition.
    ---
    parameters:
      - name: id
        in: path
        type: number
        required: true
    responses:
        200:
            description: The details of a given term
            schema:
                $ref: '#/definitions/Definition'
            examples:
    """
    try:
        definition = lib.get_definition(id=id)
    except lib.NotFoundError as error:
        return (f"{error}", 404)

    return definition


@apiv1.route("/definition/<id>", methods=["POST"])
@login_required
def update_definition(id: int):
    """Update an existing definition.
    ---
    post:
        parameters:
        - name: id
          in: path
          type: number
          required: true
        - name: term_name
          in: query
          type: string
          required: true
        - name: content
          in: query
          type: string
          required: true
    responses:
        200:
            description: The details of a given term
            schema:
                $ref: '#/definitions/Definition'
            examples:
        404:
            description: The given definition or the term_name were not found
            schema:
                type: string
    """
    try:
        definition = lib.set_definition(
            id=id,
            content=request.args["content"],
            term_name=request.args["term_name"],
            author="nobody",
        )
    except lib.NotFoundError as error:
        return (f"{error}", 404)

    return definition


@apiv1.route("/definition", methods=["POST"])
@login_required
def api_create_definition(user: str):
    """Create a new definition.
    ---
    post:
        parameters:
        - name: term_name
          in: query
          type: string
          required: true
        - name: content
          in: query
          type: string
          required: true
    responses:
        200:
            description: The details of a given term
            schema:
                $ref: '#/definitions/Definition'
        404:
            description: The given definition or the term_name were not found
            schema:
                type: string
    """
    term_name = request.form.get("term_name")
    content = request.form.get("content")
    if not term_name:
        return ("Bad request, missing term_name in post payload", 403)
    if not content:
        return ("Bad request, missing content in post payload", 403)
    try:
        definition = lib.add_definition_to_term(
            term_name=term_name,
            content=content,
            author=user,
        )
    except lib.NotFoundError as error:
        return (f"{error}", 404)

    return definition


@apiv1.route("/definition/<id>", methods=["DELETE"])
@login_required
def delete_definition(id: int, user: str):
    """Delete a definition.
    ---
    post:
        parameters:
        - name: id
          in: query
          type: number
          required: true
    responses:
        200:
            description: The definition was removed
            schema:
                $ref: '#/definitions/Definition'
        404:
            description: The given definition id was not found
            schema:
                type: string
    """
    if not id:
        return ("Bad request, missing id in payload", 403)

    try:
        definition = lib.get_definition(id=id)
    except lib.NotFoundError as error:
        return (f"{error}", 404)

    if definition["author"] != user:
        return ("Unauthorized, you are not the user that created this definition.", 401)

    lib.delete_definition(id=id)
    return ("Definition deleted", 200)
