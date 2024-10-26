from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, EqualTo, Length

class RegistrationForm(FlaskForm):
    user_id = StringField("Username:", validators=[InputRequired()])
    password = PasswordField("Password:", validators=[InputRequired(),Length(min=5)])
    password2 = PasswordField("Confirm password:", validators=[InputRequired(), EqualTo("password")])
    submit = SubmitField("Submit")

class LoginForm(FlaskForm):
    user_id = StringField("Username:", validators=[InputRequired()])
    password = PasswordField("Password:", validators=[InputRequired()])
    submit = SubmitField("Submit")
