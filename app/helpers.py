from flask import session

def is_user_logged_in():
    return 'user_id' in session
