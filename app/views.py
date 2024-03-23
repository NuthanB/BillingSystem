from flask import render_template, request, redirect, url_for
from app import app, db
from app.models import User

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            # Authentication successful, redirect to home page or dashboard
            return redirect(url_for('index'))
        else:
            # Authentication failed, redirect back to login page with an error message
            return render_template('login.html', error='Invalid email or password.')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        # Redirect to login page after successful signup
        return redirect(url_for('login'))
    return render_template('signup.html')
