from typing import Optional
from flask_login import LoginManager
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo


def init_login_manager() -> LoginManager:
    from ..models import User

    login_manager = LoginManager()
    login_manager.login_view = 'login_view'

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        return User.get_item_by_id(int(user_id))

    return login_manager


class LoginForm(FlaskForm):
    email = EmailField('Эл. почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    patronymic = StringField('Отчество')
    email = EmailField('Эл. почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')


