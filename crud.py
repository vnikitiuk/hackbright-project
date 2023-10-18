from model import connect_to_db, db, Transaction, User

def get_user_by_name(name):
    return User.query.filter_by(username=name).first()

def get_all_users_by_name(name):
    return User.query.filter_by(username=name).all()

def get_all_transactions(id):
    return Transaction.query.filter_by(user_id = id).all()

def create_user(name, password):
    return User(username=name, password_hash=password)

def get_user_cash(id):
    return User.query.filter_by(user_id=id).first().cash_amount

def update_user_cash(new_amount, user_id):
    User.query.filter_by(user_id=user_id).first().cash_amount = new_amount

def create_transaction_info(user_id, stock_symbol, stock_count, stock_price, transaction_type):

    transaction = Transaction(
        user_id = user_id,
        stock_symbol = stock_symbol,
        stock_count = stock_count,
        stock_price = stock_price,
        transaction_type = transaction_type,
    )

    return transaction
