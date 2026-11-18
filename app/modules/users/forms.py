"""Formularios del modulo: definen los campos y sus validaciones."""
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, ValidationError

from app.modules.auth import services as auth_services
from app.modules.auth.forms import RegisterForm
from app.modules.users import services


def role_choices() -> list[tuple[int, str]]:
    return [(role.id_role, role.description or role.name) for role in services.list_roles()]


class CreateUserForm(RegisterForm):
    """Hereda usuario, contrasena, confirmacion y la validacion de usuario unico del registro."""

    id_role = SelectField("Rol", coerce=int, validators=[DataRequired("Elige un rol.")])
    submit = SubmitField("Crear usuario")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id_role.choices = role_choices()


class UpdateUserForm(FlaskForm):
    username = StringField(
        "Usuario",
        validators=[
            DataRequired("Escribe un nombre de usuario."),
            Length(min=3, max=50, message="Debe tener entre 3 y 50 caracteres."),
        ],
    )
    id_role = SelectField("Rol", coerce=int, validators=[DataRequired("Elige un rol.")])
    password = PasswordField(
        "Nueva contraseña",
        description="Déjala vacía para no cambiarla.",
        validators=[Optional(), Length(min=8, message="Debe tener al menos 8 caracteres.")],
    )
    confirm_password = PasswordField(
        "Confirmar nueva contraseña",
        validators=[EqualTo("password", message="Las contraseñas no coinciden.")],
    )
    submit = SubmitField("Guardar cambios")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, obj=user, **kwargs)
        self.user = user
        self.id_role.choices = role_choices()

    def validate_username(self, field):
        existing = auth_services.find_by_username(field.data)
        if existing and existing.id_user != self.user.id_user:
            raise ValidationError("Ese usuario ya existe.")
