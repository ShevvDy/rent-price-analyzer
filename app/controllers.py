from datetime import datetime
from flask import Flask, jsonify, render_template, request, Response, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from pydantic import ValidationError

from .ml_model import get_rental_price
from .models import User, EstimatedHome
from .util.pydantic_models import Data
from .util.address import get_address_suggestions
from .util.auth import LoginForm, RegistrationForm


@login_required
def get_price_api() -> tuple[Response, int]:
    try:
        data = request.get_json()
        if 'home_id' in data and data['home_id'] is not None:
            response = get_rental_price(data)
        else:
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

@login_required
def get_address_suggestions_api() -> tuple[Response, int]:
    query = request.args.get('query', '')
    suggestions = get_address_suggestions(query)
    return jsonify(suggestions), 200

def login_view() -> str | Response:
    login_form = LoginForm()
    register_form = RegistrationForm()
    if current_user.is_authenticated:
        return redirect(url_for('lk_view'))
    if login_form.validate_on_submit():
        user = User.get_by_email(login_form.email.data)
        if user and user.check_password(login_form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('lk_view'))
        flash('Invalid username or password')
    if register_form.validate_on_submit():
        existing_user = User.get_by_email(register_form.email.data)
        if existing_user:
            flash('Username or email already exists')
            return redirect(url_for('login_view'))
        user = User(email=register_form.email.data, name=register_form.name.data, surname=register_form.surname.data, patronymic=register_form.patronymic.data)
        user.set_password(register_form.password.data)
        user.add()
        return redirect(url_for('login_view'))
    return render_template('login.html', login_form=login_form, register_form=register_form)

@login_required
def logout() -> Response:
    logout_user()
    return redirect(url_for('login_view'))

@login_required
def lk_view() -> str:
    return render_template('lk.html', estimated_homes=current_user.estimated_homes, datetime=datetime)

@login_required
def predict_view() -> str:
    return render_template('predict.html')

@login_required
def estimated_view(home_id: int) -> str | Response:
    home = EstimatedHome.get_item_by_id(home_id)
    if not home or home.user_id != current_user.id:
        return redirect(url_for('lk_view'))
    return render_template(
        'estimated.html',
        home=home,
        compute_date=datetime.fromtimestamp(home.compute_date).strftime("%Y-%m-%d %H:%M")
    )

def init_controllers(app: Flask) -> None:
    app.add_url_rule('/', view_func=login_view, methods=['GET', 'POST'])
    app.add_url_rule('/api/get_price', view_func=get_price_api, methods=['POST'])
    app.add_url_rule('/api/address', view_func=get_address_suggestions_api, methods=['GET'])
    app.add_url_rule('/logout', view_func=logout, methods=['GET'])
    app.add_url_rule('/lk', view_func=lk_view, methods=['GET'])
    app.add_url_rule('/predict', view_func=predict_view, methods=['GET'])
    app.add_url_rule('/estimated/<int:home_id>', view_func=estimated_view, methods=['GET'])
