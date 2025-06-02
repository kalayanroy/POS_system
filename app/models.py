from app import db, login # login might not be needed here if only models
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime # Import datetime

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True, nullable=False)
    description = db.Column(db.String(255))
    purchase_price = db.Column(db.Float, nullable=False)
    sale_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Optional: if we want to link products to users

    def __repr__(self):
        return '<Product {}>'.format(self.name)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchase_price_at_time = db.Column(db.Float, nullable=False) # Price per unit at time of purchase
    purchase_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    product = db.relationship('Product', backref=db.backref('purchases', lazy='dynamic'))

    def __repr__(self):
        return '<Purchase ProductID:{} Qty:{}>'.format(self.product_id, self.quantity)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    sale_price_at_time = db.Column(db.Float, nullable=False) # Price per unit at time of sale
    cost_price_at_time_of_sale = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Optional: track who made the sale

    product = db.relationship('Product', backref=db.backref('sales', lazy='dynamic'))

    def __repr__(self):
        return '<Sale ProductID:{} Qty:{}>'.format(self.product_id, self.quantity_sold)
