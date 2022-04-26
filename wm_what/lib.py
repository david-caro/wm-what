#!/usr/bin/env python3
from typing import Any, Dict, Optional

from wm_what.models import Definition, DefinitionSchema, Term, TermSchema, db


class NotFoundError(Exception):
    pass


class UnauthorizedError(Exception):
    pass


def get_terms(name_filter: Optional[str] = None, limit: Optional[int] = None) -> Optional[Dict[str, Any]]:
    if name_filter is None:
        query = db.session.query(Term)
    else:
        query = db.session.query(Term).filter(Term.name.like(f"%{name_filter}%"))

    if limit:
        query = query.limit(limit)

    term_schema = TermSchema(many=True)
    return term_schema.dump(query.all())


def get_term(name: str) -> Dict[str, Any]:
    term = db.session.query(Term).filter_by(name=name).one_or_none()
    if not term:
        raise NotFoundError(f"Unable to find a term with name {name}.")

    term_schema = TermSchema(many=False)
    return term_schema.dump(term)


def get_definition(id: int) -> Dict[str, Any]:
    definition = db.session.query(Definition).filter_by(id=id).one_or_none()
    if not definition:
        raise NotFoundError(f"Unable to find a definition with id {id}.")

    definition_schema = DefinitionSchema()
    return definition_schema.dump(definition)


def set_definition(id: int, term_name: str, author: str, content: str) -> Dict[str, Any]:
    definition = db.session.query(Definition).filter_by(id=id).one_or_none()
    if not definition:
        raise NotFoundError(f"Unable to find a definition with id {id}.")

    if not db.session.query(Term).filter_by(name=term_name).one_or_none():
        raise NotFoundError(f"Unable to find a term with name {term_name}.")

    definition.author = author
    definition.content = content
    definition.term_name = term_name
    db.session.add(definition)
    db.session.commit()
    definition = db.session.query(Definition).filter_by(id=id).one()
    definition_schema = DefinitionSchema()
    return definition_schema.dump(definition)


def delete_definition(id: int) -> None:
    definition = db.session.query(Definition).filter_by(id=id).one_or_none()
    if not definition:
        raise NotFoundError(f"Unable to find a definition with id {id}.")

    db.session.delete(definition)
    db.session.commit()


def add_term(term_name: str) -> Optional[Dict[str, Any]]:
    new_term = Term(name=term_name)
    db.session.add(new_term)
    return get_term(name=term_name)


def update_definition_for_term(
    term_name: str, definition_id: int, author: str, content: str
) -> Optional[Dict[str, Any]]:
    if not db.session.query(Term).filter_by(name=term_name).one_or_none():
        raise NotFoundError(f"Unable to find a term with name {term_name}.")

    current_definition = db.session.query(Definition).filter_by(id=definition_id).one_or_none()
    if not current_definition:
        raise NotFoundError(f"Unable to find a a definiton with id {definition_id}.")

    if current_definition.author != author:
        raise UnauthorizedError(f"Author {author} is not the author of the definition {definition_id}.")

    if current_definition.term_name != term_name:
        raise UnauthorizedError(
            f"Term {term_name} is not the term of the definition {definition_id} ({current_definition.term_name})."
        )

    current_definition.content = content
    db.session.add(current_definition)
    # needed to generate the id
    db.session.commit()
    return get_definition(id=current_definition.id)


def add_definition_to_term(term_name: str, author: str, content: str) -> Optional[Dict[str, Any]]:
    if not db.session.query(Term).filter_by(name=term_name).one_or_none():
        raise NotFoundError(f"Unable to find a term with name {term_name}.")

    new_definition = Definition(term_name=term_name, author=author, content=content)
    db.session.add(new_definition)
    # needed to generate the id
    db.session.commit()
    return get_definition(id=new_definition.id)
