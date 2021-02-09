from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_login import UserMixin
from ozon import db
import datetime


class Orders(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    created_at_date = db.Column(db.String(80))
    created_at_time = db.Column(db.String(80))
    shipment_date = db.Column(db.String(80))
    order_number = db.Column(db.String(80))
    posting_number = db.Column(db.String(80))
    offer_id = db.Column(db.String(80))
    name = db.Column(db.String(80))
    quantity = db.Column(db.Integer)
    price = db.Column(db.String(80))
    status = db.Column(db.String(80))
    time_of_wait = db.Column(db.DateTime, default=datetime.datetime.now)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return f"<users {self.id, self.username}>"
        pass


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)


class LoginForm(FlaskForm):
    login = StringField("Введите логин")
    password = PasswordField(validators=[DataRequired()])
    submit = SubmitField('Submit')


class UserLogin():
    def fromDB(self, user_id, db):
        self.__user = db.getUser(user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.__user['id'])

