import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime

db = SQLAlchemy()

class User(db.Model):
    
    __tablename__ = "users"
    
    user_id = db.Column(db.Integer,
                        autoincrement=True,
                        primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password_hash = db.Column(db.String, nullable=False)
    cash_amount = db.Column(db.Integer, default=10000)
    
    transactions = db.relationship("Transaction", back_populates="user")
    
    def __repr__(self):
        return f"<User user_id={self.user_id} username={self.username}>"


class Transaction(db.Model):
    __tablename__ = "transactions"

    transaction_id = db.Column(db.Integer,
                               autoincrement=True,
                               primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    stock_symbol = db.Column(db.String, nullable=False)
    stock_count = db.Column(db.Integer, nullable=False)
    stock_price = db.Column(db.Integer, nullable=False)
    transaction_time = db.Column(DateTime, default=datetime.datetime.utcnow)
    transaction_type = db.Column(db.String, nullable=False)

    user = db.relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction transaction_id={self.transaction_id} stock_symbol={self.stock_symbol}>"
    

def connect_to_db(flask_app, db_uri="postgresql:///stocks", echo=True):
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    flask_app.config["SQLALCHEMY_ECHO"] = echo
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.app = flask_app
    db.init_app(flask_app)

    print("Connected to the db!")

print(__name__)

if __name__ == "__main__":
    from server import app

    # Call connect_to_db(app, echo=False) if your program output gets
    # too annoying; this will tell SQLAlchemy not to print out every
    # query it executes.

    connect_to_db(app)