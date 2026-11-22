"""Formularios del modulo: definen los campos y sus validaciones (seccion 4 del contexto)."""
from datetime import date

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError

from app.modules.collaborators import services

EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PHONE = r"^[0-9+()\-\s]+$"
PERSON_FIELDS = ("first_name", "second_name", "last_name", "second_last_name", "birthdate")
PROFILE_FIELDS = ("position", "department", "email", "phone")


def at_least_two_letters(label):
    def validator(_form, field):
        if sum(char.isalpha() for char in field.data or "") < 2:
            raise ValidationError(f"{label} debe tener al menos 2 letras.")

    return validator


class CollaboratorForm(FlaskForm):
    """Campos y validaciones comunes a crear y editar."""

    first_name = StringField(
        "Primer nombre",
        description="Si tiene dos nombres, escribe el segundo en «Segundo nombre».",
        validators=[DataRequired("Escribe el primer nombre."), Length(max=50), at_least_two_letters("El primer nombre")],
    )
    second_name = StringField("Segundo nombre", validators=[Optional(), Length(max=50)])
    last_name = StringField(
        "Primer apellido",
        validators=[DataRequired("Escribe el primer apellido."), Length(max=50), at_least_two_letters("El primer apellido")],
    )
    second_last_name = StringField("Segundo apellido", validators=[Optional(), Length(max=50)])
    birthdate = DateField("Fecha de nacimiento", validators=[Optional()])
    single_first_name = BooleanField("Sí, es un solo nombre")
    single_last_name = BooleanField("Sí, es un solo apellido")

    position = StringField("Puesto", validators=[Optional(), Length(max=100)])
    department = StringField("Departamento", validators=[Optional(), Length(max=100)])
    email = StringField(
        "Correo",
        validators=[Optional(), Length(max=100), Regexp(EMAIL, message="Escribe un correo válido.")],
    )
    phone = StringField(
        "Teléfono",
        validators=[Optional(), Length(max=20), Regexp(PHONE, message="Usa solo números, espacios, +, - o paréntesis.")],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confirmations_needed = set()

    def values(self) -> dict:
        """Los datos listos para el service, sin las casillas de confirmacion ni el boton."""
        return {name: self[name].data for name in PERSON_FIELDS + PROFILE_FIELDS}

    def own_profile_id(self) -> int | None:
        return None

    def validate_first_name(self, field):
        self._check_two_in_one(field, self.second_name, self.single_first_name, "dos nombres", "Segundo nombre")

    def validate_last_name(self, field):
        self._check_two_in_one(field, self.second_last_name, self.single_last_name, "dos apellidos", "Segundo apellido")

    def validate_birthdate(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("La fecha de nacimiento no puede ser futura.")

    def validate_email(self, field):
        if services.email_taken(field.data.strip(), except_profile=self.own_profile_id()):
            raise ValidationError("Ese correo ya pertenece a otro colaborador.")

    def _check_two_in_one(self, field, second_field, confirmed, what, second_label):
        """Seccion 4.5: un guion sin segundo campo suele ser dos valores escritos juntos (Perez-Soto)."""
        if "-" in (field.data or "") and not (second_field.data or "").strip() and not confirmed.data:
            self.confirmations_needed.add(confirmed.name)
            raise ValidationError(f"Parece que escribiste {what} en un campo. Escribe el segundo en «{second_label}».")


class CreateCollaboratorForm(CollaboratorForm):
    submit = SubmitField("Crear colaborador")


class UpdateCollaboratorForm(CollaboratorForm):
    submit = SubmitField("Guardar cambios")

    def __init__(self, collaborator, *args, **kwargs):
        """Aparece lleno con los datos actuales del colaborador y de su perfil."""
        current = {name: getattr(collaborator, name) for name in PERSON_FIELDS}
        current |= {name: getattr(collaborator.profile, name) for name in PROFILE_FIELDS}
        super().__init__(*args, data=current, **kwargs)
        self.collaborator = collaborator

    def own_profile_id(self) -> int | None:
        """Al editar, el colaborador puede quedarse con su propio correo."""
        return self.collaborator.profile.id_profile
