from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Categoria(Base):
    """Tabla `categorias`."""

    __tablename__ = "categorias"

    idCategoria: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __init__(
        self,
        nombre: str,
        descripcion: Optional[str] = None,
        idCategoria: Optional[int] = None,
    ):
        if idCategoria is not None:
            self.idCategoria = idCategoria
        self.nombre = nombre
        self.descripcion = descripcion

    def json(self) -> dict:
        return {
            "idCategoria": self.idCategoria,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }

    def __str__(self) -> str:
        return f"Categoria(idCategoria={self.idCategoria}, nombre={self.nombre})"