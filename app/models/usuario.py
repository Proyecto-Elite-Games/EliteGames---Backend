from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Usuario(Base):
    """Tabla `usuarios`."""

    __tablename__ = "usuarios"

    idUsuario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    contrasena: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_registro: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP")
    )

    def __init__(
        self,
        nombre: str,
        apellido: str,
        email: str,
        contrasena: str,
        fecha_registro: Optional[datetime] = None,
        idUsuario: Optional[int] = None,
    ):
        if idUsuario is not None:
            self.idUsuario = idUsuario
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.contrasena = contrasena
        if fecha_registro is not None:
            self.fecha_registro = fecha_registro

    def json(self) -> dict:
        """Representación JSON. Nunca incluye la contraseña."""
        return {
            "idUsuario": self.idUsuario,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
        }

    def __str__(self) -> str:
        return f"Usuario(idUsuario={self.idUsuario}, nombre={self.nombre} {self.apellido}, email={self.email})"