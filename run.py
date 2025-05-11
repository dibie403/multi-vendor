from multivendor import app, db
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError




if __name__ == '__main__':
    app.run(debug=True)

from multivendor.models import User
with app.app_context():
    try:
        users = User.query.all()
        for user in users:
            print(user)
    except SQLAlchemyError as e:
        print("Database error:", e)

  
    

