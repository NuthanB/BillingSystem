from flask import render_template, request, redirect, session, url_for
from app import app, db
from app.models import User, Item,Bill, BillItem

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
            # Authentication successful, store user ID in session
            session['user_id'] = user.id
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

@app.route('/items')
def items():
    items = Item.query.all()
    return render_template('items.html', items=items)

@app.route('/edit_item/<int:item_id>', methods=['GET'])
def edit_item(item_id):
    item = Item.query.get(item_id)
    if item:
        return render_template('edit_item.html', item=item)
    else:
        # Item not found, handle appropriately (e.g., redirect to items page)
        return redirect(url_for('items'))

@app.route('/update_item', methods=['POST'])
def update_item():
    item_id = request.form['id']
    name = request.form['name']
    group = request.form['group']
    price = float(request.form['price'])
    item = Item.query.get(item_id)
    if item:
        item.name = name
        item.group = group
        item.price = price
        db.session.commit()
    return redirect(url_for('items'))

@app.route('/create_bill', methods=['POST'])
def create_bill():
    # Extract bill details from the request
    bill_number = request.form['bill_number']
    user = request.form['user']
    total = float(request.form['total'])
    # Add bill to the database
    bill = Bill(bill_number=bill_number, user=user, total=total)
    db.session.add(bill)
    db.session.commit()
    return redirect(url_for('view_bill', bill_id=bill.id))

@app.route('/view_bill/<int:bill_id>')
def view_bill(bill_id):
    bill = Bill.query.get(bill_id)
    return render_template('bill.html', bill=bill)

@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    item = BillItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('view_bill', bill_id=item.bill_id))