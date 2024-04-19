# app/models.py
from datetime import datetime
from app import db
from pytz import timezone
from sqlalchemy import func


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
