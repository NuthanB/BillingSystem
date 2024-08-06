from flaskwebgui import FlaskUI
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from pytz import timezone
from sqlalchemy import func
from sqlalchemy.sql import func
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from collections import defaultdict

import webview

def is_user_logged_in():
    return 'user_id' in session
    
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = '12345'
bcrypt = Bcrypt(app)

webview.create_window('DSU Canteen', app)


with app.app_context():
    db.create_all()

    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    items = db.relationship('Item', backref='user', lazy=True)
    activity = db.relationship('UserActivity', backref='user',
                               lazy=True, cascade='all, delete-orphan')


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    items = db.relationship('BillItem', backref='item',
                            lazy=True, cascade='all, delete-orphan')


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bill_date_time = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone("Asia/Kolkata")))
    total = db.Column(db.Float, nullable=False)
    items = db.relationship('BillItem', backref='bill',
                            lazy=True, cascade='all, delete-orphan')


class BillItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey(
        'bill.id', ondelete='CASCADE'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey(
        'item.id', ondelete='CASCADE'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)


class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone("Asia/Kolkata")))
    activity_performed = db.Column(db.String(200), nullable=False)


@app.route('/')
@app.route('/index')
def index():
    try:
        uid = session['user_id']
        items = Item.query.all()
    except KeyError:
        return redirect('/login')

    return render_template('index.html', items=items)


@app.route('/get-suggestions')
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


@app.route('/get-emails-unames', methods=['GET'])
def get_emails_unames():
    emails = [user.email for user in User.query.all()]
    unames = [user.username for user in User.query.all()]
    return jsonify({'emails': emails, 'unames': unames})


@app.route('/get-obj-codes', methods=['GET'])
def get_obj_codes():
    codes = [item.code for item in Item.query.all()]
    return jsonify({'codes': codes})


@app.route("/get-item-name")
def get_item_name():
    code = request.args.get('code')
    try:
        item_name = Item.query.filter_by(code=code).first().name
        if item_name:
            return jsonify({'name': item_name}), 200
    except:
        return jsonify({'error': 'Item not found'}), 404


@app.route("/get-item-code")
def get_item_code():
    name = request.args.get('name')
    try:
        item_code = Item.query.filter_by(name=name).first().code
        if item_code:
            return jsonify({'code': item_code}), 200
    except:
        return jsonify({'error': 'Item not found'}), 404


@app.route('/get-item-price')
def get_item_price():
    code = request.args.get('item_code').lower()
    item = Item.query.filter_by(code=code).first()
    if item:
        return jsonify({'price': item.price})
    else:
        return jsonify({'error': 'Item not found'})


def get_bill(bill):
    if bill:
        bill_details = {
            'id': bill.id,
            'bill_date_time': bill.bill_date_time.strftime('%d-%m-%Y | %H:%M'),
            'total': bill.total,
            'bill_items': []
        }

        bill_items = BillItem.query.filter_by(bill_id=bill.id).all()

        for item in bill_items:
            bill_details['bill_items'].append({
                'item_name': item.item_name,
                'quantity': item.quantity,
                'price': item.price
            })

        return bill_details

    else:
        return jsonify({'error': 'Bill not found'}), 404


@app.route('/get-bill-details')
def get_bill_details():
    bill_id = request.args.get('bill_id')
    bill = Bill.query.get(bill_id)
    if bill:
        bill_details = get_bill(bill)
        return jsonify(bill_details)
    else:
        return jsonify({'error': 'Bill not found'}), 404


@app.route('/check-match')
def check_match():
    item1Name = request.args.get('item1')
    item2Code = request.args.get('item2').lower()

    try:
        item2Name = Item.query.filter_by(code=item2Code).first()
        if item1Name.lower() == item2Name.lower():
            return jsonify({'match': 'Y'})
    except:
        return jsonify({'error': 'Item not found'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['uname']
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, username=uname).first()

        if user and bcrypt.check_password_hash(user.password, password):
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
    modal_message = None
    if request.method == 'POST':
        uname = request.form['uname']
        email = request.form['email']
        pwd = request.form['pwd']
        re_pwd = request.form['rpwd']

        existing_user_email = User.query.filter_by(email=email).first()
        existing_user_uname = User.query.filter_by(username=uname).first()
        if existing_user_email:
            modal_message = 'Email already exists.'
        elif existing_user_uname:
            modal_message = 'Username already exists.'
        elif pwd != re_pwd:
            modal_message = 'Passwords do not match.'
        else:
            user = User(
                username=uname,
                email=email,
                password=bcrypt.generate_password_hash(pwd).decode('utf-8')
            )
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('signup.html', modal_message=modal_message)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/create-bill', methods=['POST'])
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


@app.route('/submit-bill', methods=['POST'])
def submit_bill():
    if 'user_id' in session:
        user_id = session['user_id']
        data = request.json

        if data:
            items = data.get('items')
            total = data.get('total')

            if not items:
                return jsonify({'error': 'No items added to the bill'}), 400

            new_bill = Bill(user_id=user_id, total=total)
            db.session.add(new_bill)

            for item in items:
                item_db = Item.query.filter_by(
                    name=item['name']).first()

                if item_db:
                    new_quantity = item_db.quantity - item['quantity']
                    if new_quantity >= 0:
                        item_db.quantity = new_quantity
                        bill_item = BillItem(
                            bill=new_bill, item_id=item_db.id, item_name=item['name'], quantity=item['quantity'], price=item['price'])
                        db.session.add(bill_item)
                    else:
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


@app.route('/items')
def items():
    items = Item.query.all()
    return render_template('items.html', items=items)


@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        group = request.form['group']
        code = request.form['code'].lower()
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])

        if name.lower() == "coffee" or name.lower() == "tea":
            quantity = float('inf')

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


@app.route('/del-item', methods=['GET', 'POST'])
def del_item():
    item_id = request.args.get('item_id')
    item = Item.query.filter_by(id=item_id).first()

    if item:
        activity = UserActivity(user_id=session['user_id'],
                                activity_performed=f"Deleted item {item.name}")
        db.session.delete(item)
        db.session.add(activity)
        db.session.commit()
        return jsonify({'message': "Item deleted successfully"}), 200
    else:
        return jsonify({'message': "Item not found"}), 404


@app.route('/update-stock', methods=['GET', 'POST'])
def update_stock():
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


@app.route('/edit-item/<int:item_id>')
def edit_item(item_id):
    item = Item.query.get(item_id)
    if item:
        return render_template('edit_item.html', item=item)
    else:
        return redirect(url_for('items'))


@app.route('/update-item', methods=['POST'])
def update_item():
    item_id = request.form['id']
    name = request.form['name']
    group = request.form['group']
    code = request.form['code'].lower()
    price = float(request.form['price'])

    item = Item.query.get(item_id)
    if item:
        item.name = name
        item.group = group
        item.code = code
        item.price = price
        activity = UserActivity(user_id=session['user_id'],
                                activity_performed=f"Edited item {name}, {group}, {price}")
        db.session.add(activity)
        db.session.commit()
    return redirect(url_for('items'))


def get_grouped_dict(grouped_items):
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

    return grouped_items_dict


@app.route('/report')
def show_reports():
    bill = Bill.query.all()[::-1]
    grouped_items = db.session.query(
        Item.group,
        BillItem.item_name,
        func.sum(BillItem.quantity).label('total_quantity'),
        func.sum(BillItem.price).label('total_price'),
    ).join(Item, Item.id == BillItem.item_id).group_by(Item.group, BillItem.item_name).all()

    grouped_items_dict = get_grouped_dict(grouped_items=grouped_items)
    grand_total = sum(group['total_price']
                      for group in grouped_items_dict.values())

    return render_template('report.html',
                           bills=bill,
                           grouped_items=grouped_items_dict,
                           grand_total=grand_total)


@app.route('/filter-bills', methods=['GET', 'POST'])
def filter_bills():
    if request.method == 'POST':
        from_date = request.form['from_date']
        to_date = request.form['to_date']

        if from_date == "" or to_date == "":
            from_date = datetime.today().strftime('%Y-%m-%d')
            to_date = datetime.today().strftime('%Y-%m-%d')

        try:
            from_date_dt = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_dt = datetime.strptime(to_date, '%Y-%m-%d')
        except ValueError as e:
            return redirect("/report")

        if from_date_dt > to_date_dt:
            return redirect("/report")

        bills_within_date_range = Bill.query.filter(
            func.date(Bill.bill_date_time) >= from_date,
            func.date(Bill.bill_date_time) <= to_date
        ).all()[::-1]

        grouped_items = db.session.query(
            Item.group,
            BillItem.item_name,
            func.sum(BillItem.quantity).label('total_quantity'),
            func.sum(BillItem.price).label('total_price')
        ).join(Item, Item.id == BillItem.item_id).join(Bill, Bill.id == BillItem.bill_id).filter(
            Bill.id.in_([bill.id for bill in bills_within_date_range])
        ).group_by(Item.group, BillItem.item_name).all()

        grouped_items_dict = get_grouped_dict(grouped_items=grouped_items)
        grand_total = sum(group['total_price']
                          for group in grouped_items_dict.values())

        return render_template("filtered_bills.html",
                               bills=bills_within_date_range,
                               grouped_items=grouped_items_dict,
                               from_date=from_date,
                               to_date=to_date,
                               grand_total=grand_total)
    else:
        return redirect("/report")


@app.route("/print-bill")
def print_bill():
    bill_id = int(request.args.get('bill_id'))
    bill = None

    if bill_id:
        try:
            bill = Bill.query.filter_by(id=bill_id).first()
        except Exception as e:
            return jsonify({'error': 'Failed to fetch bill'}), 500
    else:
        try:
            bill = Bill.query.order_by(Bill.id.desc()).first()
        except Exception as e:
            return jsonify({'error': 'Failed to fetch latest bill'}), 500

    if bill:
        bill_details = get_bill(bill)
        [bill_date, bill_time] = bill_details["bill_date_time"].split(
            " | ")

        return render_template("token_print.html",
                               bill_id=bill.id,
                               bill_date=bill_date.replace("-", "/"),
                               bill_time=bill_time,
                               total=bill_details["total"],
                               items=bill_details["bill_items"]
                               )
    else:
        return jsonify({'error': 'No bills found'}), 404


@app.route("/print-report")
def print_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    if from_date != '0' and to_date != '0':
        bills = Bill.query.filter(
            func.date(Bill.bill_date_time) >= from_date,
            func.date(Bill.bill_date_time) <= to_date
        ).all()
    else:
        bills = Bill.query.all()

    grand_total = 0
    for bill in bills:
        grand_total += float(bill.total)

    if grand_total:
        return render_template('billwise_report.html', 
                               bills=bills, 
                               total=grand_total,
                               from_date=from_date,
                               to_date=to_date)
    else:
        return redirect("/report")


@app.route("/print-item-report")
def print_item_report():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    grouped_items = None

    if from_date != '0' and to_date != '0':
        bills_within_date_range = Bill.query.filter(
            func.date(Bill.bill_date_time) >= from_date,
            func.date(Bill.bill_date_time) <= to_date,
        ).all()

        grouped_items = db.session.query(
            Item.group,
            BillItem.item_name,
            func.sum(BillItem.quantity).label('total_quantity'),
            func.sum(BillItem.price).label('total_price')
        ).join(Item, Item.id == BillItem.item_id).join(Bill, Bill.id == BillItem.bill_id).filter(
            Bill.id.in_([bill.id for bill in bills_within_date_range])
        ).group_by(Item.group, BillItem.item_name).all()

    else:
        grouped_items = db.session.query(
            Item.group,
            BillItem.item_name,
            func.sum(BillItem.quantity).label('total_quantity'),
            func.sum(BillItem.price).label('total_price')
        ).join(Item, Item.id == BillItem.item_id).group_by(Item.group, BillItem.item_name).all()

    grouped_items_dict = get_grouped_dict(grouped_items=grouped_items)
    grand_total = sum(group['total_price']
                      for group in grouped_items_dict.values())

    if grand_total:
        return render_template('itemwise_report.html',
                               grouped_items=grouped_items_dict,
                               grand_total=grand_total,
                               from_date=from_date,
                               to_date=to_date)
    else:
        return redirect("/report")


@app.route("/user-activity")
def user_activity():
    user_id = session['user_id']
    activities = UserActivity.query.filter_by(
        user_id=user_id).order_by(UserActivity.timestamp.desc()).all()
    bill_count = Bill.query.filter_by(user_id=user_id).count()

    user_activities = defaultdict(list)
    for activity in activities:
        user_activities[activity.user].append(activity)

    return render_template("user_activity.html", user_activities=user_activities, bill_count=bill_count)


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    webview.start()
    # FlaskUI(app=app, server="flask", fullscreen=True).run()