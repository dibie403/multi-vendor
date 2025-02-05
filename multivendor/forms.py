from flask_wtf import FlaskForm
from flask_wtf.file import FileField,FileAllowed
from wtforms import StringField,PasswordField,SubmitField,BooleanField,TextAreaField
from wtforms.validators import DataRequired,Length,Email,EqualTo,ValidationError


class RegistrationForm(FlaskForm):
	username=StringField('Username', validators=[DataRequired(),Length(min=2,max=20)])
	email=StringField('Email',validators=[DataRequired(),Email()])
	password=PasswordField('Password', validators=[DataRequired()])
	confirm_password=PasswordField('Comfirm Password',validators=[DataRequired(),EqualTo('password')])
	submit=SubmitField('Sign up')

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