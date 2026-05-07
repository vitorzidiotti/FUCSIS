from flask import session, flash, redirect, url_for, make_response
from functools import wraps
from datetime import datetime

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Por favor, faça login para acessar esta página.', 'erro')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or session.get('id_grupo') != 1:
            flash('Você não tem permissão para acessar esta página.', 'erro')
            return redirect(url_for('inicio'))
        return f(*args, **kwargs)
    return decorated_function