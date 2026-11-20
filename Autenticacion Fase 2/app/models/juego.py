from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Juego(Base):
    """Tabla `juegos`."""

    __tablename__ = "juegos"

    idJuego: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    desarrollador: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    fecha_lanzamiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    imagen_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    idProveedor: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("proveedores.idProveedor", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    idCategoria: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categorias.idCategoria", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    def __init__(
        self,
        nombre: str,
        idProveedor: int,
        idCategoria: int,
        descripcion: Optional[str] = None,
        desarrollador: Optional[str] = None,
        fecha_lanzamiento: Optional[date] = None,
        imagen_url: Optional[str] = None,
        idJuego: Optional[int] = None,
    ):
        if idJuego is not None:
            self.idJuego = idJuego
        self.nombre = nombre
        self.descripcion = descripcion
        self.desarrollador = desarrollador
        self.fecha_lanzamiento = fecha_lanzamiento
        self.imagen_url = imagen_url
        self.idProveedor = idProveedor
        self.idCategoria = idCategoria

    def json(self) -> dict:
        return {
            "idJuego": self.idJuego,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "desarrollador": self.desarrollador,
            "fecha_lanzamiento": self.fecha_lanzamiento.isoformat() if self.fecha_lanzamiento else None,
            "imagen_url": self.imagen_url,
            "idProveedor": self.idProveedor,
            "idCategoria": self.idCategoria,
        }

    def __str__(self) -> str:
        return f"Juego(idJuego={self.idJuego}, nombre={self.nombre}, idProveedor={self.idProveedor}, idCategoria={self.idCategoria})"