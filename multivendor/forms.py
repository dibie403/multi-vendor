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
		status = SelectField('Register As', choices=[('buyer', 'Buyer'), ('seller', 'Seller')], validators=[DataRequired()])
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

		
