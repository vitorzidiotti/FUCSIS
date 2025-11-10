from flask import Blueprint, render_template

estoque_bp = Blueprint('estoque', __name__)

@estoque_bp.route('/estoque_mov')
def estoque_mov():
    return render_template('admin_estoque.html')
