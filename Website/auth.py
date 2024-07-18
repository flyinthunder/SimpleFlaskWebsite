from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)
user_types = ['admin', 'POS', 'Sensor', 'Customer']

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        data, validators = {}, {}
        data['email'], validators['email'] = request.form.get("email"), False
        data['password'], validators['password'] = request.form.get("password"), False

        user = User.query.filter_by(email=data['email']).first()
        check = User.query.all()
        for i in check:
            print(i.email, i.firstName, i.lastName, i.password, i.phone, i.type)
            
        if user:
            if check_password_hash(user.password, data['password']):
                flash("Login Successful!", category="success")
                login_user(user, remember=True)
                return redirect(url_for("views.home"))
            else:
                flash("Wrong Password.", category="validation_error")
        else:
            flash("User does not exist. Create a new user.", category="validation_error")

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route('/sign-up', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        data, validators = {}, {}
        data['email'], validators['email'] = request.form.get("email"), False
        data['firstName'], validators['firstName'] = request.form.get("firstName"), False
        data['lastName'], validators['lastName'] = request.form.get("lastName"), False
        data['phone'], validators['phone'] = request.form.get("phone"), False
        data['user_type'] = request.form.get("user-type")
        data['password1'], validators['password'] = request.form.get("password1"), False
        data['password2'] = request.form.get("password2")
        print(data['user_type'])
        user = User.query.filter_by(email=data['email']).first()
        if user:
            flash("Email already taken. Please login instead.", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)

        # Email Checks:
        if len(data['email']) < 4:
            #Email looks too small
            flash("Email must be atleast 4 characters", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        elif "@" not in data['email']:
            #Email must have @
            flash("Email must contain '@'", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        elif "." not in data['email']:
            #Email must have .
            flash("Email must contain '.'", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        else:
            #all email checks pass
            validators['email'] = True


        # Name Checks:
        if len(data['firstName']) == 0:
            # Name cannot be empty
            flash("First Name cannot be empty", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        else:
            validators['firstName'] = True

        if len(data['lastName']) == 0:
            # Name cannot be empty
            flash("Last Name cannot be empty", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        else:
            validators['lastName'] = True
        

        # Phone number checks:
        if len(data['phone']) != 10:
            # Phone number needs to be 10 digits.
            flash("Phone number needs to be 10 digits", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        elif not data['phone'].isnumeric():
            # Phone number has letters
            flash("Phone number can only contain numbers", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        else:
            validators['phone'] = True

        # Password Checks
        sp_chars = "[@_!#$%^&*()<>?/\|}{~:]"
        short = len(data['password1']) >= 8
        upper = any(letter.isupper() for letter in data['password1'])
        lower = any(letter.islower() for letter in data['password1'])
        special = any(letter in sp_chars for letter in data['password1'])
        number = any(letter.isnumeric() for letter in data['password1'])
        match = data['password1'] == data['password2']

        if not short:
            flash("Password needs to have atleast 8 characters.", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        elif not upper:
            flash("Password needs to have atleast 1 upper case character.", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        elif not lower:
            flash("Password needs to have atleast 1 lower case character.", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        elif not special:
            flash("Password needs to have atleast 1 special character.", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        elif not number:
            flash("Password needs to have atleast 1 number.", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        elif not match:
            flash("Passwords need to match.", category="validation_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        elif upper and lower and special and number and match:
            validators['password'] == True
        else:
            #How did we even get here ?
            flash("This is beyond science.", category="impossible_error")
            return render_template("signup.html", user=current_user, user_types=user_types)
        
        validation = True
        for validator in validators:
            if not validator:
                not validation
        if validation:
            new_user = User(email=data['email'], firstName=data['firstName'], lastName=data['lastName'], phone=data['phone'], password=generate_password_hash(data['password1'], method='pbkdf2:sha256'), type=data["user_type"])
            db.session.add(new_user)
            db.session.commit()
            flash("Account Created.", category="success")
            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))
            

    return render_template("signup.html", user=current_user, user_types=user_types)