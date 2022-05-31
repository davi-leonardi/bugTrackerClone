from select import select
from flask_login import UserMixin
from . import db, create_app
from sqlalchemy.sql import func

association_table = db.Table('association_table',
    db.Column('project_id',db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('usr_id',db.Integer, db.ForeignKey('usr.id'), primary_key=True)
)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.String(150), nullable=False)
    priority = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(150), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    owner = db.Column(db.Integer, db.ForeignKey('usr.id'))
    messages = db.relationship('Chat')

class Usr(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    projects = db.relationship('Project', secondary=association_table, lazy='subquery', backref=db.backref('usrs', lazy=True))
    tickets = db.relationship('Ticket')
    messages = db.relationship('Chat')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.String(1000))
    creation_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    status = db.Column(db.Boolean, nullable=False)
    tickets = db.relationship('Ticket')
    messages = db.relationship('Chat')
    owner = db.Column(db.Integer, db.ForeignKey('usr.id'))

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ownerName = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(100), nullable=False)
    post_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    owner = db.Column(db.Integer, db.ForeignKey('usr.id'))


