from flask import Flask, render_template, flash, redirect, url_for, session,\
     logging, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update
from wtforms import Form, StringField, PasswordField, validators
from wtforms.fields.core import FormField, IntegerField
from wtforms.validators import Regexp
from flask_mysqldb import MySQL
from datetime import datetime
from flask_marshmallow import Marshmallow
from functools import wraps
from email.mime.multipart import MIMEBase
import smtplib

app = Flask(__name__)
mysql = MySQL(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://qwallity:mysqlpass@qwallitydb.cywlir8bfmdo.eu-central-1.rds.amazonaws.com:3306/qwallity_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)


# Create Users table in DB
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(300), nullable=False)
    username = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role_id = db.Column(db.Integer)
    account = db.Column(db.Integer)

    def __repr__(self):
        return '<Users %r>'%self.id


# Create Courses table in DB
class Courses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.String(300), nullable=False)
    author = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now())
    coursetype = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float)

    def __repr__(self):
        return '<Courses %r>'%self.id

# Create Codes table in DB
class Codes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), nullable=False)
    gen_code = db.Column(db.Integer)
    is_used = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        return '<Codes %r>'%self.id

# Create User_Courses Table
class UserCourses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer)

    def __repr__(self):
        return '<User_Courses %r>'%self.id

class RegisterForm(Form):

    name = StringField('Name', [validators.Length(min=1, max=25)])  
    username = StringField('Username', [validators. Length(min=4, max=50), Regexp(r'^[A-Za-z]',message='Username should start with letters.')])
    email = StringField('Email', [validators.Length(min=6, max=50), Regexp(r"^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$",message='Email format is not valid.')])
    password = PasswordField('Password', [validators.DataRequired(), validators.Length(min=8,max=14)])
    confirm = PasswordField('Confirm Password',  [validators.EqualTo('password', message='Password do not match!')])


class Forgot(Form):
    email = StringField('Email', [validators.Length(min=6, max=50), Regexp(r"^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$",message='Email format is not valid.')])


class Reset(Form):
    new_password = PasswordField('Password', [validators.DataRequired(), validators.Length(min=8,max=14)])
    code = StringField('Code', [validators. Length(7)])


class Calculator(Form):
    number1 = StringField('number1', [validators.Length(max=10), Regexp(r'^[-+]?\d*$', message='Field should accept only numbers')])
    number2 = StringField('number2', [validators.Length(max=10), Regexp(r'^[-+]?\d*$', message='Field should accept only numbers')])


class Blackbox(Form):
    name = StringField('name', [validators.Length(min=3, max=10), Regexp(r'[A-Za-z]', message='Only letters')])
    address = StringField('address', [validators.Length(max=50), Regexp(r'[A-Za-z0-9]', message='Address should be Alphanumeric')])
    phone = StringField('phone', [validators.Length(min=8, max=10), Regexp(r'^[1-9]*$', message='Phone Number should be only numbers')]) 


class Account(Form):
    account_balance = StringField('Account')
    amount = StringField('Amount', [validators.DataRequired(), validators.Length(min=1, max=10), Regexp(r'^[0-9]*$', message='Amount shoud be numbers only')])


class Admin(Form):
    username = StringField('username')
    role = StringField('Role')
