from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, URL, Email, Length


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message='Please input a proper email address.')], render_kw={"placeholder": "Email"})
    name = StringField("Name", validators=[DataRequired()], render_kw={"placeholder": "Name"})
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, message='Your password should be a minimum of 8 characters long.')], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message='Please input a proper email address.')], render_kw={"placeholder": "Email"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")


class BuyForm(FlaskForm):
    stk_name = StringField("Stock Name", validators=[DataRequired()], render_kw={"placeholder": "Stock Symbol"})
    stk_amount = StringField("Stock Amount", validators=[DataRequired()], render_kw={"placeholder": "Number of stocks you want to buy"})
    submit = SubmitField("Buy")


class SellForm(FlaskForm):
    stk_name = SelectField("Stock Name", validators=[DataRequired()], render_kw={"placeholder": "Stock Symbol"})
    stk_amount = StringField("Stock Amount", validators=[DataRequired()], render_kw={"placeholder": "Number of stocks you want to sell"})
    submit = SubmitField("Sell")


class ChangePassword(FlaskForm):
    prev_password = PasswordField("Stock Name", validators=[DataRequired()], render_kw={"placeholder": "Previous Password"})
    new_password = PasswordField("Stock Amount", validators=[DataRequired()],render_kw={"placeholder": "New Password"})
    submit = SubmitField("Change Password")

class FindFriend(FlaskForm):
    email_address = StringField("Stock Name", validators=[DataRequired(), Email(message='Please input a proper email address.')], render_kw={"placeholder": "Enter your friends email address."})
    submit = SubmitField("Find Friend")
