
import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from multivendor import app,db,bcrypt
from flask_login import login_user,current_user,logout_user,login_required
from multivendor.forms import RegistrationForm,LoginForm,UpdateProfileForm
from multivendor.models import User





@app.route("/")
@app.route("/home")
def home():
    image_file = None
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)

    return render_template('home.html',title='home',image_file=image_file)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Convert status to boolean (True for seller, False for buyer)
            is_seller = form.status.data == "seller"

            # If user is a seller, make sure they provide shop details
            if is_seller and (not form.shop_name.data or not form.shop_motto.data):
                flash('Shop name and motto are required for sellers!', 'danger')
                return render_template('register.html', form=form)
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(
                username=form.username.data,
                email=form.email.data,
                phone_number=form.phone.data,
                password=hashed_password,  # You should hash the password before storing
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
        except Exception as e:
            flash("An error occurred while processing your registration. Please try again.", "danger")

    return render_template('register.html', form=form)


@app.route("/login",methods=['POST','GET'])
def login():
    form=LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.remember.data)
            next_page= request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
            #flash(f"Welcome {form.email.data}!, Check what's New on the Site😊", 'success')
        else:
            flash(f"Unsuccessful login,Incorrect credentials", 'danger')

    return render_template('login.html',title='login',form=form) 


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/shop")
@login_required
def shop():
    image_file = None
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)


    return render_template('shop.html',title='shop',image_file=image_file)


def save_picture(form_picture):
    random_hex=secrets.token_hex(8)
    _,f_ext=os.path.split(form_picture.filename)
    picture_fn=random_hex +f_ext
    picture_path=os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size=(1000,600)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/Profile-Edit", methods=['GET', 'POST'])
def profile_edit():
    form = UpdateProfileForm()
    
    if form.validate_on_submit():
       
           
        try:
            # Convert status to boolean (True for seller, False for buyer)
            current_user.status = form.status.data == 'True'
            if form.picture.data:
                picture_file = save_picture(form.picture.data)

                current_user.image_file = picture_file

            # Correctly assign values without commas
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.phone_number = form.phone.data
            current_user.status = current_user.status # True for sellers, False for buyers
            current_user.slug = form.username.data.lower().replace(" ", "-")  # Generate a slug
            
            db.session.commit()
            flash('Profile Updated Successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()  # Ensure rollback if there's an error
            flash("An error occurred while processing your update. Please try again.", "danger")
            print(e)

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.phone.data = current_user.phone_number
        form.status.data = "True" if current_user.status else "False"

    return render_template('edit_profile.html', form=form)



   


