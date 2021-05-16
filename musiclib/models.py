from flask_login import UserMixin
from musiclib import mysql
from musiclib import loginManager

#User loader function for loginmanager. Returns all info of the current user
@loginManager.user_loader
def load_user(ID):
    cur = mysql.connect().cursor()
    cur.execute("SELECT * FROM User WHERE id=%s", ID)
    result=cur.fetchone()
    return MyUser(result[0], result[1], result[2], result[3])

#User definition for the login manager. Assists with authorization and authentication
class MyUser(UserMixin):
    def __init__(self, ID, username, password, email, active=True):
        self.ID = ID
        self.username = username
        self.password = password
        self.email = email

    def __repr__(self):
        return f"User('{self.ID}', '{self.username}', '{self.email} ')"

    def is_active(self):
        return self.active

    def get_id(self):
        return (self.ID)

    def get_user(self):
        return(self.username)