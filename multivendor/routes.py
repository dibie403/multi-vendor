from flask import render_template, url_for, flash, redirect, request
from multivendor import app,db
from multivendor.forms import RegistrationForm,LoginForm
from multivendor.models import User





@app.route("/")
@app.route("/home")
def home():

    return render_template('home.html',title='home')


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Convert status to boolean (True for seller, False for buyer)
        is_seller = form.status.data == "seller"

        # If user is a seller, make sure they provide shop details
        if is_seller and (not form.shop_name.data or not form.shop_motto.data):
            flash('Shop name and motto are required for sellers!', 'danger')
            return render_template('register.html', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            phone_number=form.phone.data,
            password=form.password.data,  # You should hash the password before storing
            is_admin=False,  # Assuming default is False
            shop_name=form.shop_name.data if is_seller else None,  # Only store shop name if seller
            shop_motto=form.shop_motto.data if is_seller else None,  # Only store shop motto if seller
            status=is_seller,  # True for sellers, False for buyers
            slug=form.username.data.lower().replace(" ", "-")  # Generate a slug
        )

        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))  # Redirect to login page

    return render_template('register.html', form=form)


@app.route("/login")
def login():
    form=LoginForm()

    return render_template('login.html',title='register',form=form)


