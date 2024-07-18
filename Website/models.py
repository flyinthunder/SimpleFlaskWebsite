from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime, timedelta

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    firstName = db.Column(db.String(150))
    lastName = db.Column(db.String(150))
    phone = db.Column(db.String(10))
    notes = db.relationship('Note')
    type = db.Column(db.String(10))

    def makeAdmin(self):
        self.type = "admin"
        db.session.commit()

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    img_url = db.Column(db.String, nullable=False)
    description = db.Column(db.String(1000))
    price = db.Column(db.Float, nullable=False)
    quantity1 = db.Column(db.Integer, nullable=False)
    quantity2 = db.Column(db.Integer, nullable=False)
    on_hold = db.Column(db.String(25000))
    time = db.Column(db.String(150))
    has_timedout = db.Column(db.Boolean, default=False)
    min_quantity = db.Column(db.Integer, nullable=False)
    order_quantity = db.Column(db.Integer, nullable=False)
    just_ordered = db.Column(db.Boolean, default=False)

    def reduce_quantity1(self, qty):
        self.quantity1 -= qty
        db.session.commit()
    
    def reduce_quantity2(self, qty):
        self.quantity2 -= qty
        db.session.commit()
    
    def reduce_onhold(self, qty):
        if self.on_hold == None:
            self.on_hold = "0"
            db.session.commit()
        if int(self.on_hold) == qty:
            self.time = None
        on_hold = int(self.on_hold)
        self.on_hold = str(on_hold - qty)
        db.session.commit()

    def increase_quantity1(self, qty):
        self.quantity1 += qty
        db.session.commit()

    def increase_quantity2(self, qty):
        self.quantity2 += qty
        db.session.commit()

    def increase_onhold(self, qty, timeout_in_minutes):
        if self.on_hold == None:
            self.on_hold = "0"
            db.session.commit()
        on_hold = int(self.on_hold)
        self.on_hold = str(on_hold + qty)
        self.time = datetime.now() + timedelta(minutes=timeout_in_minutes)
        db.session.commit()
    
    def get_onhold_qty(self):
        if self.on_hold == None:
            self.on_hold = "0"
            db.session.commit()
        return int(self.on_hold)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
