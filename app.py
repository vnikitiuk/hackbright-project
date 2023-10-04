import os

from flask import Flask, render_template, redirect, flash, request, session, jsonify
import crud
from helper import usd, login_required
from model import connect_to_db, db
from flask_sqlalchemy import SQLAlchemy
import yfinance as yf
from werkzeug.security import check_password_hash, generate_password_hash
import decimal
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "dev"

# Custom filter
app.jinja_env.filters["usd"] = usd

@app.route('/')
@login_required
def homepage():

    # Cheking for cash amount
    user_cash = float(crud.get_user_cash(session["user_id"]))
    # Query database for transaction information
    transactions = crud.get_all_transactions(session["user_id"])
    total_sum = 0
    purchases = {}

    # Creating new dict to update home page with fresh information, stok's names and count availabel stocks
    for transaction in transactions:
        symbol = transaction.stock_symbol
        stock_info = yf.Ticker(symbol)

        if symbol in purchases:
            purchase = purchases[symbol]
            if transaction.transaction_type == "buy":
                purchase["shares"] += transaction.stock_count
            else: 
                purchase["shares"] -= transaction.stock_count

        else:
            purchase = {}
            purchase["symbol"] = symbol
            purchase["name"] = stock_info.info["longName"] 
            purchase["price"] = stock_info.info["currentPrice"]
            
            if transaction.transaction_type == "buy":
                purchase["shares"] = transaction.stock_count
            else: 
                purchase["shares"] = -transaction.stock_count

            purchases[symbol] = purchase

    # Counting the profit
    for purchase in purchases.values():
        purchase["total"] = float(purchase["shares"]) * float(purchase["price"])
        total_sum += purchase["total"]

    total_sum += user_cash

    return render_template('index.html', total_sum=total_sum, user_cash=user_cash, purchases=purchases)

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Query database for transaction data
    transactions = crud.get_all_transactions(session["user_id"])

    return render_template("history.html", transactions=transactions)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol was submitted
        symbol = request.form.get("symbol")
        if not symbol:
            return flash("must provide symbol", 400)

        # Ensure positiv number was submitted
        if not request.form.get("shares").replace(".", "", 1).isdigit() or float(request.form.get("shares")) <= 0:
            return flash("must provide positiv number", 400)

        count_of_shares = float(request.form.get("shares"))
        current_stock_price = yf.Ticker(symbol).info["currentPrice"]

        # Ensure user has enough money to buy stocks
        user_cash = float(crud.get_user_cash(session["user_id"]))
        # print(type(current_stock_price))
        # print(type(count_of_shares))
        # print(type(user_cash))
        if (current_stock_price * count_of_shares) > user_cash:
            return flash("You have not enough money for transaction")

        # Remember stock's symbol, user id, stock's count, stock's price, stock's name, type(sell/buy)
        transaction_buy = crud.create_transaction_info(session["user_id"], symbol, count_of_shares, current_stock_price, "buy")
        db.session.add(transaction_buy)

        # Update cash in users table
        user_cash -= current_stock_price * count_of_shares
        crud.update_user_cash(user_cash, session["user_id"])
        db.session.commit()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for transaction data
        transactions = crud.get_all_transactions(session["user_id"])

        # Ensure user has right amount stoks to sell
        count_of_shares_to_sell = float(request.form.get("shares"))
        count_of_available_stocks = 0
        symbol = request.form.get("symbol")

        for transaction in transactions:
            if transaction.stock_symbol == symbol:
                if transaction.transaction_type == "buy":
                    count_of_available_stocks += transaction.stock_count
                else:
                    count_of_available_stocks -= transaction.stock_count

        if count_of_shares_to_sell > count_of_available_stocks:
            return "Check how many stoks to sell is available in $Finance", 400


        # Update cash in users table
        user_cash = crud.get_user_cash(session["user_id"])
        current_stock_price = yf.Ticker(symbol).info["currentPrice"]
        new_amount = float(user_cash) + (current_stock_price * float(count_of_shares_to_sell))
        crud.update_user_cash(new_amount, session["user_id"])
        db.session.commit()

        # Remember stock's symbol, user id, stock's count, stock's price, stock's name, type(sell/buy)
        transaction_sell = crud.create_transaction_info(session["user_id"], symbol, count_of_shares_to_sell, current_stock_price, "sell")
        db.session.add(transaction_sell)
        db.session.commit()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("sell.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        user = crud.get_user_by_name(username)

        # Ensure username exists and password is correct
        if not user or not check_password_hash(user.password_hash, password):
            flash("The username or password you entered was incorrect.")
        else:
            # Log in user by storing the user's username in session
            session["username"] = user.username
            session["user_id"]  = user.user_id
            flash(f"Welcome back, {username}!")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        name = request.form.get("username")
        if not name or len(crud.get_all_users_by_name(name)) > 0:
            return flash("must provide username or such username exist")

        # Ensure password has 8 symbols
        password = request.form.get("password")
        if len(password) < 8:
            return flash("Password must be 8 or more symbols")

        # Ensure password was confirmed
        elif password != request.form.get("confirmation"):
            return flash("confimation must match the password")

        # Ensure password include numbers, lowercase and uppercase characters
        no_lower = True
        no_upper = True
        no_digit = True

        for symbol in password:
            if symbol.islower():
                no_lower = False
            elif symbol.isupper():
                no_upper = False
            elif symbol.isdigit():
                no_digit = False

        if no_lower or no_upper or no_digit:
            return flash("Password must include numbers, lowercase and uppercase characters")

        # Remember registrant
        if name == crud.get_all_users_by_name(name):
            flash("Cannot create an account with that name. Try again.")
        else:
            user = crud.create_user(name, generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("Account created! Please log in.")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/quote")
@login_required
def quote():
    return render_template("quote.html")

@app.route("/quote.json")
@login_required
def stock_info():

    symbol = request.args.get("symbol")
    stock_info = yf.Ticker(symbol)
    hist = stock_info.history(period="1y")
    chart_info = []
    for index, row in hist.iterrows():
        chart_info.append({"time" : index.strftime('%Y-%m-%d'), 
                           "close_price" : row['Close']})

    name = stock_info.info["longName"]
    price = stock_info.info["currentPrice"]
    stock = {"symbol" : symbol, "name" : name, "price" : price, "chart_info" : chart_info}
    return jsonify(stock)

if __name__ == "__main__":
    connect_to_db(app)
    app.run(host="0.0.0.0", debug=True)