from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, ValidationError, HiddenField, \
    BooleanField, PasswordField, EmailField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, URL, EqualTo


class LoginForm(FlaskForm):
    redirect = HiddenField('Redirect')
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    firstName = StringField('First Name', validators=[DataRequired()])
    lastName = StringField('Last Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Passwords must match.')])
    confirm = PasswordField('Repeat Password', validators=[DataRequired()])
    phone = StringField('Phone Number')
    submit = SubmitField('Register Account')


class StationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    lat = StringField('Latitude', validators=[DataRequired()])
    lon = StringField('Longitude', validators=[DataRequired()])
    submit = SubmitField('Save')


class SettingForm(FlaskForm):
    tz = SelectField('Timezone', validators=[DataRequired()])
    lang = SelectField('Language', validators=[DataRequired()])


class ProdForm(FlaskForm):
    loading = StringField('Loading', validators=[DataRequired()], default='TRI(2, 3, 4)')
    hauling = StringField('Hauling', validators=[DataRequired()], default='TRI(3, 3.6, 4)')
    dumping = StringField('Dumping', validators=[DataRequired()], default='1.2')
    returning = StringField('Returning', validators=[DataRequired()], default='TRI(3, 3.2, 4)')
    count_number = IntegerField('Count Number', default=100)
    run_number = IntegerField('Running Number', default=20)
    submit = SubmitField('Run')

