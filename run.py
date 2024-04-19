from app import app, db
from flaskwebgui import FlaskUI

FlaskUI(app=app, server="flask", fullscreen=True).run()