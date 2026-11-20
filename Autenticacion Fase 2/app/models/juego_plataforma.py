from decimal import Decimal
from typing import Union

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class JuegoPlataforma(Base):
    """Tabla `juego_plataforma` (PK compuesta: idJuego + idPlataforma)."""

    __tablename__ = "juego_plataforma"

    idJuego: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("juegos.idJuego", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    idPlataforma: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plataformas.idPlataforma", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    def __init__(self, idJuego: int, idPlataforma: int, precio: Union[Decimal, float, int, str]):
        self.idJuego = idJuego
        self.idPlataforma = idPlataforma
        self.precio = precio

    def json(self) -> dict:
        return {
            "idJuego": self.idJuego,
            "idPlataforma": self.idPlataforma,
            "precio": float(self.precio) if self.precio is not None else None,
        }

    def __str__(self) -> str:
        return f"JuegoPlataforma(idJuego={self.idJuego}, idPlataforma={self.idPlataforma}, precio={self.precio})"