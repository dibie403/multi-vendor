
import os
import secrets
import uuid
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify, session
from multivendor import app,db,bcrypt,mail,cache
from flask_login import login_user,current_user,logout_user,login_required
from multivendor.forms import RegistrationForm,LoginForm,UpdateProfileForm,AddProductForm,UpdateshopForm,EditProductForm,RequestResetTokenForm,ResetPasswordForm,PersonalInfoForm
from multivendor.models import User,Product,Love,CartItem,OrderItem,Order,Notification,Subscription,PersonalInfo,StoreVisit
import re
from datetime import datetime

import random
from urllib.parse import quote,urlparse, urljoin
from flask_mail import Message
import smtplib
import socket
from flask import make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import func, desc


# Initialize Limiter
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"])




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

# Add this once in your Flask app
@app.context_processor
def inject_datetime():
    from datetime import datetime
    return dict(datetime=datetime)

@app.context_processor
def inject_target_date():
    target_date = datetime(2025, 7, 12, 7, 7, 19, 960156)
    return dict(target_date=target_date)

@app.context_processor
def inject_notification_count():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    else:
        unread_count = 0
    return dict(unread_notification_count=unread_count)





@app.route("/")
@app.route("/home/power")
def home():
    page = request.args.get('page', 1, type=int)

    # Fetch products with a single query
    products = Product.query.paginate(page=page, per_page=10)

    # Render the template
    rendered = render_template('home.html', title='home', products=products)

    # Create a response with caching headers
    response = make_response(rendered)
    response.headers['Cache-Control'] = 'public, max-age=300, s-maxage=600, stale-while-revalidate=900'
    
    return response





def generate_slug(text):
    """Generate a slug by replacing special characters with '-' and ensuring lowercase"""
    return re.sub(r"[^\w]+", "-", text.lower()).strip("-")






import resend

# Assuming resend.api_key has been set earlier in your code
resend.api_key = os.getenv("RESEND_API_KEY")  # Ensure the API key is fetched from the environment

def send_welcome_email(user):
    try:
        # Render the HTML email content from your template
        html_content = render_template('welcome_email.html', user=user)

        # Send the email using Resend API
        response = resend.Emails.send({
            "from": "Vendera Team <gracedibie691@gmail.com>",  # Use a verified sender email
            "to": user.email,  # The recipient email
            "subject": "🎉 Welcome to Vendera!",  # Subject of the email
            "html": html_content,  # HTML email content
            "text": f"Welcome to Vendera, {user.username}!\nVisit us: {url_for('home', _external=True)}"  # Plain text fallback
        })

        print("Welcome email sent successfully. Response:", response)
    except Exception as e:
        print("Error sending welcome email:", e)






@app.route("/home/register", methods=['GET', 'POST'])
def register():
    next_page = request.args.get("next")  # 👈 Preserve it during GET and POST

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            is_seller = form.status.data == "seller"
            if is_seller and (not form.shop_name.data or not form.shop_motto.data):
                flash('Shop name and motto are required for sellers!', 'danger')
                return render_template('register.html', form=form, next=next_page)

            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

            username_slug = generate_slug(form.username.data)
            shop_slug = generate_slug(form.shop_name.data) if is_seller else None

            user = User(
                username=form.username.data,
                email=form.email.data,
                phone_number=form.phone.data,
                password=hashed_password,
                is_admin=False,
                shop_name=form.shop_name.data.upper() if is_seller else None,
                shop_motto=form.shop_motto.data if is_seller else None,
                status=is_seller,
                slug=username_slug,
                slug1=shop_slug
            )

            db.session.add(user)
            db.session.commit()
            send_welcome_email(user)
            flash('Account created successfully!', 'success')

            # ✅ Redirect back to login with ?next=...
            return redirect(url_for('login', next=next_page))

        except Exception as e:
            flash("An error occurred during registration.", "danger")
            print(e)

    return render_template('register.html', form=form, next=next_page)






from urllib.parse import urlparse, urljoin

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    next_page = request.args.get("next")  # 🔐 Captured from URL query

    if current_user.is_authenticated:
        return redirect(next_page) if next_page and is_safe_url(next_page) else redirect(url_for('home'))

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Login successful!", "success")

            # ✅ Redirect to original destination if it’s safe
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash("Unsuccessful login. Incorrect credentials.", "danger")

    return render_template("login.html", title="Login", form=form, next=next_page)



@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


from datetime import datetime, timedelta

def check_subscription_status(user):
    # Check if the user is a superuser (superusers should always have access)
    if user.is_super:
        return True
    
    # Check if the user is subscribed and if their subscription is still valid
    if user.is_subscribed and user.subscription_end > datetime.utcnow():
        return True  # Subscription is valid
    
    # Check if the user is on a free trial (less than 30 days since registration)
    if user.date and datetime.utcnow() - user.date < timedelta(days=30):
        return True  # User is on free trial
    
    # If no conditions are met, return False
    return False

from datetime import date

def get_today_visits(seller_id):
    today = date.today()
    visit_count = StoreVisit.query.filter(
        StoreVisit.seller_id == seller_id,
        func.date(StoreVisit.visit_time) == today
    ).count()
    return visit_count


@app.route("/store/<string:shop_name>")
def shop2(shop_name):
    image_file = None
    page = request.args.get('page', 1, type=int)
    
    # Query the user and product in one go
    user = User.query.filter_by(slug1=shop_name).first_or_404()
    is_valid = check_subscription_status(user)

    # --- Begin visit logging logic ---
    seller_id = user.id
    today = date.today()

    if current_user.is_authenticated:
        if current_user.id != seller_id:
            already_visited = StoreVisit.query.filter_by(
                user_id=current_user.id,
                seller_id=seller_id
            ).filter(func.date(StoreVisit.visit_time) == today).first()

            if not already_visited:
                visit = StoreVisit(user_id=current_user.id, seller_id=seller_id)
                db.session.add(visit)
                db.session.commit()
    else:
        # Generate a unique session ID if not present
        if 'visitor_session' not in session:
            session['visitor_session'] = str(uuid.uuid4())

        session_id = session['visitor_session']

        already_visited = StoreVisit.query.filter_by(
            session_id=session_id,
            seller_id=seller_id
        ).filter(func.date(StoreVisit.visit_time) == today).first()

        if not already_visited:
            visit = StoreVisit(user_id=None, seller_id=seller_id, session_id=session_id)
            db.session.add(visit)
            db.session.commit()

    visit_count = get_today_visits(seller_id)
    # --- End visit logging logic ---

    # Fetch products with a single query
    products_query = Product.query.filter_by(user_id=user.id).order_by(Product.date.desc())
    products = products_query.paginate(page=page, per_page=12)

    if current_user.is_authenticated:
        # Efficient retrieval of loved products using set comprehension
        loved_product_ids = {love.product_id for love in Love.query.filter_by(user_id=current_user.id).all()}

        # Efficient retrieval of cart items
        seller_id = products_query.first().user_id if products_query.first() else None
        cart_items = get_cart_items_for_seller(current_user.id, seller_id)
        cart_count = len(cart_items) if cart_items else 0

        return render_template('shop.html',
                               title='shop',
                               products=products,
                               user=user,
                               visit_count=visit_count,
                               loved_products=loved_product_ids,
                               cart_count=cart_count,
                               is_valid=is_valid,
                               shop_theme=user.shop_theme)
    else:
        # Render and cache the response only for unauthenticated users
        rendered = render_template('shop.html',
                                   title='shop',
                                   image_file=image_file,
                                   products=products,
                                   user=user,
                                   shop_theme=user.shop_theme,
                                   is_valid=is_valid)

        response = make_response(rendered)
        response.headers['Cache-Control'] = 'public, max-age=300, s-maxage=600, stale-while-revalidate=900'
        return response







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
            user_slug2 = generate_slug(form.shop_name.data)

            # Correctly assign values without commas
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.phone_number = form.phone.data
            current_user.status = current_user.status # True for sellers, False for buyers
            current_user.slug = user_slug # Generate a slug
            current_user.slug1 =user_slug2 # save genrated slug to shop_name coloum in database
            current_user.shop_name = form.shop_name.data
            
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
        form.shop_name.data = current_user.shop_name

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

@app.route("/add-Product", methods=['GET', 'POST'])
@login_required
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
        return redirect(url_for('shop2',shop_name=current_user.slug1))
    
   

    return render_template('add_product.html', form=form,image_file=image_file,shop_theme=current_user.shop_theme)


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
            current_user.shop_name = form.shop_name.data.upper()
            current_user.shop_motto = form.shop_motto.data
            current_user.shop_about = form.shop_about.data
            current_user.slug1 = shop_slug

            # Handle theme choice here (use form.shop_theme.data directly)
            if form.shop_theme.data == 'none':  # No theme selected
                current_user.shop_theme = None
            else:
                current_user.shop_theme = form.shop_theme.data

            db.session.commit()
            flash('Profile Updated Successfully!', 'success')
            return redirect(url_for('shop2', shop_name=current_user.slug1))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while processing your update. Please try again.", "danger")
            print(e)

    elif request.method == 'GET':
        # Default the theme value to 'none' if it's None
        form.shop_name.data = current_user.shop_name
        form.shop_motto.data = current_user.shop_motto
        form.shop_about.data = current_user.shop_about
        form.shop_theme.data = current_user.shop_theme if current_user.shop_theme else 'none'  # Default to 'none'

    return render_template('shop_edit.html', form=form, image_file=image_file, shop_theme=current_user.shop_theme)


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
    product= Product.query.filter_by(user_id=current_user.id).limit(10).all()
    user= User.query.filter_by(id=current_user.id).first_or_404()
    loves= Love.query.filter_by(user_id=current_user.id).order_by(Love.date.desc()).paginate(page=page, per_page=10)
    
    return render_template('loved_items.html', loves=loves,product=product,user=user,shop_theme=current_user.shop_theme)





@app.route("/store/<string:shop_name>/Product-page/<product_id>", methods=['GET', 'POST'])
def product_page(product_id, shop_name):
    print("💾 Fetching product from database...")  # <-- this will show up in terminal/log if DB is hit

    product = Product.query.filter_by(id=product_id).first_or_404()
    seller = User.query.filter_by(id=product.user_id).first()
    if current_user.is_authenticated:
        cart_items = get_cart_items_for_seller(current_user.id, product.user_id)
        cart_count = len(cart_items) if cart_items else 0
        track_code = generate_track_code()

        rendered = render_template(
            'product_view.html', 
            product=product, 
            cart_count=cart_count, 
            track_code=track_code, 
            seller_id=product.user_id, 
            shop_theme=seller.shop_theme
        )
    else:
         rendered = render_template(
            'product_view.html', 
            product=product, 
            seller_id=product.user_id, 
            shop_theme=seller.shop_theme
        )

    response = make_response(rendered)
    response.cache_control.public = True
    response.cache_control.max_age = 300  # 5 minutes

    return response



@app.route("/Product-View/<shop_name>/<int:product_id>", methods=['GET', 'POST'])
def product_page_neutral(product_id, shop_name):
    # Fetch the product details (no changes needed)
    product = Product.query.filter_by(id=product_id).first_or_404()
    
    # Fetch seller info (can cache this if needed to avoid redundant queries)
    seller = User.query.filter_by(id=product.user_id).first()
    
    # Generate a track code for this product (no changes needed)
    track_code = generate_track_code()

    return render_template(
        'product_view2Neutral.html',
        product=product,
        track_code=track_code,
        seller_id=product.user_id,
        shop_theme=seller.shop_theme
    )

@app.route('/Product-page/delete/<int:product_id>', methods=['POST', 'GET'])
@login_required
def delete_product(product_id):
    # Get the product or raise 404 if it doesn't exist
    product = Product.query.get_or_404(product_id)

    # Delete all related cart items first
    CartItem.query.filter_by(product_id=product.id).delete()

    # Delete related "loves" if applicable
    for love in product.loves:
        db.session.delete(love)

    # Delete related order items
    for order in product.order_items:
        db.session.delete(order)

    # Delete the product itself
    db.session.delete(product)
    db.session.commit()

    flash("Product has been successfully deleted.", "success")
    return redirect(url_for('shop2', shop_name=current_user.slug1))

@app.route('/Product-page/delete/product/<int:product_id>', methods=['POST', 'GET'])
@login_required
def delete_product22(product_id):
    # Get the product or raise 404 if it doesn't exist
    #product = Product.query.get_or_404(product_id)

    # Delete all related cart items first
    love=Love.query.filter_by(product_id=product_id,user_id=current_user.id).first()
    db.session.delete(love) 
    db.session.commit()

    flash("Product has been successfully deleted.", "success")
    return redirect(url_for('Loved_items'))


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
@login_required
def edit_product(product_id):
    form = EditProductForm()
    product = Product.query.get_or_404(product_id)
    #product = db.session.get(Product, product.id) 
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

            return redirect(url_for('shop2', shop_name=current_user.slug1))
        
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

    return render_template('edit_product.html', form=form, image_file=image_file, shop_theme=current_user.shop_theme, product_image=product.image)

@app.route("/cart/<seller_id>")
@login_required
def cart(seller_id):
    """Show cart items only for the current store's seller"""
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page

    seller = User.query.filter_by(id=seller_id).first_or_404()

    cart_items1 = get_cart_items_for_seller(current_user.id, seller.id)  # This returns a list
    track_code = generate_track_code()
    total_amount = sum(item.product.amount * item.quantity for item in cart_items1)
    # Sort by date in descending order
    cart_items1.sort(key=lambda item: item.date, reverse=True)  

    # Manual pagination logic
    total_items = len(cart_items1)
    start = (page - 1) * per_page
    end = start + per_page
    cart_items = cart_items1[start:end]

    # ✅ Count the number of items in the cart
    cart_count = len(cart_items1) if cart_items else 0

    # Calculate total pages
    total_pages = (total_items // per_page) + (1 if total_items % per_page else 0)

    return render_template("cart.html", 
                           cart_items=cart_items, 
                           seller=seller,
                           seller_id=seller.id ,
                           page=page, 
                           total_pages=total_pages,
                           track_code= track_code,
                           cart_count=cart_count,
                           total_amount=total_amount,
                           shop_theme=seller.shop_theme
                           )



def get_cart_items_for_seller(user_id, seller_id):
    """Retrieve only cart items belonging to the current seller's store"""
    return CartItem.query.filter_by(user_id=user_id, seller_id=seller_id).all()




@app.route("/Cart_Item/<title>/<int:product_id>", methods=['GET', 'POST'])
@login_required
def Cart_product(product_id,title):
    product = Product.query.get_or_404(product_id)
    
    # Get the quantity safely (default to 1 if missing)
    quantity = request.form.get('quantity', type=int)
    if not quantity or quantity < 1:
        quantity = 1  # Ensure quantity is always at least 1

    existing_product = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()

    if existing_product:
        flash("Product already exists in the cart, please add a new product.", "success")
    else:
        cart_product = CartItem(
            user_id=current_user.id,
            product_id=product.id,
            seller_id=product.seller.id,
            quantity=quantity,
            amount=product.amount
        )
        db.session.add(cart_product)
        db.session.commit()
        print("Added to cart")
    if title=='shop':
        return redirect(url_for('shop2', shop_name=product.seller.slug1))
    else:
        return redirect(url_for('product_page', product_id=product.id,shop_name=product.seller.slug1))

@app.route("/delete_cart/<int:product_id>,<int:seller_id>", methods=['GET', 'POST'])
@login_required
def delete_cart_item(product_id,seller_id):
    cart_item=CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    db.session.delete(cart_item) 
    db.session.commit()
    return redirect(url_for('cart', seller_id=seller_id))


def generate_track_code():
    """Generate a unique 6-digit track code as a string"""
    while True:
        track_code = str(random.randint(100000, 999999))  # Convert to string immediately
        existing_order = Order.query.filter_by(track_code=track_code).first()

        if not existing_order:
            return track_code



@app.route("/checkout/<int:seller_id>/<string:track_code>", methods=['GET', 'POST'])
@login_required
def checkout(seller_id,track_code):
    """Process checkout for a specific seller"""
    seller = User.query.filter_by(id=seller_id).first_or_404()
    
    cart_items = get_cart_items_for_seller(current_user.id, seller_id)

    if not cart_items:
        flash("Your cart is empty for this seller.", "danger")
        return redirect(url_for('cart', seller_id=seller_id))
    
    #track_code = generate_track_code()
    # Calculate total amount
    total_amount = sum(item.product.amount * item.quantity for item in cart_items)
    #print(total_amount)
    # Create an order
    order = Order(user_id=current_user.id, seller_id=seller_id,total_amount=total_amount,track_code=track_code)
    db.session.add(order)
    db.session.commit()
    #print(order)
    notification=Notification(user_id=seller.id,content=f'{current_user.username} place an order with trackcode number: {track_code}',initiator=current_user.id,is_read=False)
    #print(notification)
    db.session.add(notification)
    db.session.commit

    # Move cart items to the order
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            amount=item.amount
        )
        db.session.add(order_item)
        print(order_item)
        db.session.delete(item)  # Remove item from cart
    
    db.session.commit()
   
    
    flash("Your order has been placed successfully!", "success")

    

    return redirect(url_for('shop2', shop_name=seller.slug1))

from urllib.parse import quote

@app.route("/send_order_whatsapp/<int:seller_id>/<string:track_code>")
@login_required
def send_order_whatsapp(seller_id, track_code):
    """Send a WhatsApp message to the seller with the order track code"""

    seller = User.query.filter_by(id=seller_id).first_or_404()
    phone_number = seller.phone_number  # Ensure this is in international format (e.g., +234XXXXXXXXXX)

    country_code = "234"  # Nigeria (+234), update if needed
    if not phone_number.startswith("+") and not phone_number.startswith(country_code):
        phone_number = country_code + phone_number.lstrip("0")

    # 📌 Predefined message
    message = f"Hello {seller.shop_name}, I just placed an order with Track Code: {track_code}. Please confirm and process my order. Thank you!"

    # ✅ Generate WhatsApp URL
    whatsapp_url = f"https://api.whatsapp.com/send?phone={phone_number}&text={quote(message)}"

    print("Redirecting to WhatsApp:", whatsapp_url)  # ✅ Debugging output

    return redirect(whatsapp_url)


@app.route("/Loved_items/place/order<int:seller_id>/<int:product_id>/<string:track_code>", methods=['GET', 'POST'])
@login_required
def checkout2(seller_id,product_id,track_code):
    """Process checkout for a specific seller"""
    seller = User.query.filter_by(id=seller_id).first_or_404()
    product=Product.query.filter_by(id=product_id).first()
    """Get quantity"""
    quantity = request.form.get('quantity', type=int)
    if not quantity or quantity < 1:
        quantity = 1  # Ensure quantity is always at least 1

    print(quantity)

    total_amount = (product.amount * quantity)
    # Create an order
    order = Order(user_id=current_user.id, seller_id=seller_id,total_amount=total_amount,track_code=track_code)
    db.session.add(order)
    db.session.commit()
    print(order)
    notification=Notification(user_id=seller.id,content=f'{current_user.username} place an order with trackcode number: {track_code}',initiator=current_user.id)
    #print(notification)
    db.session.add(notification)
    db.session.commit

    order_item = OrderItem(
        order_id=order.id,
        product_id=product_id,
        quantity=quantity,
        amount=product.amount
    )
    db.session.add(order_item)
    print(order_item)
    db.session.commit()

    
    
    flash("Your order has been placed successfully!", "success")
    return redirect(url_for('product_page_neutral', product_id=product.id,shop_name=seller.slug1,success="true"))









from flask import jsonify
from datetime import datetime
import calendar
from collections import defaultdict
import calendar

from sqlalchemy import func, extract




from sqlalchemy import func, extract
from collections import defaultdict

@app.route("/seller/orders")
@limiter.limit("10 per second")
@login_required
def seller_orders():
    """Display seller orders with pagination and analytics."""
    is_valid = check_subscription_status(current_user)
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Paginate orders
    pagination = (
        Order.query.filter_by(seller_id=current_user.id)
        .order_by(Order.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    orders = pagination.items

    # ✅ Total orders count (cheap)
    total_orders = db.session.query(func.count(Order.id)).filter_by(seller_id=current_user.id).scalar()

    # ✅ Total revenue (cheap)
    total_revenue_raw = db.session.query(func.sum(Order.total_amount)).filter_by(seller_id=current_user.id).scalar() or 0

    def format_number(value):
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.0f}k"
        return str(value)

    formatted_total_revenue = format_number(total_revenue_raw)

    # ✅ Get unique customer user IDs efficiently
    user_ids = [row[0] for row in db.session.query(Order.user_id)
                .filter_by(seller_id=current_user.id).distinct()]
    user_details = User.query.filter(User.id.in_(user_ids)).all()

    unique_customers = {
        user.id: {"name": user.username, "phone_number": user.phone_number}
        for user in user_details
    }
    total_customers = len(unique_customers)

    # ✅ Monthly revenue using GROUP BY SQL
    monthly_data = db.session.query(
        extract('month', Order.created_at).label('month'),
        func.sum(Order.total_amount)
    ).filter_by(seller_id=current_user.id).group_by('month').all()

    monthly_revenue = defaultdict(float)
    for month, amount in monthly_data:
        monthly_revenue[int(month)] = float(amount)

    sales_data = {
        "months": [calendar.month_abbr[m] for m in range(1, 13)],
        "revenue": [monthly_revenue[m] for m in range(1, 13)],
    }

    # ✅ Order status counts using GROUP BY SQL
    raw_status_data = db.session.query(
        Order.status, func.count(Order.id)
    ).filter_by(seller_id=current_user.id).group_by(Order.status).all()

    status_count = {"Pending": 0, "Shipped": 0, "Delivered": 0, "Cancelled": 0}
    for status, count in raw_status_data:
        if status in status_count:
            status_count[status] = count

    # ✅ Render and cache the page
    rendered = render_template(
        "seller_orders.html",
        orders=orders,
        pagination=pagination,
        total_orders=total_orders,
        total_revenue=formatted_total_revenue,
        total_customers=total_customers,
        unique_customers=unique_customers,
        sales_data=sales_data,
        status_data=status_count,
        shop_theme=current_user.shop_theme,
        is_valid=is_valid,
    )

    response = make_response(rendered)
    response.headers["Cache-Control"] = "public, max-age=300, s-maxage=600, stale-while-revalidate=900"
    return response










@app.route("/seller/order_items/<int:order_id>")
@login_required
def get_order_items(order_id):
    """Retrieve items for a specific order (AJAX request)"""
    order = Order.query.filter_by(id=order_id, seller_id=current_user.id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    #total_cost = sum(item.amount for item in order.order_items)  # ✅ Calculate total cost
    total_cost = order.total_amount

    return jsonify({
        "track_code": order.track_code,
        "total_cost": f"₦{total_cost:.2f}",  # ✅ Format total cost
        "items": [
            {
                "product_name": item.product.name,
                "quantity": item.quantity,
                "amount": f"₦{item.amount:.2f}",
                "product_image": url_for('static', filename=f'product_images/{item.product.image}')
            }
            for item in order.order_items
        ]
    })

@app.route("/buyer/orders")
@login_required
def buyer_orders():
    """Display paginated orders for the logged-in buyer"""
    
    # Get the current page number from the URL query string (?page=2), default to 1
    page = request.args.get('page', 1, type=int)
    
    # Query and paginate orders
    orders_paginated = (
        Order.query
        .filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .paginate(page=page, per_page=10)
    )

    return render_template(
        "buyer_orders.html",
        orders=orders_paginated.items,     # list of Order objects for this page
        pagination=orders_paginated,       # full pagination object for next/prev etc.
    )

@app.route("/buyer/order_items/<int:order_id>")
@login_required
def get_order_itemss(order_id):
    """Retrieve items for a specific order (AJAX request)"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    total_cost = order.total_amount  # ✅ Calculate total cost

    return jsonify({
        "track_code": order.track_code,
        "total_cost": f"₦{total_cost:.2f}",  # ✅ Format total cost
        "items": [
            {
                "product_name": item.product.name,
                "quantity": item.quantity,
                "amount": f"₦{item.amount:.2f}",
                "product_image": url_for('static', filename=f'product_images/{item.product.image}')
            }
            for item in order.order_items
        ]
    })







@app.route("/send_whatsapp/<string:phone_number>")
@login_required
def send_whatsapp(phone_number):
    """Generate WhatsApp link with a predefined message"""

    country_code = "234"  # Nigeria (+234) → Change if needed

    # Ensure the number is in international format
    if not phone_number.startswith("+") and not phone_number.startswith(country_code):
        phone_number = country_code + phone_number.lstrip("0")  # Remove leading '0'

    # ✅ Properly encode the message and URL
    store_url = f"http://127.0.0.1:5000/store/{current_user.username}"
    message = (
        f"Hello, this is {current_user.shop_name} Store From Vendera. "
        f"Wanted To Let You Know we have new stock for you to check out. "
        f"Visit our store today at {store_url}"
    )

    # ✅ Generate WhatsApp URL with proper encoding
    whatsapp_url = f"https://api.whatsapp.com/send?phone={phone_number}&text={quote(message)}"

    return redirect(whatsapp_url)

@app.route("/message_seller/<string:phone_number>")
@login_required
def notify_vendor(phone_number):
    """Generate WhatsApp link with a predefined message"""

    country_code = "234"  # Nigeria (+234) → Change if needed

    # Ensure the number is in international format
    if not phone_number.startswith("+") and not phone_number.startswith(country_code):
        phone_number = country_code + phone_number.lstrip("0")  # Remove leading '0'

    # ✅ Properly encode the message and URL
    message = f"Hello, this is {current_user.username}, i would like to...."
    

    # ✅ Generate WhatsApp URL with proper encoding
    whatsapp_url = f"https://api.whatsapp.com/send?phone={phone_number}&text={quote(message)}"

    return redirect(whatsapp_url)

@app.route("/update_order_status", methods=["POST"])
@login_required
def update_order_status():
    order_id = request.form.get("order_id")
    new_status = request.form.get("status")

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"success": False, "message": "Order not found"}), 404

    # Ensure only the seller/admin can update status
    if order.seller_id != current_user.id:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    order.status = new_status
    db.session.commit()

    # Return the updated status and badge color
    status_classes = {
        "Pending": "badge-warning",
        "Shipped": "badge-info",
        "Delivered": "badge-success",
        "Cancelled": "badge-danger"
    }
    return jsonify({
        "success": True,
        "message": "Order status updated successfully!",
        "new_status": new_status,
        "badge_class": status_classes.get(new_status, "badge-secondary")
    })

from sqlalchemy import and_

@app.route('/search_orders', methods=['GET'])
def search_orders():
    search_query = request.args.get('query', '').strip().lower()
    seller_id = current_user.id  # Get the logged-in seller's ID

    filtered_orders = Order.query.filter(
        and_(
            Order.seller_id == seller_id,  # Ensure seller_id matches
            Order.track_code.ilike(f"%{search_query}%")  # Search by track_code
        )
    ).order_by(Order.created_at.desc()).limit(10).all()

    # Convert orders to JSON
    orders_data = [
        {
            "id": order.id,
            "track_code": order.track_code,
            "buyer": order.user.username,
            "total_amount": order.total_amount,
            "status": order.status,
            "date" : order.created_at
        }
        for order in filtered_orders
    ]

    return jsonify(orders_data)



@app.route("/search_products", methods=["POST"])
def search_products():
    search_query = request.form.get("content", "").strip()
    user_id = request.form.get("user_id")
    page = int(request.form.get("page", 1))
    per_page = 1

    pagination = Product.query.filter(
        Product.name.ilike(f"%{search_query}%"),
        Product.user_id == user_id
    ).paginate(page=page, per_page=per_page, error_out=False)

    product_list = [
        {
            "id": product.id,
            "name": product.name,
            "amount": product.amount,
            "image": product.image,
            "description": product.description,
            "shop_slug": product.seller.slug1  # make sure relationship is set up
        }
        for product in pagination.items
    ]

    return jsonify({
        "products": product_list,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    })



from math import ceil

@app.route("/home/find_products", methods=["POST"])
def find_products():
    search_query = request.form.get("content")
    page = int(request.form.get("page", 1))  # Default to page 1
    per_page = 2  # Number of products per page

    products_query = Product.query.filter(
        Product.name.ilike(f"%{search_query}%")
    )

    paginated_products = products_query.paginate(page=page, per_page=per_page, error_out=False)

    product_list = [
        {
            "id": product.id,
            "name": product.name,
            "amount": product.amount,
            "image": product.image,
            "description": product.description,
            "shop_slug": product.seller.slug1
        }
        for product in paginated_products.items
    ]

    return jsonify({
        "products": product_list,
        "has_next": paginated_products.has_next,
        "has_prev": paginated_products.has_prev,
        "total_pages": paginated_products.pages,
        "current_page": paginated_products.page
    })



@app.route('/notification', methods=['GET', 'POST'])
@login_required
def notification():
    # Join Notification and User (as initiator) in a single query
    notifications = (
        db.session.query(Notification, User)
        .join(User, User.id == Notification.initiator)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.date.desc())
        .limit(10)
        .all()
    )

    # Mark all as read
    for notification, initiator in notifications:
        if not notification.is_read:
            notification.is_read = True

    db.session.commit()

    # Restructure for template
    enriched_notifications = [
        {
            'notification': notification,
            'initiator': initiator
        }
        for notification, initiator in notifications
    ]

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template(
        'notification.html',
        title='Notification',
        notifications=enriched_notifications,
        image_file=image_file,
        shop_theme=current_user.shop_theme
    )



@app.route('/pricing', methods=['GET', 'POST'])
def pricing():
    return render_template('pricing.html',title='pricing')

import requests
from datetime import datetime, timedelta

@app.route('/pay/<plan>', methods=['GET'])
@login_required
def pay(plan):
    PK_test_key=os.getenv("paystack_pk_test")
    print(PK_test_key)
    prices = {
        'free': 0,
        '1month': 1500,
        '3months': 4000,
        '6months': 8000
    }
    amount = prices.get(plan, 0)
    target_date = datetime(2025, 7, 11, 7, 7, 19, 960156)
    return render_template('payment.html', plan=plan, amount=amount,target_date=target_date,PK_test_key=PK_test_key)







@app.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    paystack_secret_key = os.getenv('paystack_secret_key')
    reference = request.form.get('reference')  # Get payment reference from the form
    
    # Make a request to Paystack to verify the payment
    headers = {
        'Authorization': f'Bearer {paystack_secret_key}',  # Replace with your Paystack Secret Key
    }
    response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)

    if response.status_code == 200:
        data = response.json()

        if data['data']['status'] == 'success':
            # Payment is successful, update the database
            user_email = data['data']['customer']['email']
            plan = data['data']['metadata']['custom_fields'][1]['value']  # Get the plan from metadata
            amount = data['data']['amount'] // 100  # Convert to Naira

            # Find the user
            user = User.query.filter_by(email=user_email).first()

            if user:
                # Default subscription_end to None for 'free' plan or ensure it's set for others
                subscription_end = None

                # Define a dictionary mapping plans to subscription durations in days
                plan_durations = {
                    'free': 30,
                    '1month': 30,
                    '3months': 90,
                    '6months': 180
                }

                # Get the current time (for '1month', '3months', and '6months' plans)
                current_time = datetime.utcnow()

                # Calculate subscription end date
                if plan in plan_durations:
                    if plan == 'free':
                        subscription_end = user.date + timedelta(days=plan_durations[plan])
                    else:
                        subscription_end = current_time + timedelta(days=plan_durations[plan])

                # Create a new subscription record
                new_subscription = Subscription(
                    user_id=user.id,
                    plan=plan,
                    amount=amount,
                    reference=reference,
                    end_date=subscription_end
                )

                db.session.add(new_subscription)

                # Update user's subscription status
                user.is_subscribed = True
                user.subscription_end = subscription_end
                db.session.commit()

                return redirect(url_for('shop2',shop_name=user.slug1))

            else:
                return "User not found!", 404
        else:
            return "Payment verification failed!", 400
    else:
        return "Error connecting to Paystack API", 500

def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for('reset_password', token=token, _external=True)

    msg = Message(
        subject='Password Reset Request',
        sender=app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )

    msg.html = render_template('reset_email_TP.html', user=user, reset_url=reset_url)

    try:
        mail.send(msg)
        print("✅ Email sent successfully")
    except (smtplib.SMTPException, socket.gaierror, socket.timeout, ConnectionRefusedError, OSError) as e:
        print("❌ Error sending email:", e)
        flash("We couldn't send the email. Please check your internet connection and try again.", "danger")


@app.route('/request_token', methods=['GET', 'POST'])
def request_reset_token():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RequestResetTokenForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            send_reset_email(user)
            flash("An email has been sent to you with instructions to follow.", 'info')
        else:
            flash("No account found with that email address.", 'warning')

        return redirect(url_for('login'))

    return render_template('request_reset_token.html', title='Reset Password', form=form)



@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    

    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('this is an invalid or incorrect token','warning')
        return redirect(url_for('request_reset_token'))

    form=ResetPasswordForm() 
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        #user=User(username=form.username.data,email=form.email.data,password=hashed_password)
        user.password=hashed_password
        db.session.commit()
        flash(f"You password has been update!, please procceed to login😊", 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html',title='Reset_password',form=form)

@app.route('/sendmail')
def test_email():
    from flask_mail import Message

    msg = Message(
        subject='✅ Flask Mail Test',
        sender=app.config['MAIL_USERNAME'],
        recipients=['dibieemmanuel6@gmail.com']  # replace with your email to test
    )
    msg.body = '🎉 If you received this email, Flask-Mail is working correctly!'

    try:
        mail.send(msg)
        return '<h2>Email sent successfully ✅</h2>'
    except Exception as e:
        return f'<h2>Error sending email ❌</h2><pre>{e}</pre>'








@app.route('/personal_info', methods=['GET', 'POST'])
@login_required
def personal_info():
    form = PersonalInfoForm()
    user = current_user
    show_verification = False
    cooldown_remaining = 0

    if request.method == 'POST':
        if 'verify_email' in request.form:
            # Check if a code was sent recently (within 5 mins)
            last_sent = session.get('code_sent_time')
            if last_sent:
                elapsed = (datetime.utcnow() - datetime.fromisoformat(last_sent)).total_seconds()
                if elapsed < 300:
                    cooldown_remaining = int(300 - elapsed)
                    flash(f"Please wait {cooldown_remaining} seconds before resending the code.", "warning")
                    show_verification = True
                    return render_template("personal_info.html", form=form, show_verification=show_verification, cooldown=cooldown_remaining,shop_theme=current_user.shop_theme)

            # Generate and store the verification code
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            session['verification_code'] = code
            session['code_sent_time'] = datetime.utcnow().isoformat()

            # Send the code to email
            try:
                msg = Message("Your Verification Code", sender=app.config['MAIL_USERNAME'], recipients=[user.email])
                msg.body = f"Your 6-digit code is: {code}. This code will expire in 5 minutes."
                mail.send(msg)

                flash("A 6-digit code has been sent to your email.", "info")
                show_verification = True
                cooldown_remaining = 300
            except (smtplib.SMTPException, socket.gaierror, socket.timeout, ConnectionRefusedError, OSError) as e:
                print("❌ Error sending email:", e)
                flash("We couldn't send the email. Please check your internet connection and try again.", "danger")
            return render_template("personal_info.html", form=form, show_verification=show_verification, cooldown=cooldown_remaining,shop_theme=current_user.shop_theme)

        if form.validate_on_submit():
            code_entered = form.email_code.data
            code_stored = session.get('verification_code')
            code_sent_time = session.get('code_sent_time')

            # Debug: Print the sent code and the entered code
            print(f"Code sent: {code_stored}")
            print(f"Code entered: {code_entered}")

            if not code_stored or not code_sent_time:
                flash("You must verify your email first!", "danger")
                return render_template("personal_info.html", form=form, show_verification=True,shop_theme=current_user.shop_theme)

            # Check if the code has expired
            time_diff = datetime.utcnow() - datetime.fromisoformat(code_sent_time)
            if time_diff.total_seconds() > 300:
                flash("Verification code expired. Please request a new one.", "danger")
                return render_template("personal_info.html", form=form, show_verification=True,shop_theme=current_user.shop_theme)

            # Check if the entered code matches the stored code
            if code_entered != code_stored:
                flash("Incorrect verification code.", "danger")
                return render_template("personal_info.html", form=form, show_verification=True,shop_theme=current_user.shop_theme)

            # Save the personal info
            existing_info = PersonalInfo.query.filter_by(user_id=current_user.id).first()
            if existing_info:
                existing_info.first_name = form.first_name.data
                existing_info.last_name = form.last_name.data
                existing_info.country = form.country.data
                existing_info.state = form.state.data
                existing_info.address = form.address.data
                existing_info.day_of_birth = form.day_of_birth.data
                existing_info.month_of_birth = form.month_of_birth.data
                existing_info.year_of_birth = form.year_of_birth.data
            else:
                new_info = PersonalInfo(
                    user_id=current_user.id,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    country=form.country.data,
                    state=form.state.data,
                    address=form.address.data,
                    day_of_birth=form.day_of_birth.data,
                    month_of_birth=form.month_of_birth.data,
                    year_of_birth=form.year_of_birth.data
                )
                db.session.add(new_info)

            db.session.commit()
            current_user.is_verified = True
            db.session.commit()

            flash("Personal info saved successfully! You are now verified.", "success")
            return redirect(url_for('shop2', shop_name=current_user.slug1,shop_theme=current_user.shop_theme))

    elif request.method == 'GET':
        existing_info = PersonalInfo.query.filter_by(user_id=current_user.id).first()
        if existing_info:
            form.first_name.data = existing_info.first_name
            form.last_name.data = existing_info.last_name
            form.country.data = existing_info.country
            form.state.data = existing_info.state
            form.address.data = existing_info.address
            form.day_of_birth.data = existing_info.day_of_birth
            form.month_of_birth.data = existing_info.month_of_birth
            form.year_of_birth.data = existing_info.year_of_birth

        # Check for cooldown if page refreshed
        last_sent = session.get('code_sent_time')
        if last_sent:
            elapsed = (datetime.utcnow() - datetime.fromisoformat(last_sent)).total_seconds()
            if elapsed < 300:
                cooldown_remaining = int(300 - elapsed)

    return render_template("personal_info.html", form=form, show_verification=show_verification, cooldown=cooldown_remaining,shop_theme=current_user.shop_theme)





@app.route('/top-sellers')
def top_sellers():
    range_filter = request.args.get('range', 'overall')
    now = datetime.utcnow()

    # Define date filter for non-overall
    if range_filter == 'day':
        start_date = now.date()
    elif range_filter == 'week':
        start_date = now - timedelta(days=now.weekday())
    elif range_filter == 'month':
        start_date = now.replace(day=1)
    else:
        start_date = None

    if range_filter == 'overall':
        visit_subquery = db.session.query(
            StoreVisit.seller_id,
            func.count(StoreVisit.id).label('visit_count')
        ).group_by(StoreVisit.seller_id).subquery()

        order_subquery = db.session.query(
            Order.seller_id,
            func.count(Order.id).label('order_count'),
            func.coalesce(func.sum(Order.total_amount), 0).label('total_sales'),
            func.count(func.distinct(Order.user_id)).label('customer_count')
        ).group_by(Order.seller_id).subquery()

        VISIT_WEIGHT = 0.25
        ORDER_WEIGHT = 0.25
        SALES_WEIGHT = 0.3
        CUSTOMER_WEIGHT = 0.2

        query = db.session.query(
            User,
            func.coalesce(visit_subquery.c.visit_count, 0).label('visit_count'),
            func.coalesce(order_subquery.c.order_count, 0).label('order_count'),
            func.coalesce(order_subquery.c.total_sales, 0).label('total_sales'),
            func.coalesce(order_subquery.c.customer_count, 0).label('customer_count'),
            (
                VISIT_WEIGHT * func.coalesce(visit_subquery.c.visit_count, 0) +
                ORDER_WEIGHT * func.coalesce(order_subquery.c.order_count, 0) +
                SALES_WEIGHT * func.coalesce(order_subquery.c.total_sales, 0) +
                CUSTOMER_WEIGHT * func.coalesce(order_subquery.c.customer_count, 0)
            ).label('score')
        ).outerjoin(visit_subquery, User.id == visit_subquery.c.seller_id
        ).outerjoin(order_subquery, User.id == order_subquery.c.seller_id
        ).filter(
            User.shop_name.isnot(None),
            User.is_verified == True
        ).order_by(desc('score'))

    else:
        order_subquery = db.session.query(
            Order.seller_id,
            func.count(Order.id).label('order_count'),
            func.coalesce(func.sum(Order.total_amount), 0).label('total_sales')
        ).filter(Order.created_at >= start_date
        ).group_by(Order.seller_id).subquery()

        query = db.session.query(
            User,
            func.coalesce(order_subquery.c.order_count, 0).label('order_count'),
            func.coalesce(order_subquery.c.total_sales, 0).label('total_sales')
        ).outerjoin(order_subquery, User.id == order_subquery.c.seller_id
        ).filter(
            User.shop_name.isnot(None),
            User.is_verified == True
        ).order_by(
            desc('order_count'),
            desc('total_sales')
        )

    sellers = query.limit(10).all()
    rendered = render_template('top_sellers.html', sellers=sellers, selected_range=range_filter)

    # ✅ Apply Vercel Edge Caching (5 min public cache)
    response = make_response(rendered)
    response.headers['Cache-Control'] = 'public, max-age=300, s-maxage=600, stale-while-revalidate=900'
    return response




