"""Tipos y utilidades comunes a todos los modelos."""
from datetime import datetime

from sqlalchemy.dialects import mssql

from app.extensions import db

DateTime2 = db.DateTime().with_variant(mssql.DATETIME2(), "mssql")
TinyInt = db.SmallInteger().with_variant(mssql.TINYINT(), "mssql")


def now() -> datetime:
    """Fecha y hora local, equivalente a SYSDATETIME() en SQL Server."""
    return datetime.now()


class TimestampMixin:
    """Agrega las columnas CreatedAt y UpdatedAt, que se llenan solas."""

    created_at = db.Column("CreatedAt", DateTime2, nullable=False, default=now)
    updated_at = db.Column(
        "UpdatedAt", DateTime2, nullable=False, default=now, onupdate=now
    )
