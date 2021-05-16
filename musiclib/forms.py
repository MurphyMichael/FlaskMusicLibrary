from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from flask_login import current_user
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

#Form for the register page. Takes in all information to register and validates it against strict requirements
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[(DataRequired())])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

#Form for the login page. Takes in all information to log in and validates it against strict requirements
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

#Form for the search page. Takes in all information to search and runs the data against the database
class SearchForm(FlaskForm):
    choices = [('Artist', 'Artist'),
               ('Album', 'Album'),
               ('Songs', 'Songs'),
               ('User', 'User')] 
    select = SelectField('Select a field', choices=choices)
    search = StringField('')
    submit = SubmitField('Search')

#Form for the playlist creation page. Takes in all information for a new playlist and adds it to the database
class PlaylistForm(FlaskForm):
    playlistName = StringField('Enter the name of a new playlist or select one from below',  validators=[DataRequired(), Length(min=1, max=32)])
    submit = SubmitField('Submit')