from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.helpers import is_user_logged_in

from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
db = SQLAlchemy(app)
app.secret_key = '12345'
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()
