"""Tipos y utilidades comunes a todos los modelos."""
from datetime import datetime

from sqlalchemy.dialects import mssql

from app.extensions import db

FechaHora = db.DateTime().with_variant(mssql.DATETIME2(), "mssql")
TinyInt = db.SmallInteger().with_variant(mssql.TINYINT(), "mssql")


def ahora() -> datetime:
    """Fecha y hora local, equivalente a SYSDATETIME() en SQL Server."""
    return datetime.now()


class TimestampMixin:
    """Agrega las columnas CreatedAt y UpdatedAt, que se llenan solas."""

    fecha_creacion = db.Column("CreatedAt", FechaHora, nullable=False, default=ahora)
    fecha_modificacion = db.Column(
        "UpdatedAt", FechaHora, nullable=False, default=ahora, onupdate=ahora
    )
