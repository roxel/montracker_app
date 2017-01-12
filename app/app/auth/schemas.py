from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    login = fields.String(required=True, validate=validate.Length(min=1, max=256))
    password = fields.String(required=True, validate=validate.Length(max=64))
