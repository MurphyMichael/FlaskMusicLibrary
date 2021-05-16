from flask import Flask, request
from flask_bcrypt import Bcrypt
from flaskext.mysql import MySQL
from flask_login import LoginManager
import secrets as secret
import os

#Create the flask environment
app = Flask(__name__)

#Set the secret key for the current running app
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

#create the mysql environment
mysql = MySQL()

#set up the mysql information to pull from the required database using user information
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = secret.USER
app.config['MYSQL_DATABASE_PASSWORD'] = secret.PASS
app.config['MYSQL_DATABASE_DB'] = 'jts0270'
mysql.init_app(app)

#set up bcrypt to hash passwords
bcrypt = Bcrypt(app)

#create the mysql database connection
conn = mysql.connect()

#setup the login manager
loginManager = LoginManager()
loginManager.login_view = 'Login'   
loginManager.login_message_category = 'info'
loginManager.init_app(app)

#bring in the route handler
from musiclib import routes