from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.helpers import is_user_logged_in

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
db = SQLAlchemy(app)
app.secret_key = '12345'

from app import views, models
with app.app_context():
    db.create_all()
