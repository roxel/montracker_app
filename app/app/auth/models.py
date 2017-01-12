from sqlalchemy import String, Integer
from ..database import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(Integer, primary_key=True, autoincrement=True)

    # columns
    login = db.Column(String(64), nullable=False, unique=True)
    password = db.Column(String(64), nullable=False)

    # relationships
    actions = db.relationship('Action', backref='user',
                              lazy='dynamic')

    @staticmethod
    def from_form_data(form):
        return User(login=form.login.data, password=form.password.data)

