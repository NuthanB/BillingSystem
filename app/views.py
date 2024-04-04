from sqlalchemy.sql import func
from flask import render_template, request, redirect, session, url_for, jsonify
from app import app, db
from app.models import User, Item, Bill, BillItem, UserActivity
from datetime import datetime
from sqlalchemy import func
from collections import defaultdict


@app.route('/')
@app.route('/index')
def index():
    try:
        uid = session['user_id']
        items = Item.query.all()
    except KeyError:
        return render_template('login.html')
    return render_template('index.html', items=items)


@app.route('/get_suggestions')
def get_suggestions():
    keyword = request.args.get('keyword')
    if keyword:
        suggestions = Item.query.filter(
            (Item.name.ilike(f'%{keyword}%')) & (Item.quantity > 0)
        ).limit(10).all()

        suggestion_names = [item.name for item in suggestions]
        return jsonify(suggestion_names)
    else:
        return jsonify([])


@app.route('/create_bill', methods=['POST'])
def create_bill():
    bill_number = request.form['bill_number']
    user_id = session.get('user_id')

    if user_id:
        user = User.query.get(user_id)
        bill = Bill(bill_number=bill_number, user=user)
        db.session.add(bill)
        db.session.commit()

        item_name = request.form['item_name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        bill_item = BillItem(item_name=item_name,
                             quantity=quantity, price=price, bill=bill)
        db.session.add(bill_item)
        db.session.commit()

        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/submit_bill', methods=['POST'])
def submit_bill():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.json

        if data:
            items = data.get('items')
            total = data.get('total')
            new_bill = Bill(user_id=user_id, total=total)
            db.session.add(new_bill)

            for item in items:
                item_db = Item.query.filter_by(
                    name=item['name']).first()

                if item_db:
                    new_quantity = item_db.quantity - item['quantity']
                    print(new_quantity)
                    if new_quantity >= 0:
                        item_db.quantity = new_quantity
                        bill_item = BillItem(
                            bill=new_bill, item_id=item_db.id, item_name=item['name'], quantity=item['quantity'], price=item['price'])
                        db.session.add(bill_item)
                    else:
                        print("Hi")
                        db.session.rollback()
                        return jsonify({'error': f'Insufficient quantity available for {item["name"]}'}), 500
                else:
                    db.session.rollback()
                    return jsonify({'error': f'Item {item["name"]} not found'}), 500

            db.session.commit()

            return jsonify({'message': 'Bill submitted successfully'}), 200
        else:
            return jsonify({'error': 'No data received'}), 400
    else:
        return jsonify({'error': 'User not authenticated'}), 401


def get_bill(bill_id):
    bill = Bill.query.get(bill_id)
    if bill:
        bill_details = {
            'id': bill.id,
            'bill_date_time': bill.bill_date_time.strftime('%d-%m-%Y | %H:%M'),
            'total': bill.total,
            'bill_items': []  # Initialize an empty list for storing bill items
        }

        # Query related BillItems
        bill_items = BillItem.query.filter_by(bill_id=bill_id).all()

        # Populate the 'items' list in bill_details with data from BillItems
        for item in bill_items:
            bill_details['bill_items'].append({
                'item_name': item.item_name,
                'quantity': item.quantity,
                'price': item.price
                # Add more item details here as needed
            })

        return bill_details

    else:
        return jsonify({'error': 'Bill not found'}), 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            activity = UserActivity(
                user_id=user.id, activity_performed="Logged in")
            db.session.add(activity)
            db.session.commit()

            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid email or password.')
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        uname = request.form['uname']
        email = request.form['email']
        pwd = request.form['pwd']
        re_pwd = request.form['rpwd']

        existing_user_email = User.query.filter_by(email=email).first()
        existing_user_uname = User.query.filter_by(username=uname).first()
        if existing_user_email or existing_user_uname or pwd != re_pwd:
            return redirect(url_for('signup'))

        user = User(username=uname, email=email, password=pwd)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        group = request.form['group']
        code = request.form['code']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])

        user_id = session.get('user_id')
        if user_id:
            item = Item(name=name, group=group, code=code, quantity=quantity,
                        price=price, user_id=user_id)
            activity = UserActivity(user_id=session['user_id'],
                                    activity_performed=f"Added item {name}, quantity {quantity}, price {price}")
            db.session.add(item)
            db.session.add(activity)
            db.session.commit()

            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))
    return render_template('add_item.html')


@app.route('/items')
def items():
    items = Item.query.all()
    return render_template('items.html', items=items)


@app.route('/update-stock', methods=['GET', 'POST'])
def update_item_stock():
    if request.method == 'GET':
        items = Item.query.all()
        return render_template('stock_update.html', items=items)
    else:
        item_id = request.form.get('item-id')
        stock_update = int(request.form.get('add-stock'))

        item = Item.query.get(item_id)
        item.quantity += stock_update
        activity = UserActivity(user_id=session['user_id'],
                                activity_performed=f"Updated stock of {item.name} to {item.quantity}")
        db.session.add(activity)
        db.session.commit()

        return redirect(url_for('items'))


@app.route("/get_item_name/<code>")
def get_item_name(code):
    try:
        item_name = Item.query.filter_by(code=code).first().name
        if item_name:
            return jsonify({'name': item_name}), 200
    except:
        return jsonify({'error': 'Item not found'}), 404
    

@app.route("/get_item_code/<name>")
def get_item_code(name):
    try:
        item_code = Item.query.filter_by(name=name).first().code
        if item_code:
            return jsonify({'code': item_code}), 200
    except:
        return jsonify({'error': 'Item not found'}), 404


@app.route('/edit_item/<int:item_id>')
def edit_item(item_id):
    item = Item.query.get(item_id)
    if item:
        return render_template('edit_item.html', item=item)
    else:
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
        activity = UserActivity(user_id=session['user_id'],
                                activity_performed=f"Edited item {name}, {group}, {price}")
        db.session.add(activity)
        db.session.commit()
    return redirect(url_for('items'))


@app.route('/get_item_price')
def get_item_price():
    code = request.args.get('item_code')
    item = Item.query.filter_by(code=code).first()
    if item:
        return jsonify({'price': item.price})
    else:
        return jsonify({'error': 'Item not found'})


@app.route('/check_match')
def check_match():
    item1Name = request.args.get('item1')
    item2Code = request.args.get('item2')

    try:
        item2Name = Item.query.filter_by(code=item2Code).first()
        if item1Name.lower() == item2Name.lower():
            return jsonify({'match': 'Y'})
    except:
        return jsonify({'error': 'Item not found'})


@app.route('/filter-bills', methods=['GET', 'POST'])
def filter_bills():
    if request.method == 'POST':
        from_date = request.form['from_date']
        to_date = request.form['to_date']

        print(from_date, to_date)

        filtered_bills = Bill.query.filter(
            func.date(Bill.bill_date_time) >= from_date,
            func.date(Bill.bill_date_time) <= to_date
        ).all()

        print(filtered_bills)

        return render_template("filtered_bills.html",
                               bills=filtered_bills,
                               from_date=from_date,
                               to_date=to_date
                               )
    else:
        return redirect("/report")


@app.route('/report')
def show_reports():
    bill = Bill.query.all()
    bill_items = BillItem.query.all()
    return render_template('report.html', bills=bill, bill_items=bill_items)


@app.route('/delete-item', methods=['GET', 'POST'])
def delete_item():
    if request.method == 'GET':
        item_id = request.args.get('item_id')

        if item_id:
            item = Item.query.get(item_id)
            if item:
                db.session.delete(item)
                db.session.commit()
                return jsonify({'message': 'Item deleted successfully'}), 200
            else:
                return jsonify({'error': 'Item not found'}), 404
        else:
            return jsonify({'error': 'Missing item_id parameter'}), 400
    else:
        return jsonify({'error': 'Method not allowed'}), 405


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Clear session data
    return redirect(url_for('login'))


@app.route('/bill-details/<int:bill_id>')
def get_bill_details(bill_id):
    bill = Bill.query.get(bill_id)
    if bill:
        bill_details = {
            'id': bill.id,
            'bill_date_time': bill.bill_date_time.strftime('%d-%m-%Y | %H:%M'),
            'total': bill.total,
            'items': []  # Initialize an empty list for storing bill items
        }

        # Query related BillItems
        bill_items = BillItem.query.filter_by(bill_id=bill_id).all()

        # Populate the 'items' list in bill_details with data from BillItems
        for item in bill_items:
            bill_details['items'].append({
                'item_name': item.item_name,
                'quantity': item.quantity,
                'price': item.price
                # Add more item details here as needed
            })

        return jsonify(bill_details)
    else:
        return jsonify({'error': 'Bill not found'}), 404


@app.route("/print-bill/<int:bill_id>")
def print_bill(bill_id):
    print(bill_id)
    if bill_id:
        print("HI")
        try:
            bill = Bill.query.filter_by(id=bill_id).first()
        except Exception as e:
            print("Error fetching latest bill:", e)
            return jsonify({'error': 'Failed to fetch latest bill'}), 500
    else:
        print("HELLO")
        try:
            bill = Bill.query.order_by(Bill.id.desc()).first()
        except Exception as e:
            print("Error fetching latest bill:", e)
            return jsonify({'error': 'Failed to fetch latest bill'}), 500

    print(bill)
    if bill:
        bill_id = bill.id
        bill_details = get_bill(bill_id)
        print(bill_id, bill_details)
        [bill_date, bill_time] = bill_details["bill_date_time"].split(
            " | ")

        return render_template("token_print.html",
                               bill_id=bill_id,
                               bill_date=bill_date,
                               bill_time=bill_time,
                               total=bill_details["total"],
                               items=bill_details["bill_items"]
                               )
    else:
        return jsonify({'error': 'No bills found'}), 404


@app.route("/print-report/<from_date>/<to_date>")
def print_report(from_date, to_date):
    if from_date != 0 and to_date != 0:
        bill = Bill.query.filter(
            func.date(Bill.bill_date_time) >= from_date,
            func.date(Bill.bill_date_time) <= to_date
        ).all()
    else:
        bill = Bill.query.all()

    return render_template('billwise_report.html', bills=bill)


@app.route("/print-item-report/<from_date>/<to_date>")
def print_item_report(from_date, to_date):
    print("Printing...")

    # Query to group items by their group and item name, and get the sum of quantity and total price
    grouped_items = db.session.query(
        Item.group,
        BillItem.item_name,
        func.sum(BillItem.quantity).label('total_quantity'),
        func.sum(BillItem.quantity * BillItem.price).label('total_price')
    ).join(Item, Item.id == BillItem.item_id).group_by(Item.group, BillItem.item_name).all()

    # Create a dictionary to store grouped items
    grouped_items_dict = {}
    for group, item_name, total_quantity, total_price in grouped_items:
        if group not in grouped_items_dict:
            grouped_items_dict[group] = {
                'total_quantity': 0, 'total_price': 0, 'items': {}}
        grouped_items_dict[group]['total_quantity'] += total_quantity
        grouped_items_dict[group]['total_price'] += total_price
        if item_name not in grouped_items_dict[group]['items']:
            grouped_items_dict[group]['items'][item_name] = {
                'quantity': total_quantity, 'price': total_price}
        else:
            grouped_items_dict[group]['items'][item_name]['quantity'] += total_quantity
            grouped_items_dict[group]['items'][item_name]['price'] += total_price

    # Calculate grand total
    grand_total = sum(group['total_price']
                      for group in grouped_items_dict.values())

    print(grouped_items_dict)
    return render_template('itemwise_report.html',
                           grouped_items=grouped_items_dict,
                           grand_total=grand_total,
                           from_date=from_date,
                           to_date=to_date)


@app.route("/user-activity")
def user_activity():
    activities = UserActivity.query.all()

    # Group activities by user
    user_activities = defaultdict(list)
    for activity in activities:
        user_activities[activity.user].append(activity)

    print(user_activities)

    return render_template("user_activity.html", user_activities=user_activities)


@app.route("/contact")
def contact():
    return render_template("contact.html")
