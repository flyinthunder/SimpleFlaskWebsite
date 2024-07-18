from flask import Blueprint, render_template, request, flash, jsonify, json, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, User, Inventory, Cart
from . import db
from .forms import MakeAdminForm, AddItemsForm
from datetime import datetime, timedelta

TIMEOUT_IN_MINUTES = 1
 
views = Blueprint('views', __name__)
@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    items = Inventory.query.all()
    if request.method == "POST":
        note = request.form.get('note')
        if len(note) < 1:
            flash("Note cannot be empty.", category="validation_error")
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash("Note Added", category="success")
        
    return render_template("home.html", user=current_user, items=items)

@views.route('/<int:item_id>', methods=["GET"])
def getitem(item_id):
    item = Inventory.query.get(item_id)
    return render_template('itemcard.html', item=item, user=current_user)

@views.route('/admin', methods=["GET", "POST"])
@login_required
def admin():
    if current_user.is_authenticated:
        if current_user.type == 'admin':
            form2 = MakeAdminForm()
            form = AddItemsForm()
            items = Inventory.query.all()
            time = datetime.now()
            for item in items:
                if item.just_ordered == True:
                    item.just_ordered = False
                    db.session.commit()
                if item.quantity1 < item.min_quantity and item.quantity2 < item.min_quantity:
                    item.quantity1 += item.order_quantity
                    item.quantity2 += item.order_quantity
                    item.just_ordered = True
                    db.session.commit()
                if item.time is not None and datetime.strptime(item.time, '%Y-%m-%d %H:%M:%S.%f') < time:
                    item.has_timedout = True
            if request.method == "POST":
                
                if form.submit.data and form.validate():
                    
                    name = form.name.data
                    img_url = form.img_url.data
                    description = form.description.data
                    price = form.price.data
                    quantity = form.quantity.data
                    min_quantity = form.min_quantity.data
                    order_quantity = form.order_quantity.data
                    
                    item = Inventory(name=name, img_url=img_url, description=description, price=price, quantity1=quantity, quantity2=quantity, on_hold="0", min_quantity=min_quantity, order_quantity=order_quantity)
                    db.session.add(item)
                    db.session.commit()
                    
                    flash("Successfully Added Item to Database!", category='success')
                    return render_template('admin.html', form=form, items=items, form2=form2, user=current_user)
                
                elif form2.submitadmin.data and form2.validate():
                    
                    email = form2.email.data
                    user = User.query.filter_by(email=email).first()
                    if user:
                        return render_template('make_admin.html', email=email, user=current_user)
                    else:
                        flash("User does not exist.", category="validation_error")
                        return render_template('admin.html', form=form, items=items, form2=form2, user=current_user)
                else:
                    flash("Form didn't pass validation.", category='validation_error')
                    return render_template('admin.html', form=form, items=items, form2=form2, user=current_user)
                
            elif request.method == "GET":
                return render_template('admin.html', form=form, items=items, form2=form2, user=current_user)
        else:
            return redirect(url_for('views.home'))
    else:
        return redirect(url_for('views.home'))

@views.route('/delete-note', methods=["POST"])
def delete_note():
    note = json.loads(request.data)
    note_id = note['note_id']
    note = Note.query.get(note_id)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            return jsonify({})

@views.route('/cart', methods=["GET", "POST"])
@login_required
def cart():
    user_id = current_user.id
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    items = []
    final_total = 0
    for item in cart_items:
        inv_item = Inventory.query.get(item.item_id)
        inv_item.quantity1 = item.quantity
        final_total += inv_item.price * inv_item.quantity1
        items.append(inv_item)
    return render_template('cart.html', cart=items, final_total=final_total, user=current_user)

@views.route('/<int:item_id>/add_to_cart', methods=["POST", "GET"])
def add_to_cart(item_id):

    if current_user.is_authenticated:
        user_id = current_user.id
        cart_item = Cart.query.filter_by(item_id=item_id, user_id=user_id).first()
        if cart_item:
            cart_item.quantity += 1
            db.session.add(cart_item)
            db.session.commit()
            flash("Item Added.", category="success")
        else:
            cart = Cart(item_id=item_id, user_id=user_id, quantity=1)
            db.session.add(cart)
            db.session.commit()
            flash("Item Added.", category="success")
    else:
        flash('You need to log in to add items to your cart', category='danger')
        return redirect(url_for('auth.loginPage'))
    return redirect(url_for('views.home'))

@views.route('/cart/<int:item_id>/remove', methods=["POST", "GET"])
def remove_from_cart(item_id):
    user_id = current_user.id
    cart_item = Cart.query.filter_by(item_id=item_id, user_id=user_id).first()

    if not cart_item:
        return redirect(url_for('views.cart'))

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        db.session.add(cart_item)
        db.session.commit()
    else:
        db.session.delete(cart_item)
        db.session.commit()

    return redirect(url_for('views.cart'))

@views.route('/<int:item_id>/found', methods=["POST", "GET"])
def items_found(item_id):
    item = Inventory.query.filter_by(id=item_id).first()
    item.time = None
    item.quantity1 += int(item.on_hold)
    item.on_hold = 0
    db.session.commit()
    return redirect(url_for('views.admin'))

@views.route('/<int:item_id>/lost', methods=["POST", "GET"])
def items_lost(item_id):
    item = Inventory.query.filter_by(id=item_id).first()
    item.time = None
    item.quantity2 -= int(item.on_hold)
    item.on_hold = 0
    db.session.commit()
    return redirect(url_for('views.admin'))

@views.route('/cart/clear', methods=["POST", "GET"])
def clear_cart():
    user_id = current_user.id
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    for cart_item in cart_items:
        db.session.delete(cart_item)
        db.session.commit()

    return redirect(url_for('views.cart'))

def message_flasher(error_items, success_items):
    print(success_items, error_items)
    if error_items == []:
        if len(success_items) > 1:
            flash(", ".join(success_items) + " were successfully purchased.", category="success")
        elif len(success_items) == 1:
            flash(success_items[0] + " was purchased.", category="success")
        return True
    else:
        if len(success_items) > 1:
            flash(", ".join(success_items) + " were successfully purchased.", category="success")
        elif len(success_items) == 1:
            flash(success_items[0] + " was purchased.", category="success")

        if len(error_items) > 1:
            flash(", ".join(error_items) + " could not be purchased.", category="validation_error")
        elif len(error_items) == 1:
            flash(error_items[0] + " could not be purchased.", category="validation_error")

        return False

@views.route('/cart/checkout', methods=["POST", "GET"])
def checkout():
    user_id = current_user.id
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    
    if current_user.type == "admin":
        success_items = []
        error_items = []
        for cart_item in cart_items:
            item = Inventory.query.filter_by(id=cart_item.item_id).first()
            if item.quantity1 >= cart_item.quantity and item.quantity2 >= cart_item.quantity:
                item.reduce_quantity1(cart_item.quantity)
                item.reduce_quantity2(cart_item.quantity)
                db.session.delete(cart_item)
                db.session.commit()
                success_items.append(item.name)
            else:
                error_items.append(item.name)
            
        if message_flasher(error_items=error_items, success_items=success_items):
            return redirect(url_for('views.checkout_success'))
        else:
            return redirect(url_for('views.checkout_failure'))

    elif current_user.type == "Sensor":
        #Add items on hold.
        success_items = []
        error_items = []
        for cart_item in cart_items:
            item = Inventory.query.filter_by(id=cart_item.item_id).first()
            if item.quantity1 >= cart_item.quantity:
                item.reduce_quantity1(cart_item.quantity)
                item.increase_onhold(cart_item.quantity, TIMEOUT_IN_MINUTES)
                db.session.delete(cart_item)
                db.session.commit()
                success_items.append(item.name)
            else:
                error_items.append(item.name)
        
        if message_flasher(error_items=error_items, success_items=success_items):
            return redirect(url_for('views.checkout_success'))
        else:
            return redirect(url_for('views.checkout_failure'))
    
    elif current_user.type == "POS":
        #Remove items on hold and inventory.
        success_items = []
        error_items = []
        for cart_item in cart_items:
            item = Inventory.query.filter_by(id=cart_item.item_id).first()
            if item.get_onhold_qty() >= cart_item.quantity and item.quantity2 >= cart_item.quantity: 
                item.reduce_quantity2(cart_item.quantity)
                item.reduce_onhold(cart_item.quantity)
                db.session.delete(cart_item)
                db.session.commit()
                success_items.append(item.name)
            elif item.quantity2 >= cart_item.quantity and int(item.on_hold) < cart_item.quantity:
                error_items.append(item.name)
            else:
                flash("Impossible error. Something somewhere went horribly wrong.", category="validation_error")
                return redirect(url_for('views.checkout_failure'))
        
        if message_flasher(error_items=error_items, success_items=success_items):
            return redirect(url_for('views.checkout_success'))
        else:
            return redirect(url_for('views.checkout_failure'))
    
    elif current_user.type == "Customer":
        #Checkout like an online user.
        success_items = []
        error_items = []
        for cart_item in cart_items:
            item = Inventory.query.filter_by(id=cart_item.item_id).first()
            if item.quantity1 >= cart_item.quantity and item.quantity2 >= cart_item.quantity:
                item.reduce_quantity1(cart_item.quantity)
                item.reduce_quantity2(cart_item.quantity)
                db.session.delete(cart_item)
                db.session.commit()
                success_items.append(item.name)
            else:
                error_items.append(item.name)
        
        if message_flasher(error_items=error_items, success_items=success_items):
            return redirect(url_for('views.checkout_success'))
        else:
            return redirect(url_for('views.checkout_failure'))
    
    else:
        flash("Impossible error. This type of user should not exist.", category="validation_error")
        return redirect(url_for('views.checkout_failure'))

@views.route("/checkout_success", methods=["POST", "GET"])
def checkout_success():
    return render_template("checkout_success.html", user=current_user) 

@views.route("/checkout_failure", methods=["POST", "GET"])
def checkout_failure():
    return render_template("checkout_failure.html", user=current_user) 

@views.route("/make_admin/<email>", methods=["POST", "GET"])
def MakeAdmin(email):
    
    user = User.query.filter_by(email=email).first()
    user.makeAdmin()
    
    return redirect(url_for('views.admin'))