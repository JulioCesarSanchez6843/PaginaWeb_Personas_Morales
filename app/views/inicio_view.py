from flask import Blueprint, render_template

inicio_view = Blueprint('inicio_view', __name__)

@inicio_view.route('/')
def inicio():
    return render_template('inicio.html')
