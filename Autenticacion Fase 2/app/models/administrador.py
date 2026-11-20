from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Administrador(Base):
    """Tabla `administradores`."""

    __tablename__ = "administradores"

    idAdmin: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    contrasena: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(50), nullable=False)
    fecha_creacion: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP")
    )

    def __init__(
        self,
        nombre: str,
        apellido: str,
        email: str,
        contrasena: str,
        rol: str,
        fecha_creacion: Optional[datetime] = None,
        idAdmin: Optional[int] = None,
    ):
        if idAdmin is not None:
            self.idAdmin = idAdmin
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.contrasena = contrasena
        self.rol = rol
        if fecha_creacion is not None:
            self.fecha_creacion = fecha_creacion

    def json(self) -> dict:
        """Representación JSON. Nunca incluye la contraseña."""
        return {
            "idAdmin": self.idAdmin,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "rol": self.rol,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        }

    def __str__(self) -> str:
        return f"Administrador(idAdmin={self.idAdmin}, nombre={self.nombre} {self.apellido}, email={self.email}, rol={self.rol})"