from flask import render_template, url_for, flash, redirect, request
from multivendor import app
from multivendor.forms import RegistrationForm

@app.route("/")
@app.route("/home")
def home():

    return render_template('home.html',title='home')


@app.route("/register")
def register():
    form=RegistrationForm()

    return render_template('login.html',title='register',form=form)


