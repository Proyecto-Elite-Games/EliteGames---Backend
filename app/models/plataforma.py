from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Plataforma(Base):
    """Tabla `plataformas`."""

    __tablename__ = "plataformas"

    idPlataforma: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    def __init__(self, nombre: str, idPlataforma: Optional[int] = None):
        if idPlataforma is not None:
            self.idPlataforma = idPlataforma
        self.nombre = nombre

    def json(self) -> dict:
        return {
            "idPlataforma": self.idPlataforma,
            "nombre": self.nombre,
        }

    def __str__(self) -> str:
        return f"Plataforma(idPlataforma={self.idPlataforma}, nombre={self.nombre})"