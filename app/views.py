from flask import render_template, request, redirect, session, url_for
from app import app, db
from app.models import User, Item,Bill, BillItem
from flask import jsonify,request


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')



@app.route('/get_suggestions')
def get_suggestions():
    keyword = request.args.get('keyword')
    if keyword:  # Check if keyword is not empty
        # Query the Item table to get suggestions based on the keyword
        suggestions = Item.query.filter(Item.name.ilike(f'%{keyword}%')).limit(10).all()
        # Extract names from suggestions
        suggestion_names = [item.name for item in suggestions]
        # Return suggestion names as JSON response
        return jsonify(suggestion_names)
    else:
        # Return an empty list if keyword is empty
        return jsonify([])


@app.route('/add_item_to_bill', methods=['POST'])
def add_item_to_bill():
    # Get item details from the request
    item_name = request.json['item_name']
    quantity = request.json['quantity']
    price = request.json['price']
    
    # Perform any necessary validation or processing
    
    # Add the item to the bill table
    # For example, you might create a new entry in the BillItem table
    new_item = BillItem(item_name=item_name, quantity=quantity, price=price)
    db.session.add(new_item)
    db.session.commit()
    
    # Return a response indicating success
    return jsonify({'message': 'Item added to bill successfully'}), 200

@app.route('/create_bill', methods=['POST'])
def create_bill():
    # Extract bill details from the request
    bill_number = request.form['bill_number']
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        bill = Bill(bill_number=bill_number, user=user)
        db.session.add(bill)
        db.session.commit()

        # Extract item details from the form and add them to the bill
        item_name = request.form['item_name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        bill_item = BillItem(item_name=item_name, quantity=quantity, price=price, bill=bill)
        db.session.add(bill_item)
        db.session.commit()

        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    item = BillItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('index'))

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

@app.route('/get_item_price')
def get_item_price():
    item_name = request.args.get('item_name')
    # Query the database to retrieve the price for the selected item
    item = Item.query.filter_by(name=item_name).first()
    if item:
        return jsonify({'price': item.price})
    else:
        return jsonify({'error': 'Item not found'})
