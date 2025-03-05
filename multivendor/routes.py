
import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify
from multivendor import app,db,bcrypt
from flask_login import login_user,current_user,logout_user,login_required
from multivendor.forms import RegistrationForm,LoginForm,UpdateProfileForm,AddProductForm,UpdateshopForm,EditProductForm
from multivendor.models import User,Product,Love
import re
from datetime import datetime





@app.route("/")
@app.route("/home/power")
def home():
    image_file = None
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)

    return render_template('home.html',title='home',image_file=image_file)




def generate_slug(text):
    """Generate a slug by replacing special characters with '-' and ensuring lowercase"""
    return re.sub(r"[^\w]+", "-", text.lower()).strip("-")

@app.route("/home/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Convert status to boolean (True for seller, False for buyer)
            is_seller = form.status.data == "seller"

            # If user is a seller, ensure they provide shop details
            if is_seller and (not form.shop_name.data or not form.shop_motto.data):
                flash('Shop name and motto are required for sellers!', 'danger')
                return render_template('register.html', form=form)

            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

            # Generate slugs
            username_slug = generate_slug(form.username.data)
            shop_slug = generate_slug(form.shop_name.data) if is_seller else None

            user = User(
                username=form.username.data,
                email=form.email.data,
                phone_number=form.phone.data,
                password=hashed_password,
                is_admin=False,  # Assuming default is False
                shop_name=form.shop_name.data.upper() if is_seller else None,
                shop_motto=form.shop_motto.data if is_seller else None,
                status=is_seller,  # True for sellers, False for buyers
                slug=username_slug,  # Slug for username
                slug1=shop_slug  # Slug for shop name
            )

            db.session.add(user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))  # Redirect to login page

        except Exception as e:
            flash("An error occurred while processing your registration. Please try again.", "danger")
            print(e)  # Debugging purposes

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
            flash("Login successful!", "success")
        else:
            flash(f"Unsuccessful login,Incorrect credentials", 'danger')

    return render_template('login.html',title='login',form=form) 


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))




@app.route("/store/<string:username>")
def shop2(username):
    image_file = None
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    page = request.args.get('page', 1, type=int)

    user= User.query.filter_by(slug=username).first_or_404()
    products=Product.query.filter_by(user_id=user.id).order_by(Product.date.desc()).paginate(page=page, per_page=2)
    loved_products = {love.product_id for love in Love.query.filter_by(user_id=current_user.id).all()}
    
    print(user.shop_image_file)

    return render_template('shop.html',title='shop',image_file=image_file,products=products,user=user,loved_products=loved_products)


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
            user_slug = generate_slug(form.username.data)

            # Correctly assign values without commas
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.phone_number = form.phone.data
            current_user.status = current_user.status # True for sellers, False for buyers
            current_user.slug = user_slug # Generate a slug
            
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
        slug = generate_slug1(form.name.data)
        
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
        flash("Product added successfully", "success")
        return redirect(url_for('shop2',username=current_user.slug))
    
   

    return render_template('add_product.html', form=form,image_file=image_file,shop_theme='white')



@app.route("/shop-edit", methods=['GET', 'POST'])
def shop_edit():
    form = UpdateshopForm()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    image = None  # Set image to None initially

   
    
    if form.validate_on_submit():

        try:
            
            if form.picture.data:
                picture_file = save_picture2(form.picture.data)

                current_user.shop_image_file = picture_file
            shop_slug = generate_slug(form.shop_name.data)

            # Correctly assign values without commas
            current_user.shop_name = form.shop_name.data.upper()
            current_user.shop_motto = form.shop_motto.data
            current_user.shop_about = form.shop_about.data
            current_user.slug1 = shop_slug # Generate a slug
            
            db.session.commit()
            flash('Profile Updated Successfully!', 'success')
            return redirect(url_for('shop2',username=current_user.slug))
        except Exception as e:
            db.session.rollback()  # Ensure rollback if there's an error
            flash("An error occurred while processing your update. Please try again.", "danger")
            print(e)
        

    elif request.method == 'GET':
        form.shop_name.data = current_user.shop_name
        form.shop_motto.data = current_user.shop_motto
        form.shop_about.data= current_user.shop_about

    return render_template('shop_edit.html', form=form,image_file=image_file,shop_theme='white')



@app.route("/unlike_like_product/<int:product_id>", methods=["POST"])
@login_required
def unlike_like_product(product_id):
    product = Product.query.get_or_404(product_id)

    existing_like = Love.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        print("unlike")
        return jsonify({"status": "unliked", "product_id": product_id})
    else:
        like = Love(user_id=current_user.id, product_id=product.id)
        db.session.add(like)
        db.session.commit()
        print("like")
        return jsonify({"status": "liked", "product_id": product_id})


@app.route("/Loved_items", methods=['GET', 'POST'])
@login_required
def Loved_items(): 
    page = request.args.get('page', 1, type=int)
    product= Product.query.filter_by(user_id=current_user.id).all() 
    user= User.query.filter_by(id=current_user.id).first_or_404()
    loves= Love.query.filter_by(user_id=current_user.id).order_by(Love.date.desc()).paginate(page=page, per_page=2)
    
    return render_template('loved_items.html', loves=loves,product=product,user=user,shop_theme='white')



@app.route("/store/<string:username>/Product-page/<product_id>", methods=['GET', 'POST'])
@login_required
def product_page(product_id,username):
    product=Product.query.filter_by(id=product_id).first_or_404()

    
    return render_template('product_view.html',product=product)

@app.route('/Product-page/delete/<int:product_id>', methods=['POST', 'GET'])
@login_required
def delete_product(product_id):

    # Get the post or raise 404 if it doesn't exist
    product = Product.query.get_or_404(product_id)

    for love in product.loves:
        db.session.delete(love)


    # Delete the post itself
    db.session.delete(product)
    db.session.commit()

    flash("Product has been successfully.", "success")
    return redirect(url_for('shop2',username=current_user.slug))

import re
from datetime import datetime
from multivendor.models import Product  

def generate_slug1(name):
    """Generate a unique slug by replacing special characters and ensuring uniqueness in the database"""
    base_slug = re.sub(r"[^\w]+", "-", name.lower()).strip("-")  # Clean the text
    
    # Generate a timestamp using datetime (YYYYMMDDHHMMSS)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Example: 20250303143025
    slug = f"{base_slug}-{timestamp}"

    # Ensure uniqueness in the database
    counter = 1
    while Product.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{timestamp}-{counter}"  # Append counter if necessary
        counter += 1  # Increment counter

    return slug


  

@app.route("/edit-Product/<product_id>", methods=['GET', 'POST'])
def edit_product(product_id):
    form = EditProductForm()
    #product = Product.query.get_or_404(product_id)
    product = db.session.get(Product, product.id) 
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    
    if form.validate_on_submit():
        try:
            # Save the image if provided
            if form.picture.data:
                picture_file = save_picture1(form.picture.data)  # Save the image
                product.image = picture_file  # Update image reference
            
            # Generate a unique slug
            slug = generate_slug1(form.name.data)
            
            product.name = form.name.data.upper()
            product.description = form.description.data
            product.amount = form.amount.data
            product.category = form.category.data
            product.shelf = form.shelf.data
            product.slug = slug  # Assign the unique slug
            
            db.session.commit()
            flash("Product successfully updated!", "success")

            return redirect(url_for('shop2', username=current_user.slug))
        
        except Exception as e:
            db.session.rollback()  # Rollback changes on error
            flash("An error occurred while processing your update. Please try again.", "danger")
            print(e)

    elif request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.amount.data = product.amount
        form.category.data = product.category
        form.shelf.data = product.shelf

    return render_template('edit_product.html', form=form, image_file=image_file, shop_theme='white', product_image=product.image)


