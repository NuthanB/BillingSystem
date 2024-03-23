from flask import render_template, request, redirect, session, url_for
from app import app, db
from app.models import User, Item

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

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        group = request.form['group']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        user_id = session.get('user_id')  # Assuming user is logged in and session contains user ID
        if user_id:
            item = Item(name=name, group=group, quantity=quantity, price=price, user_id=user_id)
            db.session.add(item)
            db.session.commit()
            return redirect(url_for('index'))  # Redirect to home page after adding item
        else:
            return redirect(url_for('login'))  # Redirect to login page if user is not logged in
    return render_template('add_item.html')
