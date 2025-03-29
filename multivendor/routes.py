
import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify
from multivendor import app,db,bcrypt
from flask_login import login_user,current_user,logout_user,login_required
from multivendor.forms import RegistrationForm,LoginForm,UpdateProfileForm,AddProductForm,UpdateshopForm,EditProductForm
from multivendor.models import User,Product,Love,CartItem,OrderItem,Order
import re
from datetime import datetime
import random
from urllib.parse import quote





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
    product=Product.query.filter_by(user_id=user.id).first()
    products=Product.query.filter_by(user_id=user.id).order_by(Product.date.desc()).paginate(page=page, per_page=2)
    seller_id=product.user_id if product else None
    cart_items = get_cart_items_for_seller(current_user.id, seller_id)
    cart_count = len(cart_items) if cart_items else 0
    loved_products = {love.product_id for love in Love.query.filter_by(user_id=current_user.id).all()}
    
    print(user.shop_image_file)

    return render_template('shop.html',title='shop',image_file=image_file,products=products,user=user,loved_products=loved_products,product=product,cart_count=cart_count,shop_theme="white")


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
def product_page(product_id, username):
    """Display product details and retrieve the last track code from session"""

    product = Product.query.filter_by(id=product_id).first_or_404()
    seller_id = product.user_id if product else None
    cart_items = get_cart_items_for_seller(current_user.id, seller_id)
    
    # ✅ Count the number of items in the cart
    cart_count = len(cart_items) if cart_items else 0

    track_code = generate_track_code()

    return render_template(
        'product_view.html', 
        product=product, 
        cart_count=cart_count, 
        track_code=track_code, 
        seller_id=seller_id, 
        shop_theme='white'
    )



@app.route("/Product-View/<username>/<int:product_id>", methods=['GET', 'POST'])
@login_required
def product_page_neutral(product_id,username):
    product=Product.query.filter_by(id=product_id).first_or_404()
    seller_id=product.user_id if product else None

    track_code = generate_track_code()
    
    return render_template('product_view2Neutral.html',product=product,shop_theme='white',track_code=track_code,seller_id=seller_id)

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
    return redirect(url_for('shop2', username=current_user.slug))

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

@app.route("/cart/<seller_id>")
def cart(seller_id):
    """Show cart items only for the current store's seller"""
    page = request.args.get('page', 1, type=int)
    per_page = 1  # Number of items per page

    seller = User.query.filter_by(id=seller_id).first_or_404()
    cart_items1 = get_cart_items_for_seller(current_user.id, seller.id)  # This returns a list

    # Sort by date in descending order
    cart_items1.sort(key=lambda item: item.date, reverse=True)  

    # Manual pagination logic
    total_items = len(cart_items1)
    start = (page - 1) * per_page
    end = start + per_page
    cart_items = cart_items1[start:end]

    # Calculate total pages
    total_pages = (total_items // per_page) + (1 if total_items % per_page else 0)

    return render_template("cart.html", 
                           cart_items=cart_items, 
                           seller=seller, 
                           page=page, 
                           total_pages=total_pages)



def get_cart_items_for_seller(user_id, seller_id):
    """Retrieve only cart items belonging to the current seller's store"""
    return CartItem.query.filter_by(user_id=user_id, seller_id=seller_id).all()




@app.route("/Cart_Item/<int:product_id>", methods=['GET', 'POST'])
@login_required
def Cart_product(product_id):
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

    return redirect(url_for('product_page', product_id=product.id, username=product.seller.slug))

@app.route("/delete_cart/<int:product_id>,<int:seller_id>", methods=['GET', 'POST'])
@login_required
def delete_cart_item(product_id,seller_id):
    cart_item=CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    db.session.delete(cart_item) 
    db.session.commit()
    return redirect(url_for('cart', seller_id=seller_id))


def generate_track_code():
    """Generate a unique 6-digit track code"""
    while True:
        track_code = random.randint(100000, 999999)  # Generate a 6-digit number
        existing_order = Order.query.filter_by(track_code=track_code).first()

        if not existing_order:
            return track_code  # Ensure uniqueness


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
    print(total_amount)
    # Create an order
    order = Order(user_id=current_user.id, seller_id=seller_id,total_amount=total_amount,track_code=track_code)
    db.session.add(order)
    db.session.commit()
    print(order)

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
    

    return redirect(url_for('shop2', username=seller.slug,track_code=track_code))

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


@app.route("/Loved_items/place/order<int:seller_id>,<int:product_id>,<string:track_code>", methods=['GET', 'POST'])
@login_required
def checkout2(seller_id,product_id,track_code):
    """Process checkout for a specific seller"""
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
    return redirect(url_for('Loved_items'))








from flask import jsonify
from datetime import datetime
import calendar
from collections import defaultdict
import calendar

@app.route("/seller/orders")
@login_required
def seller_orders():
    """Display only the last 10 orders but calculate analytics from all orders"""

    # 📌 Fetch the last 10 orders for display
    orders = (
        Order.query.filter_by(seller_id=current_user.id)
        .order_by(Order.created_at.desc())
        .limit(10)  # ✅ Only get the latest 10 orders
        .all()
    )

    # 📌 Fetch **all** orders for accurate analytics
    all_orders = Order.query.filter_by(seller_id=current_user.id).all()

    # ✅ Get total orders count
    total_orders = len(all_orders)

    # ✅ Calculate total revenue from all orders
    total_revenue = sum(order.total_amount for order in all_orders)

    # ✅ Format the total revenue in 'K' (thousands) or 'M' (millions) format
    def format_number(value):
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"  # Example: 2,500,000 → 2.5M
        elif value >= 1_000:
            return f"{value / 1_000:.0f}k"  # Example: 215,000 → 215k
        return str(value)  # No formatting for small numbers

    # ✅ Apply formatting
    formatted_total_revenue = format_number(total_revenue)

    # ✅ Extract unique customers from all orders
    unique_customers = {}
    for order in all_orders:
        if order.user_id not in unique_customers:
            unique_customers[order.user_id] = {
                "name": order.user.username,  # Assuming a `name` field in the User model
                "phone_number": order.user.phone_number,  # Assuming phone number exists
            }

    total_customers = len(unique_customers)  # ✅ Get count of unique customers

    # ✅ Initialize monthly revenue dictionary
    monthly_revenue = defaultdict(float)
    for order in all_orders:  # ✅ Loop through all orders
        order_month = order.created_at.month
        monthly_revenue[order_month] += order.total_amount

    # ✅ Prepare data for Chart.js
    sales_data = {
        "months": [calendar.month_abbr[m] for m in range(1, 13)],  # ['Jan', 'Feb', ..., 'Dec']
        "revenue": [monthly_revenue[m] for m in range(1, 13)],  # ✅ Correct revenue for each month
    }

    # 📌 Order Status Data for Pie Chart
    status_count = {"Pending": 0, "Shipped": 0, "Delivered": 0,"Cancelled":0}
    for order in all_orders:
        if order.status in status_count:
            status_count[order.status] += 1

    return render_template(
        "seller_orders.html",
        orders=orders,
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_customers=total_customers,
        unique_customers=unique_customers,  # ✅ Pass unique customers to the template
        sales_data=sales_data,
        status_data=status_count,
        shop_theme='white'
    )


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
        "total_cost": f"${total_cost:.2f}",  # ✅ Format total cost
        "items": [
            {
                "product_name": item.product.name,
                "quantity": item.quantity,
                "amount": f"${item.amount:.2f}",
                "product_image": url_for('static', filename=f'product_images/{item.product.image}')
            }
            for item in order.order_items
        ]
    })

@app.route("/buyer/orders")
@login_required
def buyer_orders():
    
    """Display all orders for the logged-in buyer"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()

    return render_template("buyer_orders.html", orders=orders)

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
        "total_cost": f"${total_cost:.2f}",  # ✅ Format total cost
        "items": [
            {
                "product_name": item.product.name,
                "quantity": item.quantity,
                "amount": f"${item.amount:.2f}",
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
            "status": order.status
        }
        for order in filtered_orders
    ]

    return jsonify(orders_data)

@app.route("/search_products", methods=["POST"])
def search_products():
    search_query = request.form.get("content")
    user_id = request.form.get("user_id")  # Ensure you get the correct user ID

    products = Product.query.filter(
        Product.name.ilike(f"%{search_query}%"),
        Product.user_id == user_id
    ).all()

    product_list = [
        {
            "id": product.id,
            "name": product.name,
            "amount": product.amount,
            "image": product.image,
            "description":product.description
        }
        for product in products
    ]

    return jsonify(product_list)


