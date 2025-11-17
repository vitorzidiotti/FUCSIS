# /api/utils/decorators.py
import datetime
from functools import wraps, update_wrapper
from flask import session, flash, redirect, url_for, make_response

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return update_wrapper(no_cache, view)

def login_required():
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                flash('Por favor, faça login para acessar esta página.', 'erro')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def admin_required():
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                flash('Por favor, faça login para acessar esta página.', 'erro')
                return redirect(url_for('auth.login'))
            if not session.get('is_admin'):
                flash('Você não tem permissão para acessar esta página.', 'erro')
                return redirect(url_for('main.inicio'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper