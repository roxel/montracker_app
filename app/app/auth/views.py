from app.helpers import validation_failed
from flask import Blueprint, request
from flask_restful import Api, Resource, fields, marshal_with, abort
from ..database import db
from .models import User
from .schemas import UserSchema

auth = Blueprint('auth', __name__)
auth_api = Api(auth, prefix='/auth/api/v1')


user_fields = {
    "id": fields.Integer,
    "login": fields.String,
}


@auth_api.resource('/users', endpoint='users')
class UserListApi(Resource):

    @marshal_with(user_fields)
    def get(self):
        return User.query.all()

    @marshal_with(user_fields)
    def post(self):
        """
        Returns created action item with its shortened analysis data items.
        """
        user_data, errors = UserSchema().load(request.get_json())
        if errors:
            validation_failed(errors)
        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        return user, 201


@auth_api.resource('/users/<int:user_id>')
class UserApi(Resource):

    @marshal_with(user_fields)
    def get(self, user_id):
        return User.query.get(user_id)
