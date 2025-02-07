from flask_wtf import FlaskForm
from flask_wtf.file import FileField,FileAllowed
from wtforms import StringField,PasswordField,SubmitField,BooleanField,TextAreaField,SelectField
from wtforms.validators import DataRequired,Length,Email,EqualTo,ValidationError,Optional
from multivendor.models import User



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
		
	

class LoginForm(FlaskForm):
	email=StringField('Email',validators=[DataRequired(),Email()])
	password=PasswordField('Password', validators=[DataRequired()])
	remember=BooleanField('Remember me')
	submit=SubmitField('Log in')