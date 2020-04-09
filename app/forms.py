from flask_wtf import FlaskForm as Form
from wtforms import StringField, DecimalField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired

class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Submit')