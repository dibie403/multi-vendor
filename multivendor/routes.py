
import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify
from multivendor import app,db,bcrypt
from flask_login import login_user,current_user,logout_user,login_required
from multivendor.forms import RegistrationForm,LoginForm,UpdateProfileForm,AddProductForm,UpdateshopForm
from multivendor.models import User,Product
import re





@app.route("/")
@app.route("/home/power")
def home():
    image_file = None
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)

    return render_template('home.html',title='home',image_file=image_file)


@app.route("/home/register", methods=['GET', 'POST'])
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
                slug=form.username.data.lower().replace(" ", "-"),  # Generate a slug
                slug1 = form.shop_name.data.lower().replace(" ", "-")  
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




@app.route("/store/<string:username>,")
def shop2(username):
    image_file = None
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)


    return render_template('shop.html',title='shop',image_file=image_file)


def save_picture(form_picture):
    random_hex=secrets.token_hex(8)
    _,f_ext=os.path.split(form_picture.filename)
    picture_fn=random_hex +f_ext
    picture_path=os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size=(250,250)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def save_picture1(form_picture):
    random_hex=secrets.token_hex(8)
    _,f_ext=os.path.split(form_picture.filename)
    picture_fn=random_hex +f_ext
    picture_path=os.path.join(app.root_path, 'static/product_images', picture_fn)

    output_size=(250,250)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn
def save_picture2(form_picture):
    random_hex=secrets.token_hex(8)
    _,f_ext=os.path.split(form_picture.filename)
    picture_fn=random_hex +f_ext
    picture_path=os.path.join(app.root_path, 'static/corasel', picture_fn)

    output_size=(250,250)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/home/Profile-Edit", methods=['GET', 'POST'])
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

@app.route("/plazo/{current_user.username}")
def plazo():
    image_file = None
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)


    return render_template('home.html',title='shop',image_file=image_file)




@app.route('/copy_link', methods=['GET'])
def copy_link():
    # Get the referrer URL (the page the request came from)
    current_url = request.referrer  
    flash('Store website link copied successfully!', 'success')
    
    # Render a template that will copy the URL and then redirect.
    return render_template('copy_link.html', link=current_url)


def generate_slug(name):
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')
    return slug

@app.route("/add-Product", methods=['GET', 'POST'])
def New_product():
    form = AddProductForm()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    image = None  # Set image to None initially
    
    if form.validate_on_submit():
        # Handle invalid file types
        if form.picture.errors:
            for error in form.picture.errors:
                flash(f"File upload error: {error}", "danger")
            return redirect(url_for('new_post'))
        
        # Save the image if provided
        if form.picture.data:
            try:
                # Save image temporarily or upload to cloud storage
                picture_file = save_picture1(form.picture.data)  # Saves image locally to static/post_images
                image = picture_file  # Update image reference to the saved image
                print(f"Image saved: {image}")  # Debug log
            except Exception as e:
                print(f"Error saving image: {e}")
                flash("Error saving the image. Please try again.", 'danger')
                return redirect(url_for('new_post'))
        
        # Generate the slug based on the title
        slug = generate_slug(form.name.data)
        
        # Create and add the new post
        product = Product(
            name=form.name.data.upper(),
            description=form.description.data,
            amount=form.amount.data,
            category= form.category.data,
            shelf= form.shelf.data,
            user_id=current_user.id,
            slug=slug,
            image=image  # Save image file reference (path or cloud URL)
        )
        db.session.add(product)
        db.session.commit()
        flash("Producted added successfully", "success")
        return redirect(url_for('shop2',username=current_user.slug1))
    
   

    return render_template('add_product.html', form=form,image_file=image_file)



@app.route("/shop-edit", methods=['GET', 'POST'])
def shop_edit():
    form = UpdateshopForm()
    image_file = None
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    image = None  # Set image to None initially
    
    if form.validate_on_submit():

        try:
            
            if form.picture.data:
                picture_file = save_picture2(form.picture.data)

                current_user.image_file = picture_file

            # Correctly assign values without commas
            current_user.shop_name = form.shop_name.data
            current_user.shop_motto = form.shop_motto.data
            current_user.shop_about = form.shop_about.data
            current_user.slug1 = form.shop_name.data.lower().replace(" ", "-")  # Generate a slug
            
            db.session.commit()
            flash('Profile Updated Successfully!', 'success')
            return redirect(url_for('shop2',username=current_user.slug1))
        except Exception as e:
            db.session.rollback()  # Ensure rollback if there's an error
            flash("An error occurred while processing your update. Please try again.", "danger")
            print(e)
        

    elif request.method == 'GET':
        form.shop_name.data = current_user.shop_name
        form.shop_motto.data = current_user.shop_motto

    return render_template('shop_edit.html', form=form,image_file=image_file)





   


