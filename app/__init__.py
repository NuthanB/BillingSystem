from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.helpers import is_user_logged_in

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = '12345'

with app.app_context():
    db.create_all()
