from app import app
from flaskwebgui import FlaskUI

FlaskUI(app=app, server="flask", fullscreen=True).run()
# app.run(debug=True)
