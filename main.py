import json
from flask import Flask, render_template, redirect, flash, url_for, request
from flask_bootstrap import Bootstrap
from forms import LoginForm, RegisterForm, BuyForm, SellForm, ChangePassword, FindFriend
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
import os
import requests
from random import shuffle


app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


gravatar = Gravatar(app, size=30, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)


class User(UserMixin, db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    follow_stocks = relationship('FollowingStock', back_populates='owner')
    funds = db.Column(db.Float)
    stocks = relationship('OwnershipStock', back_populates='owner')
    history = relationship('History', back_populates='person')
    friends = relationship('Friends', back_populates='person')


class FollowingStock(db.Model):
    __tablename__ = "StocksFollowing"
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    owner = relationship("User", back_populates="follow_stocks")
    stock_name = db.Column(db.String(250))


class OwnershipStock(db.Model):
    __tablename__ = "StocksOwning"
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    owner = relationship("User", back_populates="stocks")
    stock_name = db.Column(db.String(250), nullable=False)
    stock_amount = db.Column(db.Integer, nullable=False)
    stock_cost = db.Column(db.Float, nullable=False)


class Friends(db.Model):
    __tablename__ = "Friends"
    id = db.Column(db.Integer, primary_key=True)
    person = relationship('User', back_populates='friends')
    person_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    friend_id = db.Column(db.Integer)
    friend_name = db.Column(db.String(250), nullable=False)
    
    
class History(db.Model):
    __tablename__ = "History"
    id = db.Column(db.Integer, primary_key=True)
    tran_type = db.Column(db.String(250), nullable=False)
    tran_value = db.Column(db.String(250), nullable=False)
    stock_amount = db.Column(db.Integer, nullable=False)
    stock_name = db.Column(db.String, nullable=False)
    person = relationship('User', back_populates='history')
    person_id = db.Column(db.Integer, db.ForeignKey("Users.id"))


db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return url_for('static', filename='icons/icon.ico')


@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        the_user = User.query.filter_by(email=login_form.email.data).first()
        if the_user is None:
            flash('Sorry this email is not registered.')
        else:
            if check_password_hash(the_user.password, login_form.password.data):
                login_user(the_user)
                return redirect(url_for('user_home'))
            else:
                flash('Sorry you inputted the wrong password.')
    return render_template('login.html', form=login_form)


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    signup_form = RegisterForm()
    if signup_form.validate_on_submit():
        user = User.query.filter_by(email=signup_form.email.data).first()
        if user:
            flash('Sorry a user with that email already exists')
        else:
            the_user = User(
                email=signup_form.email.data,
                name=signup_form.name.data,
                password=generate_password_hash(signup_form.password.data, "pbkdf2:sha256", 8),
                funds=10000,
            )
            db.session.add(the_user)
            db.session.commit()
            login_user(the_user)
            return redirect(url_for('user_home'))
    return render_template('signup.html', form=signup_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/dashboard', methods=['POST', 'GET'])
@login_required
def user_home():
    stock_data = current_user.stocks
    stock_dict = {}
    if request.method == 'POST':
        stock_name = request.form['stock-search']
        return redirect(url_for('comp_data', stk=stock_name))

    if stock_data:
        stock_dict['Stock Symbol'] = 'Number of Stocks'
        for stock in stock_data:
            stock_dict[stock.stock_name] = stock.stock_amount
        return render_template('user_home.html', stock_dict=stock_dict)

    return render_template('user_home.html')


@app.route('/company')
@login_required
def comp_data():
    stk = request.args.get('stk')
    payload = {
        "token": os.environ.get('TOKEN')
    }
    info = requests.get(f'https://cloud.iexapis.com/stable/stock/{stk}/company', params=payload)
    if info and stk.lower()!='appl':
        info = info.json()
        price = requests.get(f'https://cloud.iexapis.com/stable/stock/{stk}/quote/latestPrice', params=payload).json()
        stock = FollowingStock.query.filter_by(owner=current_user, stock_name=stk).first()

        return render_template('company_page.html', company_info=info, stock_price=price, name=stk, user_stock=stock)

    return render_template('not_found.html', name=stk)


@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    password_form = ChangePassword()
    friend_form = FindFriend()

    if friend_form.validate_on_submit() and friend_form.submit.data:
        friend = User.query.filter_by(email=friend_form.email_address.data).first()
        if friend:
            db.session.add(Friends(
                person=current_user,
                friend_id=friend.id,
                friend_name=friend.name
            ))
            db.session.commit()
        else:
            flash('The user you are looking for does not exist.', 'friend')

    if password_form.validate_on_submit() and password_form.submit.data:
        if check_password_hash(current_user.password, password_form.prev_password.data):
            if len(password_form.new_password.data) >= 8:
                current_user.password = generate_password_hash(password_form.new_password.data, "pbkdf2:sha256", 8)
                db.session.commit()
                flash('Password Changed', 'password')
            else:
                flash('Your new password should be at least 8 characters long.', 'password')
        else:
            flash('Sorry you inputted the incorrect previous password.', 'password')

    return render_template('profile_page.html', password_form=password_form, friend_form=friend_form)


@app.route('/articles')
@login_required
def articles():
    stocks = FollowingStock.query.filter_by(owner=current_user)
    news_articles = []
    if stocks:
        for stock in stocks:
            payload = {
                "token": os.environ.get('TOKEN')
            }
            info = requests.get(f'https://cloud.iexapis.com/stable/stock/{stock.stock_name}/news/last/7', params=payload)
            if info:
                news_articles += info.json()
        shuffle(news_articles)
    return render_template('articles.html', the_articles=news_articles)


@app.route('/add-follow')
@login_required
def add_follow():
    stk = request.args.get('stk')
    stock = FollowingStock.query.filter_by(owner=current_user, stock_name=stk).first()
    if stock is None:
        stock = FollowingStock(
            owner=current_user,
            stock_name=stk
        )
        db.session.add(stock)
        db.session.commit()
    else:
        db.session.delete(stock)
        db.session.commit()
    return redirect(url_for('comp_data', stk=stk))


@app.route('/buy-stock', methods=['POST', 'GET'])
@login_required
def buy_stock():
    form = BuyForm()
    if request.args.get('stk'):
        name = request.args.get('stk')
    else:
        name = None
    if form.validate_on_submit():
        payload = {
            "token": os.environ.get('TOKEN')
        }
        try:
            cost = int(requests.get(f'https://cloud.iexapis.com/stable/stock/{form.stk_name.data}/quote/latestPrice', params=payload).json())
            cost = int(form.stk_amount.data) * cost
            if current_user.funds - cost > 0:
                current_user.funds = current_user.funds - cost
                db.session.add(OwnershipStock(
                    stock_name=form.stk_name.data,
                    stock_amount=form.stk_amount.data,
                    stock_cost=cost,
                    owner=current_user
                ))

                stock = FollowingStock.query.filter_by(owner=current_user, stock_name=form.stk_name.data).first()
                if stock is None:
                    stock = FollowingStock(
                        owner=current_user,
                        stock_name=form.stk_name.data
                    )
                    db.session.add(stock)
                else:
                    db.session.delete(stock)

                db.session.add(History(
                    tran_type='BUY',
                    person=current_user,
                    tran_value=-cost,
                    stock_amount=int(form.stk_amount.data),
                    stock_name=form.stk_name.data,
                ))
                db.session.commit()

                return redirect(url_for('user_home'))

            else:
                flash('Sorry you dont have enough funds to make this purchase')
        except(json.decoder.JSONDecodeError):
            flash('Sorry the stock you searched for does not exist.')

    return render_template('buy_stock.html', form=form, name=name)


@app.route('/sell-stock', methods=['POST', 'GET'])
@login_required
def sell_stock():
    form = SellForm(stk_name=request.args.get('stk'))
    form.stk_name.choices = [x.stock_name for x in current_user.stocks]
    if form.validate_on_submit():
        num_stks = OwnershipStock.query.filter_by(owner=current_user, stock_name=form.stk_name.data).first().stock_amount
        if num_stks >= int(form.stk_amount.data):
            stock_amount = num_stks - int(form.stk_amount.data)
            payload = {
                "token": os.environ.get('TOKEN')
            }
            current_val = int(requests.get(f'https://cloud.iexapis.com/stable/stock/{form.stk_name.data}/quote/latestPrice', params=payload).json())
            if stock_amount == 0:
                db.session.delete(OwnershipStock.query.filter_by(owner=current_user, stock_name=form.stk_name.data).first())
            else:
                the_stock = OwnershipStock.query.filter_by(owner=current_user, stock_name=form.stk_name.data).first()
                the_stock.stock_amount = stock_amount
            db.session.add(History(
                tran_type='SELL',
                person=current_user,
                tran_value=+(int(form.stk_amount.data) * current_val),
                stock_amount=int(form.stk_amount.data),
                stock_name=form.stk_name.data,
            ))
            current_user.funds = current_user.funds + int(form.stk_amount.data) * current_val
            db.session.commit()
            return redirect(url_for('user_home'))
        else:
            flash("Sorry you can't sell more stocks than you own")

    return render_template('sell_stock.html', form=form)


@app.route('/friend-page')
def friend_page():
    frd = request.args.get('frd')
    person = User.query.get(int(frd))
    stock_data = person.stocks
    stock_dict = {}
    if stock_data:
        stock_dict['Stock Symbol'] = 'Number of Stocks'
        for stock in stock_data:
            stock_dict[stock.stock_name] = stock.stock_amount
        return render_template('friend_page.html', person=person, stock_dict=stock_dict)

    return render_template('friend_page.html', person=person)


if __name__=="__main__":
    app.run(debug=True)
