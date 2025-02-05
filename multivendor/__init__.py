import os
from flask import Flask

app = Flask(__name__)
# Application secret key
app.config['SECRET_KEY']= os.getenv("Secret_key")

from multivendor import routes  
