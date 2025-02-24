from multivendor import app
import os



if __name__ == '__main__':
    app.run(debug=True)

from multivendor import app,db
from multivendor.models import User,Product

with app.app_context():
    users=User.query.all()
    print(users)