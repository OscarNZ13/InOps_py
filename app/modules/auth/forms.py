"""Formularios del modulo: definen los campos y sus validaciones."""
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from app.modules.auth import services


class LoginForm(FlaskForm):
    username = StringField("Usuario", validators=[DataRequired("Escribe tu usuario.")])
    password = PasswordField("Contraseña", validators=[DataRequired("Escribe tu contraseña.")])
    submit = SubmitField("Iniciar sesión")


class RegisterForm(FlaskForm):
    username = StringField(
        "Usuario",
        validators=[
            DataRequired("Elige un nombre de usuario."),
            Length(min=3, max=50, message="Debe tener entre 3 y 50 caracteres."),
        ],
    )
    password = PasswordField(
        "Contraseña",
        validators=[
            DataRequired("Escribe una contraseña."),
            Length(min=8, message="Debe tener al menos 8 caracteres."),
        ],
    )
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[
            DataRequired("Confirma la contraseña."),
            EqualTo("password", message="Las contraseñas no coinciden."),
        ],
    )
    submit = SubmitField("Crear cuenta")

    def validate_username(self, field):
        """WTForms ejecuta solo los metodos validate_<campo> al validar el formulario."""
        if services.find_by_username(field.data):
            raise ValidationError("Ese usuario ya existe.")
