from flask_wtf import FlaskForm
from flask_wtf.file import FileField,FileAllowed
from wtforms import StringField,PasswordField,SubmitField,BooleanField,TextAreaField,SelectField
from wtforms.validators import DataRequired,Length,Email,EqualTo,ValidationError,Optional
from multivendor.models import User
from flask_login import current_user



class RegistrationForm(FlaskForm):
		username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
		email = StringField('Email', validators=[DataRequired(), Email()])
		phone = StringField('Phone Number', validators=[DataRequired()])
		password = PasswordField('Password', validators=[DataRequired()])
		confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
		status = SelectField('Register As', choices=[('buyer', 'Buyer'), ('seller', 'Seller')], validators=[DataRequired()])

		# Shop Fields (optional for buyers)
		shop_name = StringField('Shop Name', validators=[Optional(), Length(max=20)])
		shop_motto = TextAreaField('Shop Motto', validators=[Optional()])

		submit = SubmitField('Sign Up')

		#function to handle wether the user alredy exist in the database.
		def validate_username(self,username):
			user=User.query.filter_by(username=username.data).first()

			if user:
				raise ValidationError('Username already taken,Please pick a unique username')

		def validate_email(self,email):
			user=User.query.filter_by(email=email.data).first()

			if user:
				raise ValidationError('Email already Exist,Please use a unique Email')
		def validate_phone(self,phone):
			user=User.query.filter_by(username=phone.data).first()

			if user:
				raise ValidationError('Phone number already taken,Please pick a unique phone number')

		def validate_shop(self,shop_name):
			user=User.query.filter_by(username=show_name.data).first()

			if user:
				raise ValidationError('Shop name already taken,Please pick a unique shop name')

		def validate_shopMotor(self,shop_motto):
			user=User.query.filter_by(username=shop_motto.data).first()

			if user:
				raise ValidationError('Brand slogan already taken,Please pick a unique slogan')


class LoginForm(FlaskForm):
	email=StringField('Email',validators=[DataRequired(),Email()])
	password=PasswordField('Password', validators=[DataRequired()])
	remember=BooleanField('Remember me')
	submit=SubmitField('Log in')


class UpdateProfileForm(FlaskForm):
		username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
		email = StringField('Email', validators=[DataRequired(), Email()])
		phone = StringField('Phone Number', validators=[DataRequired()])
		status = SelectField('Register As', choices=[('True', 'Seller'), ('False', 'Buyer')], validators=[DataRequired()])
		picture=FileField('Update Profile Picture',validators=[FileAllowed(['jpg','png'])])
		submit=SubmitField('Update')


		def validate_username(self,username):
			if username.data != current_user.username:
				user=User.query.filter_by(username=username.data).first()

				if user:
					raise ValidationError('Username already taken,Please pick a unique username')

		def validate_email(self,email):
			if email.data != current_user.email:
				user=User.query.filter_by(email=email.data).first()

				if user:
				   raise ValidationError('Email already Exist,Please use a unique Email')

		def validate_phone(self,phone):
			if phone.data != current_user.phone_number:
				user=User.query.filter_by(phone_number=phone.data).first()

				if user:
				   raise ValidationError('phone number already Exist,Please use a unique Email')

		

class AddProductForm(FlaskForm):
    # Product Name
    name = StringField(
        'Product Name', 
        validators=[DataRequired(), Length(min=3, max=20)]
    )

    # Description
    description = TextAreaField(
        'Description', 
        validators=[DataRequired()]
    )

    # Amount
    amount = StringField(
        'Amount', 
        validators=[DataRequired(), Length(min=3, max=20)]
    )

    # Category Dropdown
    category = SelectField(
        'Category', 
        choices=[
            ('shoes', 'Shoes'), 
            ('clothes', 'Clothes'), 
            ('perfume', 'Perfume'), 
            ('electronics', 'Electronics'), 
            ('books', 'Books'), 
            ('phones', 'Phones'),
            ('laptops', 'Laptops'),
            ('home_appliances', 'Home Appliances'),
            ('beauty', 'Beauty & Personal Care'),
            ('health', 'Health & Wellness'),
            ('sports', 'Sports & Outdoors'),
            ('toys', 'Toys & Games'),
            ('automotive', 'Automotive'),
            ('furniture', 'Furniture'),
            ('groceries', 'Groceries'),
            ('watches', 'Watches & Accessories'),
            ('jewelry', 'Jewelry'),
            ('handbags', 'Handbags & Accessories'),
            ('gaming', 'Gaming & Consoles'),
            ('office_supplies', 'Office Supplies'),
            ('others', 'Others')
        ],
        validators=[DataRequired()]
    )

    # Shelf Dropdown
    shelf = SelectField(
        'Shelf', 
        choices=[
            ('featured', 'Featured'), 
            ('top_sales', 'Top Sales'), 
            ('best_selling', 'Best Selling')
        ],
        validators=[DataRequired()]
    )

    # Product Image Upload
    picture = FileField(
        'Add Product Image', 
        validators=[FileAllowed(['jpg', 'png'])]
    )

    # Submit Button
    submit = SubmitField('Update')


class UpdateshopForm(FlaskForm):
		# Shop Fields (optional for buyers)
		shop_name = StringField('Shop Name', validators=[DataRequired(), Length(max=20)])
		shop_motto = TextAreaField('Shop Motto', validators=[DataRequired()])
		shop_about=TextAreaField('About Your Store', validators=[DataRequired()])
		picture=FileField('Update Profile Picture',validators=[FileAllowed(['jpg','png'])])
		submit = SubmitField('Sign Up')

		#function to handle wether the user alredy exist in the database

		def validate_shop(self,shop_name):
			user=User.query.filter_by(username=show_name.data).first()

			if user:
				raise ValidationError('Shop name already taken,Please pick a unique shop name')

		def validate_shopMotor(self,shop_motto):
			user=User.query.filter_by(username=shop_motto.data).first()

			if user:
				raise ValidationError('Brand slogan already taken,Please pick a unique slogan')

