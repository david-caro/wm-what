from flask_login.mixins import UserMixin
from flask_marshmallow import Marshmallow  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from marshmallow import fields

db = SQLAlchemy()
ma = Marshmallow()


class Definition(db.Model):
    __tablename__ = "definition"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(80), unique=False, nullable=False)
    content = db.Column(db.String(256), unique=False, nullable=False)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    updated = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    term_name = db.Column(db.String(80), db.ForeignKey("term.name"))
    term = db.relationship("Term", back_populates="definitions")


class Term(db.Model):
    __tablename__ = "term"
    name = db.Column(db.String(80), primary_key=True)
    definitions = db.relationship("Definition", back_populates="term")


# We don't need to persist this, comes from oauth
class User(UserMixin):
    def __init__(self, username: str):
        self.username = username

    def get_id(self) -> str:
        return self.username


class DefinitionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Definition
        include_fk = True


class TermSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Term
        include_fk = True

    definitions = fields.List(fields.Nested(DefinitionSchema, exclude=["term_name"]))
