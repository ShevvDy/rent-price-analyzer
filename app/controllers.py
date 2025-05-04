from flask import Flask, jsonify, render_template, request, Response, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from pydantic import ValidationError

from .ml_model import get_rental_price
from .models import User
from .util.pydantic_models import Data
from .util.address import get_address_suggestions
from .util.auth import LoginForm, RegistrationForm


def get_price_api() -> tuple[Response, int]:
    try:
        data = request.get_json()
        data = Data(**data)
        data = data.model_dump()
        data.pop('flatType')
        response = get_rental_price(data)
    except ValidationError as e:
        return jsonify({
            "status": "error",
            "errors": e.errors()
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "errors": [str(e)]
        }), 500
    return jsonify(response), 200

def get_address_suggestions_api() -> tuple[Response, int]:
    query = request.args.get('query', '')
    suggestions = get_address_suggestions(query)
    return jsonify(suggestions), 200

def index_view() -> str:
    return render_template("index.html")

def login_view() -> str | Response:
    if current_user.is_authenticated:
        return redirect(url_for('index_view'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index_view'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)


def register_view() -> str | Response:
    if current_user.is_authenticated:
        return redirect(url_for('index_view'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.get_by_email(form.email.data)
        if existing_user:
            flash('Username or email already exists')
            return redirect(url_for('register'))
        user = User(email=form.email.data, name=form.name.data, surname=form.surname.data, patronymic=form.patronymic.data)
        user.set_password(form.password.data)
        user.add()
        flash('Registration successful!')
        return redirect(url_for('login_view'))
    return render_template('register.html', form=form)

@login_required
def logout():
    logout_user()
    return redirect(url_for('index_view'))

def init_controllers(app: Flask) -> None:
    app.add_url_rule('/', view_func=index_view, methods=['GET'])
    app.add_url_rule('/api/get_price', view_func=get_price_api, methods=['POST'])
    app.add_url_rule('/api/address', view_func=get_address_suggestions_api, methods=['GET'])
    app.add_url_rule('/login', view_func=login_view, methods=['GET', 'POST'])
    app.add_url_rule('/register', view_func=register_view, methods=['GET', 'POST'])
    app.add_url_rule('/logout', view_func=logout, methods=['GET'])
