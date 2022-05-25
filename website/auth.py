import re
from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import current_user, login_user, login_required, logout_user
from .models import Usr

auth = Blueprint('auth',__name__ )

@auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password1')
        rememberMe = request.form.get('rememberMe')

        user = Usr.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=rememberMe)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password', category='error')
        else:
            flash('Email does not exist', category='error')

    return render_template("login.html")


@auth.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        name = request.form.get('fullName')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = Usr.query.filter_by(email=email).first()

        if user:
            flash("Email already registered", category="error")
        else:     
            if not re.match("^[A-Za-z]+[ ][A-Za-z]+$", str(name)):
                flash("Invalid name", category="error") 
            elif (len(name) > 30):
                flash("Invalid name length, it should be under <30 chars", category="error")
            elif not re.match("^[0-9a-z._]+[@][a-z]+\.[A-Za-z]+$", str(email)):
                flash("Invalid email", category="error")
            elif(len(email) > 30):
                flash("Invalid email length, it should be <30 chars", category="error")
            elif (password1 != password2):
                flash("Passwords do not match!", category="error")
            elif (len(password1) < 8 or len(password1) > 20):
                flash("Invalid password length, it should be between 8 - 20 chars", category="error")
            else:
                new_user = Usr(full_name = name, email = email, password = generate_password_hash(password1, method='sha256'))
                db.session.add(new_user)
                db.session.commit()

                login_user(new_user)
                flash("Account created", category="success")
                return redirect(url_for('views.home'))

    return render_template("register.html")

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))